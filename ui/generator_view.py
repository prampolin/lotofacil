"""
Interface de Terminal para Geração Passo a Passo e Curadoria Interativa de Jogos da Lotofácil.
"""

import os
import json
import collections

from engine.candidate_generator import generate_candidate_pool
from engine.filter_pipeline import (
    FilterPipeline,
    build_historical_set,
    build_historical_14_set,
    is_historically_drawn,
    get_current_cycle_info,
    calc_rule_transitions,
    get_top_transitions,
)
from engine.rules_evaluator import (
    PRIMES, FIBONACCI, MULTIPLES_OF_3, BORDER,
    count_odds, count_primes, count_border, count_fibonacci,
    count_multiples_of_3, calc_sum, count_cycle_numbers,
    eval_rows_distribution, eval_cols_distribution,
    eval_consecutives, eval_triple_jump, count_triple_jumps
)


def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')


def parse_number_list(text):
    """Converte string de dezenas ('01 05 12' ou '1, 5, 12') em um set de inteiros."""
    if not text.strip():
        return set()
    cleaned = text.replace(',', ' ').replace(';', ' ')
    nums = set()
    for token in cleaned.split():
        if token.isdigit():
            val = int(token)
            if 1 <= val <= 25:
                nums.add(val)
    return nums


def parse_range(text, default_min, default_max):
    """
    Converte entrada do usuário ('7-8', '7..8', '7,8', '7', '') em uma tupla (min_val, max_val).
    Se vazio, retorna (default_min, default_max).
    """
    text = text.strip()
    if not text:
        return default_min, default_max
    
    cleaned = text.replace('..', '-').replace(',', '-').replace(';', '-').replace(' ', '-')
    parts = [p for p in cleaned.split('-') if p.isdigit()]
    
    if len(parts) == 1:
        v = int(parts[0])
        return v, v
    elif len(parts) >= 2:
        return int(parts[0]), int(parts[1])
    
    return default_min, default_max


def parse_filter_choice(text, default_min, default_max):
    """
    Processa a escolha do usuário para filtros numéricos de intervalo:
    - 'N', 'n', 'nao', 'não': retorna None (filtro desativado / não usar)
    - 'P', 'p', 'padrao', 'padrão' ou '': retorna tupla (default_min, default_max)
    - valores numéricos (ex: '3-5', '4', '3..5'): retorna tupla (min_val, max_val)
    """
    cleaned = text.strip().lower()
    if cleaned in ('n', 'nao', 'não', 'no'):
        return None
    if cleaned in ('p', 'padrao', 'padrão', ''):
        return default_min, default_max
    
    return parse_range(text, default_min, default_max)


def parse_repetition_choice(text, default_list):
    """
    Processa a escolha do usuário para o filtro de repetições:
    - 'N', 'n', 'nao', 'não': retorna list(range(5, 16)) (todas as 5 a 15 repetições possíveis, sem filtrar)
    - 'P', 'p', 'padrao', 'padrão' ou '': retorna default_list (ex: [8, 9, 10])
    - valores como '8-10', '9,10', '9': retorna lista de inteiros customizada
    """
    cleaned = text.strip().lower()
    if cleaned in ('n', 'nao', 'não', 'no'):
        return list(range(5, 16))
    if cleaned in ('p', 'padrao', 'padrão', ''):
        return list(default_list)
    
    return parse_list_of_ints(text, default_list)


def parse_single_int_choice(text, default_val):
    """
    Processa a escolha do usuário para filtros de valor único/máximo (ex: sequências consecutivas):
    - 'N', 'n', 'nao', 'não': retorna None (filtro desativado)
    - 'P', 'p', 'padrao', 'padrão' ou '': retorna default_val
    - valores numéricos como '4', '1-4': retorna inteiro customizado
    """
    cleaned = text.strip().lower()
    if cleaned in ('n', 'nao', 'não', 'no'):
        return None
    if cleaned in ('p', 'padrao', 'padrão', ''):
        return default_val
    
    parts = [int(p) for p in cleaned.replace('..', '-').replace(',', '-').split('-') if p.isdigit()]
    if parts:
        return parts[-1]
    return default_val


