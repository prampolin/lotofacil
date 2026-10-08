def calculate_cycles(contests):
    """
    Calcula os ciclos históricos da Lotofácil conforme a regra cycle.md.
    Retorna:
    - Lista com o consolidado de cada ciclo.
    - Dicionário mapeando cada concurso para o ciclo ao qual pertence.
    """
    cycles = []
    current_cycle_number = 1
    seen_numbers = set()
    start_contest = None
    contest_to_cycle = {}
    cycle_contests = []
    
    for contest in contests:
        if not start_contest:
            start_contest = contest['concurso']
            
        seen_numbers.update(contest['dezenas'])
        cycle_contests.append(contest['concurso'])
        
        is_closed = len(seen_numbers) == 25
        
        cycle_info = {
            "cycle_number": current_cycle_number,
            "status": "closed" if is_closed else "open",
            "start_contest": start_contest,
            "seen_count": len(seen_numbers),
            "is_closing_contest": is_closed,
            "length_so_far": len(cycle_contests)
        }
        contest_to_cycle[contest['concurso']] = cycle_info
        
        if is_closed:
            cycle_info["end_contest"] = contest['concurso']
            cycle_info["length"] = len(cycle_contests)
            cycles.append(cycle_info)
            
            # Reseta para o próximo ciclo
            current_cycle_number += 1
            seen_numbers = set()
            start_contest = None
            cycle_contests = []
            
    # Adiciona o ciclo atual que ainda está aberto
    if start_contest:
        cycles.append({
            "cycle_number": current_cycle_number,
            "status": "open",
            "start_contest": start_contest,
            "seen_count": len(seen_numbers),
            "length": len(cycle_contests),
            "is_closing_contest": False
        })
        
    return cycles, contest_to_cycle
