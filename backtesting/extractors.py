"""
Extratores de características estatísticas por concurso para a Lotofácil.
"""

from engine.rules_evaluator import (
    PRIMES, FIBONACCI, MULTIPLES_OF_3, BORDER, CENTER,
    count_odds, count_evens, count_primes, count_border, count_center,
    count_fibonacci, count_multiples_of_3, calc_sum,
    eval_rows_distribution, eval_cols_distribution,
    eval_consecutives
)

def extract_parity(dezenas):
    odds = count_odds(dezenas)
    return f"{odds}I-{15-odds}P"

def extract_sum_range(dezenas):
    s = calc_sum(dezenas)
    group_start = (s // 10) * 10
    return f"{group_start}-{group_start+9}"

def extract_primes(dezenas):
    return count_primes(dezenas)

def extract_fibonacci(dezenas):
    return count_fibonacci(dezenas)

def extract_multiples_of_3(dezenas):
    return count_multiples_of_3(dezenas)

def extract_border(dezenas):
    return count_border(dezenas)

def extract_center(dezenas):
    return count_center(dezenas)

def extract_row_distribution(dezenas):
    return "-".join(map(str, eval_rows_distribution(dezenas)))

def extract_col_distribution(dezenas):
    return "-".join(map(str, eval_cols_distribution(dezenas)))

def extract_consecutives(dezenas):
    longest, pairs = eval_consecutives(sorted(dezenas))
    return f"max_{longest}-pairs_{pairs}"

def extract_repetitions(curr_dezenas, prev_dezenas):
    if not prev_dezenas:
        return None
    return len(set(curr_dezenas).intersection(set(prev_dezenas)))

RULE_DEFINITIONS = {
    "parity": {
        "name": "Paridade (Ímpares / Pares)",
        "extractor": lambda c, prev=None: extract_parity(c['dezenas']),
        "is_transition": False,
        "support_pool_reduction": True,
        "predicate_builder": lambda val: (lambda cand: extract_parity(cand) == val)
    },
    "sum_range": {
        "name": "Faixa de Soma (de 10 em 10)",
        "extractor": lambda c, prev=None: extract_sum_range(c['dezenas']),
        "is_transition": False,
        "support_pool_reduction": True,
        "predicate_builder": lambda val: (lambda cand: extract_sum_range(cand) == val)
    },
    "primes": {
        "name": "Números Primos",
        "extractor": lambda c, prev=None: extract_primes(c['dezenas']),
        "is_transition": False,
        "support_pool_reduction": True,
        "predicate_builder": lambda val: (lambda cand: extract_primes(cand) == val)
    },
    "fibonacci": {
        "name": "Números de Fibonacci",
        "extractor": lambda c, prev=None: extract_fibonacci(c['dezenas']),
        "is_transition": False,
        "support_pool_reduction": True,
        "predicate_builder": lambda val: (lambda cand: extract_fibonacci(cand) == val)
    },
    "multiples_of_3": {
        "name": "Múltiplos de 3",
        "extractor": lambda c, prev=None: extract_multiples_of_3(c['dezenas']),
        "is_transition": False,
        "support_pool_reduction": True,
        "predicate_builder": lambda val: (lambda cand: extract_multiples_of_3(cand) == val)
    },
    "border": {
        "name": "Moldura (Borda)",
        "extractor": lambda c, prev=None: extract_border(c['dezenas']),
        "is_transition": False,
        "support_pool_reduction": True,
        "predicate_builder": lambda val: (lambda cand: extract_border(cand) == val)
    },
    "row_distribution": {
        "name": "Distribuição por Linhas",
        "extractor": lambda c, prev=None: extract_row_distribution(c['dezenas']),
        "is_transition": False,
        "support_pool_reduction": True,
        "predicate_builder": lambda val: (lambda cand: extract_row_distribution(cand) == val)
    },
    "col_distribution": {
        "name": "Distribuição por Colunas",
        "extractor": lambda c, prev=None: extract_col_distribution(c['dezenas']),
        "is_transition": False,
        "support_pool_reduction": True,
        "predicate_builder": lambda val: (lambda cand: extract_col_distribution(cand) == val)
    },
    "consecutives": {
        "name": "Sequências Consecutivas",
        "extractor": lambda c, prev=None: extract_consecutives(c['dezenas']),
        "is_transition": False,
        "support_pool_reduction": True,
        "predicate_builder": lambda val: (lambda cand: extract_consecutives(cand) == val)
    },
    "repetitions": {
        "name": "Repetições do Concurso Anterior",
        "extractor": lambda c, prev=None: extract_repetitions(c['dezenas'], prev['dezenas'] if prev else None),
        "is_transition": True,
        "support_pool_reduction": True,
        "predicate_builder": lambda val, prev_set=None: (
            lambda cand: len(set(cand).intersection(prev_set)) == val if prev_set else True
        )
    }
}