def parse_sequence_choice(text, default_max=5):
    """
    Processa a escolha do usuário para o filtro de sequências consecutivas:
    - 'N', 'n', 'nao', 'não', 'no': retorna None (filtro desativado)
    - 'P', 'p', 'padrao', 'padrão' ou '': retorna (1, default_max) -> máx default_max seguidas
    - número único (ex: '4'): retorna (1, 4) -> máx 4 seguidas
    - intervalo (ex: '3-5'): retorna (3, 5) -> mín 3 e máx 5 seguidas
    """
    cleaned = text.strip().lower()
    if cleaned in ('n', 'nao', 'não', 'no'):
        return None
    if cleaned in ('p', 'padrao', 'padrão', ''):
        return (1, default_max)
    
    cleaned_range = cleaned.replace('..', '-').replace(',', '-').replace(';', '-').replace(' ', '-')
    parts = [int(p) for p in cleaned_range.split('-') if p.isdigit()]
    if len(parts) == 1:
        return (1, parts[0])
    elif len(parts) >= 2:
        return (parts[0], parts[1])
    return (1, default_max)


def parse_triple_jump_choice(text, default_min=0, default_max=1):
    """
    Processa a escolha do usuário para o filtro de pulo triplo (gap de 3 dezenas):
    - 'N', 'n', 'nao', 'não', 'no', 'todos': retorna None (filtro desativado / aceita qualquer quantidade)
    - 'P', 'p', 'padrao', 'padrão' ou '': retorna (default_min, default_max) -> padrão (0, 1) pulos
    - '0', 'sem', 'nenhum': retorna (0, 0) -> apenas jogos sem nenhum pulo triplo
    - '1': retorna (1, 1) -> exatamente 1 pulo triplo
    - 'S', 's', 'sim', 'com', '>=1', '1+': retorna (1, 3) -> jogos com pelo menos 1 pulo triplo
    - intervalo '0-1', '1-2', etc.: retorna (min_v, max_v)
    """
    cleaned = text.strip().lower()
    if cleaned in ('n', 'nao', 'não', 'no', 'todos'):
        return None
    if cleaned in ('p', 'padrao', 'padrão', ''):
        return (default_min, default_max)
    if cleaned in ('s', 'sim', 'com', '>=1', '1+'):
        return (1, 3)
    if cleaned in ('0', 'sem', 'nenhum'):
        return (0, 0)
    
    cleaned_range = cleaned.replace('..', '-').replace(',', '-').replace(';', '-').replace(' ', '-')
    parts = [int(p) for p in cleaned_range.split('-') if p.isdigit()]
    if len(parts) == 1:
        return (parts[0], parts[0])
    elif len(parts) >= 2:
        return (parts[0], parts[1])
    return (default_min, default_max)


def parse_boolean_choice(text, default_val=True):
    """
    Processa escolha booleana (ex: exclusão histórica):
    - 'N', 'n', 'nao', 'não': retorna False (não aplicar)
    - 'P', 'p', 'padrao', 'padrão', 's', 'sim' ou '': retorna default_val (normalmente True)
    """
    cleaned = text.strip().lower()
    if cleaned in ('n', 'nao', 'não', 'no'):
        return False
    if cleaned in ('p', 'padrao', 'padrão', 's', 'sim', ''):
        return True
    return default_val


def parse_list_of_ints(text, default_list):
    """Converte entrada do usuário ('8-11' ou '8,9,10,11' ou '8 9 10 11') em lista de ints."""
    text = text.strip()
    if not text:
        return default_list
    
    if '-' in text or '..' in text:
        min_v, max_v = parse_range(text, min(default_list), max(default_list))
        return list(range(min_v, max_v + 1))
        
    cleaned = text.replace(',', ' ').replace(';', ' ')
    nums = []
    for token in cleaned.split():
        if token.isdigit():
            nums.append(int(token))
    return sorted(nums) if nums else default_list


def format_game(comb):
    """Formata as 15 dezenas com 2 dígitos separadas por espaço."""
    return " ".join(f"{n:02d}" for n in comb)


def prompt_step_header(step_num, title, total_steps=13):
    print(f"\n[{step_num}/{total_steps}] === {title} ===")



