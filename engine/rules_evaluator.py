"""
Avaliadores de regras estatísticas para combinações da Lotofácil.
Todas as funções são otimizadas para processar candidatos de forma rápida.
"""

PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23}
FIBONACCI = {1, 2, 3, 5, 8, 13, 21}
MULTIPLES_OF_3 = {3, 6, 9, 12, 15, 18, 21, 24}
BORDER = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
CENTER = {7, 8, 9, 12, 13, 14, 17, 18, 19}
CROSS = {3, 8, 11, 12, 13, 14, 15, 18, 23}

ROWS = [
    {1, 2, 3, 4, 5},
    {6, 7, 8, 9, 10},
    {11, 12, 13, 14, 15},
    {16, 17, 18, 19, 20},
    {21, 22, 23, 24, 25}
]

COLS = [
    {1, 6, 11, 16, 21},
    {2, 7, 12, 17, 22},
    {3, 8, 13, 18, 23},
    {4, 9, 14, 19, 24},
    {5, 10, 15, 20, 25}
]


def count_odds(comb):
    """Retorna a quantidade de números ímpares."""
    return sum(1 for n in comb if n % 2 != 0)


def count_evens(comb):
    """Retorna a quantidade de números pares."""
    return sum(1 for n in comb if n % 2 == 0)


def count_primes(comb):
    """Retorna a quantidade de números primos."""
    return sum(1 for n in comb if n in PRIMES)


def count_fibonacci(comb):
    """Retorna a quantidade de números de Fibonacci."""
    return sum(1 for n in comb if n in FIBONACCI)


def count_multiples_of_3(comb):
    """Retorna a quantidade de múltiplos de 3."""
    return sum(1 for n in comb if n in MULTIPLES_OF_3)


def count_border(comb):
    """Retorna a quantidade de números na moldura."""
    return sum(1 for n in comb if n in BORDER)


def count_center(comb):
    """Retorna a quantidade de números no miolo/centro."""
    return sum(1 for n in comb if n in CENTER)


def calc_sum(comb):
    """Retorna a soma total das dezenas."""
    return sum(comb)


def count_cycle_numbers(comb, missing_cycle_numbers):
    """Retorna quantas dezenas do ciclo atual estão presentes na combinação."""
    if not missing_cycle_numbers:
        return 0
    return sum(1 for n in comb if n in missing_cycle_numbers)


def eval_rows_distribution(comb):
    """Retorna tupla com a quantidade de dezenas em cada uma das 5 linhas."""
    comb_set = set(comb) if not isinstance(comb, set) else comb
    return tuple(len(comb_set.intersection(r)) for r in ROWS)


def eval_cols_distribution(comb):
    """Retorna tupla com a quantidade de dezenas em cada uma das 5 colunas."""
    comb_set = set(comb) if not isinstance(comb, set) else comb
    return tuple(len(comb_set.intersection(c)) for c in COLS)


def eval_consecutives(sorted_comb):
    """
    Avalia sequências consecutivas em uma combinação ordenada:
    Retorna (longest_sequence, consecutive_pairs)
    """
    longest = 1
    current = 1
    pairs = 0
    
    for i in range(len(sorted_comb) - 1):
        if sorted_comb[i+1] == sorted_comb[i] + 1:
            current += 1
            pairs += 1
            if current > longest:
                longest = current
        else:
            current = 1
            
    return longest, pairs


def count_triple_jumps(sorted_comb):
    """
    Retorna a quantidade de pulos triplos (3 números faltantes consecutivos entre 2 dezenas).
    Ou seja, contagem de ocorrências onde sorted_comb[i+1] - sorted_comb[i] == 4.
    """
    count = 0
    for i in range(len(sorted_comb) - 1):
        if sorted_comb[i+1] - sorted_comb[i] == 4:
            count += 1
    return count


def eval_triple_jump(sorted_comb):
    """
    Retorna True se houver pelo menos um pulo triplo (3 números faltantes consecutivos entre 2 dezenas).
    Ou seja, sorted_comb[i+1] - sorted_comb[i] == 4
    """
    return count_triple_jumps(sorted_comb) > 0

