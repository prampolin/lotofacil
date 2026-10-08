"""
Módulo para geração otimizada do Pool de Candidatos da Lotofácil
com base nas dezenas do concurso anterior, faixas de repetições,
dezenas fixas e dezenas excluídas.
"""

import itertools


def generate_candidate_pool(previous_numbers, allowed_repetitions, fixed_numbers=None, excluded_numbers=None):
    """
    Gera o conjunto de candidatos (15 dezenas cada) respeitando:
    - previous_numbers: 15 dezenas do concurso anterior
    - allowed_repetitions: lista/conjunto de inteiros R (quantas dezenas repetir do concurso anterior)
    - fixed_numbers: dezenas que OBRIGATORIAMENTE devem estar no jogo
    - excluded_numbers: dezenas que NÃO podem estar no jogo
    
    Retorna uma lista de tuplas ordenadas (cada tupla tem 15 números).
    """
    fixed_set = set(fixed_numbers) if fixed_numbers else set()
    excluded_set = set(excluded_numbers) if excluded_numbers else set()
    
    # Validações de consistência
    if fixed_set.intersection(excluded_set):
        raise ValueError("Uma dezena não pode ser fixa e excluída simultaneamente.")
    if len(fixed_set) > 15:
        raise ValueError("O número de dezenas fixas não pode ser maior que 15.")
        
    all_numbers = set(range(1, 26))
    prev_set = set(previous_numbers)
    missing_set = all_numbers - prev_set
    
    # Separa fixas e excluídas por grupo (concurso anterior vs ausentes)
    fixed_prev = fixed_set.intersection(prev_set)
    fixed_missing = fixed_set.intersection(missing_set)
    
    avail_prev = sorted(list(prev_set - fixed_prev - excluded_set))
    avail_missing = sorted(list(missing_set - fixed_missing - excluded_set))
    
    candidates = []
    
    # Para cada quantidade de repetições permitida
    for r in sorted(allowed_repetitions):
        needed_prev = r - len(fixed_prev)
        needed_missing = (15 - r) - len(fixed_missing)
        
        # Verifica se é matematicamente viável
        if needed_prev < 0 or needed_prev > len(avail_prev):
            continue
        if needed_missing < 0 or needed_missing > len(avail_missing):
            continue
            
        prev_combos = list(itertools.combinations(avail_prev, needed_prev)) if needed_prev > 0 else [()]
        miss_combos = list(itertools.combinations(avail_missing, needed_missing)) if needed_missing > 0 else [()]
        
        base_fixed = tuple(sorted(fixed_set))
        
        for cp in prev_combos:
            for cm in miss_combos:
                # Junta fixas + selecionadas do sorteio anterior + selecionadas dos ausentes
                comb = sorted(base_fixed + cp + cm)
                candidates.append(tuple(comb))
                
    return candidates
