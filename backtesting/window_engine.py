"""
Gerador de janelas para testes (Sliding Windows e Fixed Blocks).
"""

def generate_sliding_windows(contests, window_size=10, min_start_idx=None):
    """
    Gera pares (train_contests, target_contest, prev_target_contest).
    window_size: tamanho da janela histórica de treino.
    min_start_idx: a partir de qual índice começar a gerar alvos.
    """
    n = len(contests)
    start = window_size if min_start_idx is None else max(window_size, min_start_idx)
    
    for i in range(start, n):
        train = contests[i - window_size:i]
        target = contests[i]
        prev_target = contests[i - 1] if i > 0 else None
        yield (train, target, prev_target, i)

def generate_fixed_blocks(contests, block_size=10):
    """
    Gera testes em blocos fixos:
    Treino: [0..block_size-1] -> Alvo: block_size
    Treino: [block_size..2*block_size-1] -> Alvo: 2*block_size
    E assim por diante.
    """
    n = len(contests)
    i = block_size
    while i < n:
        train = contests[i - block_size:i]
        target = contests[i]
        prev_target = contests[i - 1]
        yield (train, target, prev_target, i)
        i += block_size
