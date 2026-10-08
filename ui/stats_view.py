import json
import os
from rich.console import Console
from rich.table import Table

from engine.stats import (
    calc_parity, calc_primes, calc_border, 
    calc_center, calc_cross, calc_sum, calc_rows, calc_repeated, calc_all_time_repeated,
    calc_group_distribution_repetition, calc_consecutive_draws
)

def render_stat(title, freq_list, total_contests):
    console = Console()
    table = Table(title=f"\n[bold magenta]{title}[/bold magenta]", show_lines=True)
    table.add_column("Padrão", justify="left", style="cyan", no_wrap=True)
    table.add_column("Frequência (Ocorrências)", justify="right", style="green")
    table.add_column("% do Histórico", justify="right", style="yellow")
    
    # Mostrar apenas os 15 mais frequentes para não poluir
    for pattern, count in freq_list[:15]:
        pct = (count / total_contests) * 100
        table.add_row(pattern, str(count), f"{pct:.2f}%")
        
    console.print(table)
    print("\n")


def render_group_distribution_repetition(contests):
    console = Console()
    res = calc_group_distribution_repetition(contests)
    if not res:
        console.print("[bold red]Dados insuficientes para calcular repetição entre concursos.[/bold red]")
        return

    total = res["total_transitions"]
    exact_reps = res["exact_signature_repeats"]
    exact_pct = res["exact_signature_pct"]

    console.print(f"\n[bold magenta]=== ANÁLISE DE REPETIÇÃO POR GRUPOS/LINHAS (01-05 a 21-25) ===[/bold magenta]")
    console.print(f"[dim]Total de transições consecutivas analisadas: {total:,}[/dim]\n")

    # Tabela 1: Quantidade de Grupos que repetem
    t1 = Table(title="[bold cyan]1. Quantidade de Grupos com Mesma Quantidade do Concurso Anterior[/bold cyan]", show_lines=True)
    t1.add_column("Grupos com Mesma Qtd", justify="left", style="cyan", no_wrap=True)
    t1.add_column("Ocorrências", justify="right", style="green")
    t1.add_column("% das Transições", justify="right", style="yellow")
    t1.add_column("Interpretação", justify="left", style="white")

    meanings = {
        0: "Todos os 5 grupos mudaram de quantidade",
        1: "Cenário mais frequente (4 grupos mudaram)",
        2: "Moderado (3 grupos mudaram)",
        3: "Baixo (2 grupos mudaram)",
        4: "Impossível matematicamente (soma fixa em 15)",
        5: "Repetição Integral (todos os 5 iguais)"
    }

    for k, cnt, pct in res["matching_groups"]:
        label = f"{k} de 5 grupos repetiram" if k != 5 else "5 de 5 grupos (INTEGRAL)"
        t1.add_row(label, f"{cnt:,}", f"{pct:.2f}%", meanings.get(k, ""))

    console.print(t1)
    console.print(f"[bold yellow]⚡ Repetição Integral da Assinatura (5 grupos iguais):[/bold yellow] Ocorreu apenas [bold green]{exact_reps}[/bold green] vezes ([bold yellow]{exact_pct:.2f}%[/bold yellow]).\n")

    # Tabela 2: Repetição por Grupo Individual
    t2 = Table(title="[bold cyan]2. Taxa de Repetição Individual de Cada Grupo[/bold cyan]", show_lines=True)
    t2.add_column("Grupo / Faixa", justify="left", style="cyan", no_wrap=True)
    t2.add_column("Repetiu a Qtd", justify="right", style="green")
    t2.add_column("% de Repetição", justify="right", style="yellow")

    for grp_label, cnt, pct in res["group_individuals"]:
        t2.add_row(grp_label, f"{cnt:,}", f"{pct:.2f}%")

    console.print(t2)
    print("\n")

    # Tabela 3: Assinaturas que mais repetiram integralmente
    if res["top_repeated_signatures"]:
        t3 = Table(title="[bold cyan]3. Assinaturas que mais Repetiram Integralmente (Top Ocorrências)[/bold cyan]", show_lines=True)
        t3.add_column("Assinatura (G1-G2-G3-G4-G5)", justify="left", style="cyan", no_wrap=True)
        t3.add_column("Repetiu no Próximo", justify="right", style="green")
        t3.add_column("Total de Saídas", justify="right", style="white")
        t3.add_column("Taxa de Repetição", justify="right", style="yellow")

        for sig_str, reps, tots, pct in res["top_repeated_signatures"][:10]:
            t3.add_row(sig_str, str(reps), str(tots), f"{pct:.2f}%")

        console.print(t3)
        print("\n")


