import json
import os
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

from engine.cycle import calculate_cycles
from engine.delay import calculate_current_delays, calculate_frequencies

def render_movement_table(json_path):
    console = Console()
    
    if not os.path.exists(json_path):
        console.print("[bold red]Base de dados não encontrada. Atualize primeiro (Opção 0).[/bold red]")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        all_contests = json.load(f)
        
    if not all_contests:
        console.print("[bold red]Nenhum concurso encontrado na base.[/bold red]")
        return
        
    cycles, contest_to_cycle = calculate_cycles(all_contests)
    
    # Escopo visual: Últimos 2 ciclos completos + Atual
    last_cycle_num = cycles[-1]['cycle_number']
    target_start_cycle = max(1, last_cycle_num - 2)
    
    display_contests = [c for c in all_contests if contest_to_cycle[c['concurso']]['cycle_number'] >= target_start_cycle]
    
    if not display_contests:
        console.print("[red]Não foi possível determinar o escopo.[/red]")
        return
        
    # Cálculos de Métricas
    delays = calculate_current_delays(all_contests)
    frequencies = calculate_frequencies(display_contests)
    
    # Montando a Tabela
    table = Table(
        box=box.SIMPLE_HEAVY,
        show_lines=True,
        header_style="bold magenta"
    )
    
    table.add_column("Concursos", justify="center", style="bold")
    
    for i in range(1, 26):
        table.add_column(f"{i:02d}", justify="center")
        
    # Preenchendo Concursos
    for c in display_contests:
        c_num = c['concurso']
        c_info = contest_to_cycle[c_num]
        drawn_set = set(c['dezenas'])
        
        row_cells = [str(c_num)]
        for i in range(1, 26):
            if i in drawn_set:
                row_cells.append(f"[bold white on #800080] {i:02d} [/]")
            else:
                row_cells.append(f"[#555555] -- [/]")
                
        table.add_row(*row_cells)
        
        # Divisor de Fechamento de Ciclo
        if c_info['is_closing_contest']:
            cycle_num = c_info['cycle_number']
            length = c_info['length_so_far']
            span_cells = [f"[bold green]Ciclo {cycle_num}[/]"]
            # Preenche o resto da linha para não desalinhar (gambiarra visual pro console)
            for i in range(1, 26):
                if i == 5:
                    span_cells.append(f"[green]Fechou[/]")
                elif i == 10:
                    span_cells.append(f"[green]Com[/]")
                elif i == 15:
                    span_cells.append(f"[bold green]{length}[/]")
                elif i == 20:
                    span_cells.append(f"[green]Conc.[/]")
                else:
                    span_cells.append("")
            table.add_row(*span_cells, style="on #222222")
            
    # Rodapé 1: Atraso Atual
    delay_cells = ["[bold]Atraso[/bold]"]
    for i in range(1, 26):
        d = delays[i]
        if d == 0:
            style = "dim"
            val = " 0"
        elif 1 <= d <= 2:
            style = "white on #8b0000"
            val = f" {d}"
        elif 3 <= d <= 4:
            style = "bold white on #d2691e"
            val = f" {d}"
        else:
            style = "bold black on #ffd700"
            val = f" {d}"
        delay_cells.append(f"[{style}] {val} [/{style}]" if d>0 else f"[dim] {val} [/dim]")
    table.add_row(*delay_cells)
    
    # Rodapé 2: Frequência %
    freq_cells = ["[bold]Freq %[/bold]"]
    for i in range(1, 26):
        f = frequencies[i]
        if f <= 40:
            style = "black on #00ffff"
        elif 50 <= f <= 60:
            style = "white on #555555"
        elif 70 <= f <= 80:
            style = "bold white on #0000ff"
        else:
            style = "bold white on #000080"
        freq_cells.append(f"[{style}]{f:02d}[/{style}]")
    table.add_row(*freq_cells)
    
    console.print("\n")
    console.print(table)
    console.print("\n")
