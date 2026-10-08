def calculate_current_delays(contests):
    """
    Calcula o atraso atual de cada dezena até o último concurso fornecido na lista.
    Conforme a regra number-delay.md.
    """
    delays = {i: 0 for i in range(1, 26)}
    
    for contest in contests:
        drawn = set(contest['dezenas'])
        for i in range(1, 26):
            if i in drawn:
                delays[i] = 0
            else:
                delays[i] += 1
                
    return delays

def calculate_frequencies(contests_window):
    """
    Calcula a frequência percentual de cada número em uma janela de concursos.
    """
    total_contests = len(contests_window)
    if total_contests == 0:
        return {i: 0 for i in range(1, 26)}
        
    counts = {i: 0 for i in range(1, 26)}
    for contest in contests_window:
        for dezena in contest['dezenas']:
            counts[dezena] += 1
            
    frequencies = {}
    for i in range(1, 26):
        pct = (counts[i] / total_contests) * 100
        frequencies[i] = int(round(pct))
        
    return frequencies