def render_consecutive_draws(contests):
    console = Console()
    res = calc_consecutive_draws(contests)
    if not res:
        console.print("[bold red]Dados insuficientes para calcular sequências consecutivas.[/bold red]")
        return

    total = res["total_contests"]
    record = res["overall_record"]
    ranking = res["ranking"]

    console.print(f"\n[bold magenta]=== MAIOR SEQUÊNCIA CONSECUTIVA DE SAÍDAS POR DEZENA ===[/bold magenta]")
    console.print(f"[dim]Total de concursos analisados: {total:,}[/dim]\n")

    if record:
        rec_occ = ", ".join([f"conc. {s} ao {e}" for s, e in record["max_occurrences"]])
        console.print(
            f"🏆 [bold yellow]RECORDE HISTÓRICO ABSOLUTO:[/bold yellow] "
            f"A dezena [bold white on #800080] {record['number']:02d} [/] "
            f"saiu em [bold green]{record['max_streak']} concursos consecutivos[/bold green] "
            f"({rec_occ}).\n"
        )

    # Tabela 1: Ranking de todas as 25 dezenas
    t1 = Table(
        title="[bold cyan]1. Ranking de Maiores Sequências Consecutivas (Dezenas 01 a 25)[/bold cyan]",
        show_lines=True
    )
    t1.add_column("Rank", justify="center", style="bold", no_wrap=True)
    t1.add_column("Dezena", justify="center", no_wrap=True)
    t1.add_column("Maior Sequência", justify="center", style="bold green")
    t1.add_column("Período(s) do Recorde", justify="left", style="white")
    t1.add_column("Seq. Atual", justify="center")
    t1.add_column("Média por Sequência", justify="right", style="cyan")
    t1.add_column("Total de Saídas", justify="right", style="yellow")

    medals = {1: "🥇 1º", 2: "🥈 2º", 3: "🥉 3º"}

    for idx, r in enumerate(ranking, 1):
        rank_str = medals.get(idx, f"{idx:2d}º")
        num_cell = f"[bold white on #800080] {r['number']:02d} [/]"
        streak_cell = f"{r['max_streak']} conc."

        if len(r['max_occurrences']) > 1:
            per_str = ", ".join([f"{s} ao {e}" for s, e in r['max_occurrences']])
            per_cell = f"{per_str} [dim]({len(r['max_occurrences'])}x)[/dim]"
        else:
            s, e = r['max_occurrences'][0]
            per_cell = f"Conc. {s} ao {e}"

        cur = r['current_streak']
        if cur > 0:
            cur_cell = f"[bold yellow]{cur} conc.[/bold yellow]"
        else:
            cur_cell = "[dim]0 (ausente)[/dim]"

        avg_cell = f"{r['avg_streak']:.2f} conc."
        tot_cell = f"{r['total_draws']:,} ({r['draw_pct']:.1f}%)"

        t1.add_row(rank_str, num_cell, streak_cell, per_cell, cur_cell, avg_cell, tot_cell)

    console.print(t1)
    print("\n")

    # Tabela 2: Distribuição global do tamanho das sequências
    t2 = Table(
        title="[bold cyan]2. Distribuição Global de Tamanho das Sequências de Saída[/bold cyan]",
        show_lines=True
    )
    t2.add_column("Tamanho da Sequência", justify="left", style="cyan", no_wrap=True)
    t2.add_column("Ocorrências Históricas", justify="right", style="green")
    t2.add_column("% do Total de Sequências", justify="right", style="yellow")
    t2.add_column("Classificação / Dinâmica", justify="left", style="white")

    grouped_counts = {
        "1 concurso (Saiu e falhou no seguinte)": 0,
        "2 concursos seguidos": 0,
        "3 concursos seguidos": 0,
        "4 concursos seguidos": 0,
        "5 concursos seguidos": 0,
        "6 a 9 concursos seguidos": 0,
        "10 a 14 concursos seguidos": 0,
        "15 ou mais concursos seguidos": 0,
    }
    grouped_notes = {
        "1 concurso (Saiu e falhou no seguinte)": "Muito comum (~42%)",
        "2 concursos seguidos": "Frequente (~24%)",
        "3 concursos seguidos": "Moderado (~14%)",
        "4 concursos seguidos": "Ocasional (~9%)",
        "5 concursos seguidos": "Pouco frequente (~5%)",
        "6 a 9 concursos seguidos": "Raro (~7%)",
        "10 a 14 concursos seguidos": "Muito raro (~0.8%)",
        "15 ou mais concursos seguidos": "Extremamente raro / Recordes (< 0.1%)",
    }

    for length, cnt, pct in res["global_streak_distribution"]:
        if length == 1:
            grouped_counts["1 concurso (Saiu e falhou no seguinte)"] += cnt
        elif length == 2:
            grouped_counts["2 concursos seguidos"] += cnt
        elif length == 3:
            grouped_counts["3 concursos seguidos"] += cnt
        elif length == 4:
            grouped_counts["4 concursos seguidos"] += cnt
        elif length == 5:
            grouped_counts["5 concursos seguidos"] += cnt
        elif 6 <= length <= 9:
            grouped_counts["6 a 9 concursos seguidos"] += cnt
        elif 10 <= length <= 14:
            grouped_counts["10 a 14 concursos seguidos"] += cnt
        else:
            grouped_counts["15 ou mais concursos seguidos"] += cnt

    total_streaks = res["total_streaks_all"]
    for label, count in grouped_counts.items():
        pct = (count / total_streaks * 100) if total_streaks > 0 else 0.0
        t2.add_row(label, f"{count:,}", f"{pct:.2f}%", grouped_notes.get(label, ""))

    console.print(t2)
    print("\n")