def run_game_generator(results_file="lotofacil_resultados.json"):
    clear_screen()
    print("==========================================================")
    print("             GERADOR INTELIGENTE DE JOGOS                 ")
    print("==========================================================")

    if not os.path.exists(results_file):
        print(f"❌ Arquivo de resultados '{results_file}' não encontrado.")
        print("Atualize a base de dados no menu principal primeiro.")
        input("\n[ Pressione ENTER para voltar ]")
        return

    with open(results_file, 'r', encoding='utf-8') as f:
        contests = json.load(f)

    if not contests:
        print("❌ Nenhum concurso encontrado na base de dados.")
        input("\n[ Pressione ENTER para voltar ]")
        return

    sorted_contests = sorted(contests, key=lambda c: c['concurso'])
    last_contest = sorted_contests[-1]
    last_dezenas = sorted(last_contest['dezenas'])
    
    print(f"📌 Último Concurso: #{last_contest['concurso']} ({last_contest.get('data', '')})")
    print(f"   Dezenas sorteadas: {format_game(last_dezenas)}")
    
    cycle_num, missing_cycle, cycle_len = get_current_cycle_info(sorted_contests)
    if missing_cycle and len(missing_cycle) < 25:
        missing_str = " ".join(f"{n:02d}" for n in sorted(missing_cycle))
        print(f"🔄 Ciclo Atual: #{cycle_num} (Concursos no ciclo: {cycle_len} | Faltam {len(missing_cycle)} dezenas: {missing_str})")
    else:
        print(f"🔄 Ciclo Atual: #{cycle_num} (Novo ciclo - todas as 25 dezenas disponíveis)")
    print("----------------------------------------------------------")

    # ==========================================================
    # PASSO 1: DEZENAS FIXAS E EXCLUÍDAS
    # ==========================================================
    prompt_step_header(1, "Dezenas Fixas e Excluídas")
    print("ℹ️ Dezenas Fixas: estarão em 100% dos jogos gerados.")
    print("ℹ️ Dezenas Excluídas: não estarão em nenhum jogo gerado.")
    
    while True:
        fixas_input = input("\nDigite as dezenas FIXAS separadas por espaço (ou ENTER para nenhuma): ").strip()
        fixed_numbers = parse_number_list(fixas_input)
        if len(fixed_numbers) > 15:
            print("⚠️ Máximo de 15 dezenas fixas permitidas. Tente novamente.")
            continue
        break
        
    while True:
        excluidas_input = input("Digite as dezenas EXCLUÍDAS separadas por espaço (ou ENTER para nenhuma): ").strip()
        excluded_numbers = parse_number_list(excluidas_input)
        conflict = fixed_numbers.intersection(excluded_numbers)
        if conflict:
            print(f"⚠️ As dezenas {conflict} não podem ser fixas e excluídas ao mesmo tempo. Tente novamente.")
            continue
        if len(excluded_numbers) > 10:
            print("⚠️ Excluir mais de 10 dezenas deixa menos de 15 disponíveis para o jogo. Tente novamente.")
            continue
        break

    if fixed_numbers:
        print(f"✅ Fixas ({len(fixed_numbers)}): {' '.join(f'{n:02d}' for n in sorted(fixed_numbers))}")
    if excluded_numbers:
        print(f"⛔ Excluídas ({len(excluded_numbers)}): {' '.join(f'{n:02d}' for n in sorted(excluded_numbers))}")

    # ==========================================================
    # PASSO 2: REPETIÇÕES DO CONCURSO ANTERIOR (POOL INICIAL)
    # ==========================================================
    prompt_step_header(2, "Repetições do Concurso Anterior")
    print("📊 Histórico geral de repetições:")
    print("   9 repetidas: ~33% | 8 repetidas: ~25% | 10 repetidas: ~23% | 11 repetidas: ~7%")
    
    # Transição do último concurso
    if len(sorted_contests) >= 2:
        prev_to_last = sorted_contests[-2]['dezenas']
        last_rep_count = len(set(prev_to_last).intersection(set(last_dezenas)))
        rep_transitions = calc_rule_transitions(sorted_contests, lambda c: 0) # calcularemos para repetições
        # Calcular transição exata de repetições
        rep_history = []
        for i in range(1, len(sorted_contests)):
            r = len(set(sorted_contests[i-1]['dezenas']).intersection(set(sorted_contests[i]['dezenas'])))
            rep_history.append(r)
        
        counts_after = collections.Counter()
        for i in range(len(rep_history) - 1):
            if rep_history[i] == last_rep_count:
                counts_after[rep_history[i+1]] += 1
                
        total_trans = sum(counts_after.values())
        if total_trans > 0:
            top_t = counts_after.most_common(2)
            top_str = ", ".join(f"{v} rep ({c/total_trans*100:.1f}%)" for v, c in top_t)
            print(f"🎯 No último concurso repetiram {last_rep_count} dezenas. Transições mais comuns seguintes: {top_str}")

    rep_input = input("\nFaixa de repetições [P = Padrão (8-10) | N = Não usar | ou digite ex: 8-10]: ").strip()
    allowed_repetitions = parse_repetition_choice(rep_input, [8, 9, 10])
    
    if len(allowed_repetitions) == 11 and set(allowed_repetitions) == set(range(5, 16)):
        print("⚡ Filtro de repetições DESATIVADO (todas as 5 a 15 repetições permitidas).")
    elif allowed_repetitions == [8, 9, 10]:
        print("⚡ Usando faixa padrão: 8 a 10 repetidas.")
    else:
        print(f"⚡ Usando faixa personalizada: {allowed_repetitions} repetidas.")
    
    print(f"\n⏳ Gerando Pool de Candidatos inicial ({allowed_repetitions} repetidas)...")
    try:
        candidates = generate_candidate_pool(
            previous_numbers=last_dezenas,
            allowed_repetitions=allowed_repetitions,
            fixed_numbers=fixed_numbers,
            excluded_numbers=excluded_numbers
        )
    except Exception as e:
        print(f"❌ Erro ao gerar candidatos: {e}")
        input("\n[ Pressione ENTER para voltar ]")
        return

    pipeline = FilterPipeline(candidates)
    print(f"✨ Pool inicial gerado: {len(pipeline.candidates):,} candidatos disponíveis.")

    if len(pipeline.candidates) == 0:
        print("⚠️ Nenhuma combinação possível com esses parâmetros iniciais.")
        input("\n[ Pressione ENTER para voltar ]")
        return

    # ==========================================================
    # PASSO 3: EXCLUSÃO DE RESULTADOS HISTÓRICOS
    # ==========================================================
    prompt_step_header(3, "Exclusão de Resultados Já Sorteados")
    historical_15 = build_historical_set(sorted_contests)
    historical_14 = build_historical_14_set(sorted_contests)
    print(f"📊 A Lotofácil possui {len(sorted_contests):,} concursos já sorteados na história.")
    print(f"ℹ️ Total de combinações de 14 dezenas extraídas: {len(sorted_contests):,} x 15 = {len(sorted_contests) * 15:,} ({len(historical_14):,} únicas).")
    print("ℹ️ Este filtro exclui combinações que repitam 14 ou 15 dezenas de qualquer resultado histórico.")
    
    hist_input = input("\nExcluir resultados com 14 e 15 dezenas já sorteadas? [P = Padrão (14 e 15) | 15 = Apenas 15 | N = Não usar]: ").strip().lower()
    if hist_input in ('n', 'nao', 'não', 'no'):
        print("⏩ Filtro de exclusão histórica DESATIVADO (não aplicado).")
    elif hist_input in ('15', '15 dezenas', 'apenas 15'):
        stat = pipeline.apply("historical_exclusion", lambda c: c not in historical_15)
        print(f"⚡ Filtro aplicado [Apenas 15 dezenas]: {stat['removed_count']:,} jogos históricos removidos | Restantes: {stat['remaining_count']:,}")
    else:
        stat = pipeline.apply("historical_exclusion", lambda c: not is_historically_drawn(c, historical_14, historical_15))
        print(f"⚡ Filtro aplicado [14 e 15 dezenas]: {stat['removed_count']:,} jogos históricos (14 ou 15 dezenas) removidos | Restantes: {stat['remaining_count']:,}")

    # ==========================================================
    # PASSO 4: DEZENAS DO CICLO ATUAL
    # ==========================================================
    prompt_step_header(4, "Dezenas Faltantes do Ciclo Atual")
    if missing_cycle and len(missing_cycle) < 25:
        num_missing = len(missing_cycle)
        print(f"📊 Faltam {num_missing} dezenas para fechar o Ciclo #{cycle_num}: {missing_str}")
        default_min_cycle = 1 if num_missing >= 2 else 0
        default_max_cycle = min(num_missing, 3)
        
        cycle_input = input(f"Dezenas do ciclo por jogo [P = Padrão ({default_min_cycle}-{default_max_cycle}) | N = Não usar | ou digite ex: 1-2]: ").strip()
        cycle_choice = parse_filter_choice(cycle_input, default_min_cycle, default_max_cycle)
        if cycle_choice is not None:
            min_c, max_c = cycle_choice
            label = "Padrão" if cycle_choice == (default_min_cycle, default_max_cycle) else "Personalizado"
            stat = pipeline.apply("cycle_missing", lambda c: min_c <= count_cycle_numbers(c, missing_cycle) <= max_c)
            print(f"⚡ Filtro aplicado [{label}: {min_c} a {max_c}]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
        else:
            print("⏩ Filtro de dezenas do ciclo DESATIVADO (não aplicado).")
    else:
        print("ℹ️ O ciclo atual acabou de ser reiniciado. Pulando filtro específico de ciclo.")

    # ==========================================================
    # PASSO 5: PARIDADE (PARES / ÍMPARES)
    # ==========================================================
    prompt_step_header(5, "Paridade (Pares / Ímpares)")
    last_odds = count_odds(last_dezenas)
    last_evens = 15 - last_odds
    
    parity_trans = calc_rule_transitions(sorted_contests, lambda c: count_odds(c['dezenas']))
    top_p_trans = get_top_transitions(parity_trans, last_odds, 2)
    top_p_str = ", ".join(f"{o}I/{15-o}P ({pct:.1f}%)" for o, _, pct in top_p_trans) if top_p_trans else "7I/8P, 8I/7P"
    
    print(f"📊 Histórico: 7 ímpares (~31%), 8 ímpares (~26%), 9 ímpares (~20%), 6 ímpares (~18%)")
    print(f"🎯 Último concurso teve: {last_odds} ímpares / {last_evens} pares.")
    if top_p_trans:
        print(f"🔄 Transições mais frequentes pós {last_odds}I: {top_p_str}")
        
    parity_input = input("Faixa de ÍMPARES [P = Padrão (7-8) | N = Não usar | ou digite ex: 7-9]: ").strip()
    parity_choice = parse_filter_choice(parity_input, 7, 8)
    if parity_choice is not None:
        min_odds, max_odds = parity_choice
        label = "Padrão" if parity_choice == (7, 8) else "Personalizado"
        stat = pipeline.apply("parity", lambda c: min_odds <= count_odds(c) <= max_odds)
        print(f"⚡ Filtro aplicado [{label}: {min_odds} a {max_odds}]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
    else:
        print("⏩ Filtro de Paridade DESATIVADO (não aplicado).")

    # ==========================================================
    # PASSO 6: NÚMEROS PRIMOS
    # ==========================================================
    prompt_step_header(6, "Números Primos")
    print("ℹ️ Primos da Lotofácil (9 total): 02, 03, 05, 07, 11, 13, 17, 19, 23")
    last_primes = count_primes(last_dezenas)
    
    primes_trans = calc_rule_transitions(sorted_contests, lambda c: count_primes(c['dezenas']))
    top_pr_trans = get_top_transitions(primes_trans, last_primes, 2)
    top_pr_str = ", ".join(f"{pr} primos ({pct:.1f}%)" for pr, _, pct in top_pr_trans) if top_pr_trans else "5, 6 primos"
    
    print(f"📊 Histórico: 5 primos (~33%), 6 primos (~30%), 4 primos (~19%), 7 primos (~11%)")
    print(f"🎯 Último concurso teve: {last_primes} primos.")
    if top_pr_trans:
        print(f"🔄 Transições mais frequentes pós {last_primes} primos: {top_pr_str}")
        
    primes_input = input("Faixa de PRIMOS [P = Padrão (5-6) | N = Não usar | ou digite ex: 4-6]: ").strip()
    primes_choice = parse_filter_choice(primes_input, 5, 6)
    if primes_choice is not None:
        min_pr, max_pr = primes_choice
        label = "Padrão" if primes_choice == (5, 6) else "Personalizado"
        stat = pipeline.apply("primes", lambda c: min_pr <= count_primes(c) <= max_pr)
        print(f"⚡ Filtro aplicado [{label}: {min_pr} a {max_pr}]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
    else:
        print("⏩ Filtro de Números Primos DESATIVADO (não aplicado).")

    # ==========================================================
    # PASSO 7: MOLDURA (BORDA)
    # ==========================================================
    prompt_step_header(7, "Moldura (Borda do Volante)")
    print("ℹ️ Borda (16 números): 01-05, 06, 10, 11, 15, 16, 20, 21-25")
    last_border = count_border(last_dezenas)
    
    border_trans = calc_rule_transitions(sorted_contests, lambda c: count_border(c['dezenas']))
    top_b_trans = get_top_transitions(border_trans, last_border, 2)
    top_b_str = ", ".join(f"{b} borda ({pct:.1f}%)" for b, _, pct in top_b_trans) if top_b_trans else "10, 9 borda"
    
    print(f"📊 Histórico: 10 borda (~31%), 9 borda (~28%), 11 borda (~17%), 8 borda (~11%)")
    print(f"🎯 Último concurso teve: {last_border} na borda.")
    if top_b_trans:
        print(f"🔄 Transições mais frequentes pós {last_border} borda: {top_b_str}")
        
    border_input = input("Faixa na MOLDURA [P = Padrão (9-11) | N = Não usar | ou digite ex: 9-11]: ").strip()
    border_choice = parse_filter_choice(border_input, 9, 11)
    if border_choice is not None:
        min_b, max_b = border_choice
        label = "Padrão" if border_choice == (9, 11) else "Personalizado"
        stat = pipeline.apply("border", lambda c: min_b <= count_border(c) <= max_b)
        print(f"⚡ Filtro aplicado [{label}: {min_b} a {max_b}]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
    else:
        print("⏩ Filtro de Moldura DESATIVADO (não aplicado).")

    # ==========================================================
    # PASSO 8: SOMA TOTAL DAS DEZENAS
    # ==========================================================
    prompt_step_header(8, "Soma Total das Dezenas")
    last_sum = calc_sum(last_dezenas)
    print(f"📊 Média histórica da soma: ~195 a 200 (80% dos concursos ficam entre 170 e 220)")
    print(f"🎯 Último concurso teve soma: {last_sum}")
    
    sum_input = input("Faixa da SOMA total [P = Padrão (170-220) | N = Não usar | ou digite ex: 180-210]: ").strip()
    sum_choice = parse_filter_choice(sum_input, 170, 220)
    if sum_choice is not None:
        min_s, max_s = sum_choice
        label = "Padrão" if sum_choice == (170, 220) else "Personalizado"
        stat = pipeline.apply("sum", lambda c: min_s <= calc_sum(c) <= max_s)
        print(f"⚡ Filtro aplicado [{label}: {min_s} a {max_s}]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
    else:
        print("⏩ Filtro de Soma Total DESATIVADO (não aplicado).")

    # ==========================================================
    # PASSO 9: NÚMEROS DE FIBONACCI
    # ==========================================================
    prompt_step_header(9, "Números de Fibonacci")
    print("ℹ️ Fibonacci (7 números): 01, 02, 03, 05, 08, 13, 21")
    last_fib = count_fibonacci(last_dezenas)
    print(f"📊 Histórico: 4 fibonacci (~38%), 5 fibonacci (~30%), 3 fibonacci (~19%)")
    print(f"🎯 Último concurso teve: {last_fib} números de Fibonacci.")
    
    fib_input = input("Faixa de FIBONACCI [P = Padrão (3-5) | N = Não usar | ou digite ex: 3-5]: ").strip()
    fib_choice = parse_filter_choice(fib_input, 3, 5)
    if fib_choice is not None:
        min_fib, max_fib = fib_choice
        label = "Padrão" if fib_choice == (3, 5) else "Personalizado"
        stat = pipeline.apply("fibonacci", lambda c: min_fib <= count_fibonacci(c) <= max_fib)
        print(f"⚡ Filtro aplicado [{label}: {min_fib} a {max_fib}]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
    else:
        print("⏩ Filtro de Fibonacci DESATIVADO (não aplicado).")

    # ==========================================================
    # PASSO 10: MÚLTIPLOS DE 3
    # ==========================================================
    prompt_step_header(10, "Múltiplos de 3")
    print("ℹ️ Múltiplos de 3 (8 números): 03, 06, 09, 12, 15, 18, 21, 24")
    last_m3 = count_multiples_of_3(last_dezenas)
    print(f"📊 Histórico: 5 múltiplos (~35%), 4 múltiplos (~27%), 6 múltiplos (~18%)")
    print(f"🎯 Último concurso teve: {last_m3} múltiplos de 3.")
    
    m3_input = input("Faixa de MÚLTIPLOS DE 3 [P = Padrão (4-6) | N = Não usar | ou digite ex: 4-6]: ").strip()
    m3_choice = parse_filter_choice(m3_input, 4, 6)
    if m3_choice is not None:
        min_m3, max_m3 = m3_choice
        label = "Padrão" if m3_choice == (4, 6) else "Personalizado"
        stat = pipeline.apply("multiples_of_3", lambda c: min_m3 <= count_multiples_of_3(c) <= max_m3)
        print(f"⚡ Filtro aplicado [{label}: {min_m3} a {max_m3}]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
    else:
        print("⏩ Filtro de Múltiplos de 3 DESATIVADO (não aplicado).")

    # ==========================================================
    # PASSO 11: DISTRIBUIÇÃO DE LINHAS E COLUNAS
    # ==========================================================
    prompt_step_header(11, "Distribuição de Linhas e Colunas")
    print("ℹ️ Evita linhas ou colunas vazias (0 dezenas) ou superlotadas (5 dezenas).")
    print("📊 Padrão equilibrado: Entre 1 e 4 dezenas por linha e por coluna.")
    
    rc_input = input("Equilíbrio de Linhas e Colunas [P = Padrão (1-4) | N = Não usar | ou digite ex: 1-4]: ").strip()
    rc_choice = parse_filter_choice(rc_input, 1, 4)
    if rc_choice is not None:
        min_rc, max_rc = rc_choice
        label = "Padrão" if rc_choice == (1, 4) else "Personalizado"
        def rc_predicate(c):
            rows = eval_rows_distribution(c)
            if any(r < min_rc or r > max_rc for r in rows):
                return False
            cols = eval_cols_distribution(c)
            if any(col < min_rc or col > max_rc for col in cols):
                return False
            return True
            
        stat = pipeline.apply("rows_cols", rc_predicate)
        print(f"⚡ Filtro aplicado [{label}: {min_rc} a {max_rc} por linha/col]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
    else:
        print("⏩ Filtro de Linhas e Colunas DESATIVADO (não aplicado).")

    # ==========================================================
    # PASSO 12: SEQUÊNCIAS CONSECUTIVAS (DEZENAS SEGUIDAS)
    # ==========================================================
    prompt_step_header(12, "Sequências Consecutivas (Dezenas Seguidas)")
    print("ℹ️ Sequência: mede o maior bloco de dezenas sorteadas seguidas (ex: 01-02-03 = 3 seguidas).")
    print("📊 Histórico: 4 seguidas (~31.5%), 5 seguidas (~27.1%), 3 seguidas (~12.7%), 6 seguidas (~15.4%)")
    
    last_seq_longest, _ = eval_consecutives(last_dezenas)
    seq_trans = calc_rule_transitions(sorted_contests, lambda c: eval_consecutives(sorted(c['dezenas']))[0])
    top_seq_trans = get_top_transitions(seq_trans, last_seq_longest, 2)
    top_seq_str = ", ".join(f"máx {v} ({pct:.1f}%)" for v, _, pct in top_seq_trans) if top_seq_trans else "máx 4, máx 5"
    print(f"🎯 Último concurso teve maior sequência de: {last_seq_longest} dezenas seguidas.")
    if top_seq_trans:
        print(f"🔄 Transições mais frequentes pós máx {last_seq_longest}: {top_seq_str}")

    seq_input = input("\nMaior sequência consecutiva [P = Padrão (máx 5) | N = Não usar | ou digite ex: 4 ou 3-5]: ").strip()
    seq_choice = parse_sequence_choice(seq_input, default_max=5)
    if seq_choice is not None:
        min_seq, max_seq = seq_choice
        if min_seq == 1:
            label = f"máx {max_seq} seguidas"
            stat = pipeline.apply("consecutives", lambda c: eval_consecutives(c)[0] <= max_seq)
        else:
            label = f"{min_seq} a {max_seq} seguidas"
            stat = pipeline.apply("consecutives", lambda c: min_seq <= eval_consecutives(c)[0] <= max_seq)
        print(f"⚡ Filtro aplicado [{label}]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
    else:
        print("⏩ Filtro de Sequências Consecutivas DESATIVADO (não aplicado).")

    # ==========================================================
    # PASSO 13: PULO TRIPLO (GAP DE 3 NÚMEROS FALTANTES)
    # ==========================================================
    prompt_step_header(13, "Pulo Triplo (Gap de 3 Dezenas Faltantes)")
    print("ℹ️ Pulo Triplo: ocorre quando há exatamente 3 números não sorteados entre duas dezenas do jogo.")
    print("   Exemplo: 05 e 09 (faltam 06, 07, 08 -> dif 4) ou 10 e 14 (faltam 11, 12, 13).")
    print("   (Regra de espaçamento/gap, totalmente independente de sequências consecutivas).")
    print("📊 Histórico: Sem pulo (0): ~55.9% | 1 pulo triplo: ~37.8% | 2 pulos: ~6.2% (0 ou 1 pulo = 93.7%)")
    
    last_tj_count = count_triple_jumps(last_dezenas)
    tj_trans = calc_rule_transitions(sorted_contests, lambda c: count_triple_jumps(sorted(c['dezenas'])))
    top_tj_trans = get_top_transitions(tj_trans, last_tj_count, 2)
    top_tj_str = ", ".join(f"{v} pulo(s) ({pct:.1f}%)" for v, _, pct in top_tj_trans) if top_tj_trans else "0 ou 1 pulo"
    print(f"🎯 Último concurso teve: {last_tj_count} pulo(s) triplo(s).")
    if top_tj_trans:
        print(f"🔄 Transições mais frequentes pós {last_tj_count} pulo(s): {top_tj_str}")

    tj_input = input("\nQuantidade de PULOS TRIPLOS [P = Padrão (0-1) | 0 = Sem pulo | 1 = Exatamente 1 | S = Com pulo (>=1) | N = Não usar]: ").strip()
    tj_choice = parse_triple_jump_choice(tj_input, default_min=0, default_max=1)
    if tj_choice is not None:
        min_tj, max_tj = tj_choice
        if min_tj == max_tj:
            label = f"{min_tj} pulo(s) triplo(s)" if min_tj > 0 else "Sem pulo triplo (0)"
        elif min_tj == 1 and max_tj >= 3:
            label = "Com pulo triplo (>= 1)"
        else:
            label = f"{min_tj} a {max_tj} pulos triplos"
        stat = pipeline.apply("triple_jump", lambda c: min_tj <= count_triple_jumps(c) <= max_tj)
        print(f"⚡ Filtro aplicado [{label}]: {stat['removed_count']:,} removidos | Restantes: {stat['remaining_count']:,}")
    else:
        print("⏩ Filtro de Pulo Triplo DESATIVADO (não aplicado).")

    # ==========================================================
    # FINALIZAÇÃO DOS FILTROS E CURADORIA INTERATIVA
    # ==========================================================
    total_remaining = len(pipeline.candidates)
    print("\n" + "="*58)
    print(f"🏁 PROCESSAMENTO CONCLUÍDO! Total de jogos filtrados: {total_remaining:,}")
    print("="*58)

    if total_remaining == 0:
        print("\n⚠️ Todos os candidatos foram eliminados pelos filtros combinados.")
        print("Dica: Tente relaxar um ou mais filtros na próxima execução.")
        input("\n[ Pressione ENTER para voltar ao menu ]")
        return

    # Inicia a tela de revisão e eliminação de 10 em 10
    curate_games_paginated(pipeline.candidates)


def curate_games_paginated(games_list):
    """
    Interface de revisão paginada de 10 em 10 jogos.
    Permite eliminar jogos específicos da página e finalizar a lista.
    """
    current_games = list(games_list)
    page_size = 10
    current_page = 0

    while True:
        clear_screen()
        total_games = len(current_games)
        if total_games == 0:
            print("⚠️ Todos os jogos foram eliminados.")
            input("\n[ Pressione ENTER para voltar ao menu ]")
            return

        total_pages = (total_games + page_size - 1) // page_size
        if current_page >= total_pages:
            current_page = max(0, total_pages - 1)

        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, total_games)
        page_items = current_games[start_idx:end_idx]

        print("======================================================================")
        print(f"           CURADORIA DE JOGOS (Página {current_page + 1} de {total_pages} | Total: {total_games} jogos)")
        print("======================================================================")
        
        for slot, game in enumerate(page_items, start=1):
            formatted_game = format_game(game)
            seq_len = eval_consecutives(game)[0]
            tj_count = count_triple_jumps(game)
            print(f"  [{slot:2d}]  {formatted_game}  (Seq: {seq_len} | Pulos 3x: {tj_count})")

        print("----------------------------------------------------------------------")
        print("Comandos:")
        print("  - Digite os números dos jogos da página para ELIMINAR (ex: 2 ou 1, 4, 8)")
        print("  - [P] Próxima página   | [A] Página anterior")
        print("  - [F] Finalizar e exibir lista final mantida")
        print("  - [S] Sair / Cancelar")
        
        cmd = input("\nOpção: ").strip().lower()

        if cmd == 'p' or cmd == '':
            if current_page < total_pages - 1:
                current_page += 1
            else:
                print("ℹ️ Você já está na última página.")
        elif cmd == 'a':
            if current_page > 0:
                current_page -= 1
            else:
                print("ℹ️ Você já está na primeira página.")
        elif cmd == 'f':
            # Finalizar e exibir todos os jogos mantidos
            show_final_games_summary(current_games)
            return
        elif cmd == 's':
            confirm = input("Deseja realmente sair e descartar os jogos gerados? (s/N): ").strip().lower()
            if confirm == 's':
                return
        else:
            # Processar eliminação por número de slot (1 a len(page_items))
            cleaned_slots = cmd.replace(',', ' ').replace(';', ' ')
            to_remove_slots = []
            for token in cleaned_slots.split():
                if token.isdigit():
                    s = int(token)
                    if 1 <= s <= len(page_items):
                        to_remove_slots.append(s)
            
            if to_remove_slots:
                # Índices absolutos a remover
                abs_indices = sorted([start_idx + (s - 1) for s in to_remove_slots], reverse=True)
                for idx in abs_indices:
                    del current_games[idx]
                print(f"🗑️ {len(abs_indices)} jogo(s) eliminado(s) com sucesso.")
            else:
                print("⚠️ Comando ou número de jogo não reconhecido.")


def show_final_games_summary(final_games):
    """Exibe na tela a lista limpa e formatada de todos os jogos mantidos."""
    clear_screen()
    print("======================================================================")
    print(f"                JOGOS FINAIS SELECIONADOS ({len(final_games)} jogos)")
    print("======================================================================")
    for i, game in enumerate(final_games, start=1):
        print(f"Jogo {i:02d}:  {format_game(game)}")
    print("======================================================================")
    print(f"✅ Total de {len(final_games)} jogos prontos para aposta!")
    input("\n[ Pressione ENTER para retornar ao menu principal ]")