def menu_estatisticas(json_path):
    console = Console()
    
    if not os.path.exists(json_path):
        console.print("[bold red]Base de dados não encontrada. Atualize primeiro (Opção 0).[/bold red]")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        contests = json.load(f)
        
    if not contests:
        console.print("[bold red]Nenhum concurso encontrado.[/bold red]")
        return
        
    total = len(contests)
    
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        console.print(f"[bold cyan]=== MENU DE ESTATÍSTICAS ({total} Concursos Analisados) ===[/bold cyan]\n")
        print("1 - Pares e Ímpares (Parity)")
        print("2 - Números Primos")
        print("3 - Moldura vs Miolo (Border & Center)")
        print("4 - Distribuição da Cruz")
        print("5 - Soma das Dezenas")
        print("6 - Distribuição por Linhas")
        print("7 - Repetidas do Concurso Anterior")
        print("8 - Repetidas em Toda a História (Todos x Todos)")
        print("9 - Repetição de Distribuição por Grupos (01-05 a 21-25)")
        print("10 - Maior Sequência Consecutiva de Saída por Dezena (Recordes)")
        print("V - Voltar ao Menu Principal")
        
        op = input("\nOpção: ").strip().lower()
        os.system('clear' if os.name == 'posix' else 'cls')
        
        if op == "1":
            render_stat("Frequência: Pares e Ímpares", calc_parity(contests), total)
        elif op == "2":
            render_stat("Frequência: Números Primos", calc_primes(contests), total)
        elif op == "3":
            render_stat("Frequência: Dezenas na Moldura", calc_border(contests), total)
            render_stat("Frequência: Dezenas no Miolo", calc_center(contests), total)
        elif op == "4":
            render_stat("Frequência: Dezenas na Cruz", calc_cross(contests), total)
        elif op == "5":
            render_stat("Frequência: Soma das Dezenas", calc_sum(contests), total)
        elif op == "6":
            render_stat("Frequência: Padrões de Linha (L1-L2-L3-L4-L5)", calc_rows(contests), total)
        elif op == "7":
            # Passamos (total - 1) porque o primeiro concurso não tem um anterior para comparar
            render_stat("Frequência: Repetidas do Concurso Anterior", calc_repeated(contests), total - 1 if total > 1 else 1)
        elif op == "8":
            console.print("[yellow]Calculando milhões de combinações (Todos x Todos)... Por favor, aguarde alguns segundos.[/yellow]")
            total_pairs = (total * (total - 1)) // 2
            render_stat(f"Frequência: Repetidas em Toda a História\nTotal de cruzamentos analisados: {total_pairs:,}", calc_all_time_repeated(contests), total_pairs if total_pairs > 0 else 1)
        elif op == "9":
            render_group_distribution_repetition(contests)
        elif op == "10":
            render_consecutive_draws(contests)
        elif op == "v" or op == "voltar":
            break
        else:
            print("Opção inválida.")
            
        input("[ Pressione ENTER para voltar às Estatísticas ]")

