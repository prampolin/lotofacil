"""
Módulo do Pipeline de Filtros e Análise de Transições Estatísticas para a Lotofácil.
Executa filtros sequenciais com métricas precisas e calcula probabilidades de transição.
"""

import collections
import itertools
from engine.rules_evaluator import (
    PRIMES, FIBONACCI, MULTIPLES_OF_3, BORDER, CENTER,
    count_odds, count_primes, count_border, count_fibonacci,
    count_multiples_of_3, calc_sum, count_cycle_numbers,
    eval_rows_distribution, eval_cols_distribution,
    eval_consecutives, eval_triple_jump, count_triple_jumps
)
from engine.cycle import calculate_cycles


class FilterPipeline:
    def __init__(self, candidates):
        self.candidates = candidates
        self.history = []

    def apply(self, rule_name, predicate_fn):
        """
        Aplica um filtro ao pool de candidatos atual.
        predicate_fn(candidate_tuple) -> bool (True para manter, False para eliminar)
        Retorna as estatísticas do filtro aplicado.
        """
        input_count = len(self.candidates)
        filtered = [c for c in self.candidates if predicate_fn(c)]
        remaining_count = len(filtered)
        removed_count = input_count - remaining_count
        
        stat = {
            "rule": rule_name,
            "input_count": input_count,
            "removed_count": removed_count,
            "remaining_count": remaining_count
        }
        self.candidates = filtered
        self.history.append(stat)
        return stat


def build_historical_set(contests):
    """Retorna um conjunto contendo todas as combinações de 15 dezenas já sorteadas na história."""
    return {tuple(sorted(c['dezenas'])) for c in contests}


def build_historical_14_set(contests):
    """
    Retorna um conjunto contendo todas as combinações de 14 dezenas contidas nos sorteios históricos.
    Para cada um dos concursos de 15 dezenas, extrai as C(15, 14) = 15 combinações (ex: 3.784 x 15).
    """
    hist_14 = set()
    for c in contests:
        dezenas = sorted(c['dezenas'])
        for sub in itertools.combinations(dezenas, 14):
            hist_14.add(sub)
    return hist_14


def is_historically_drawn(candidate, hist_14_set, hist_15_set=None):
    """
    Verifica se um jogo candidato (15 dezenas) possui 14 ou 15 dezenas iguais a algum sorteio histórico.
    Se hist_15_set for fornecido, testa primeiro se o jogo de 15 dezenas é idêntico a algum concurso (O(1)).
    Em seguida, verifica se qualquer uma das 15 combinações de 14 dezenas do candidato está em hist_14_set.
    """
    cand_tuple = tuple(sorted(candidate)) if not isinstance(candidate, tuple) else candidate
    if hist_15_set is not None and cand_tuple in hist_15_set:
        return True
    for sub in itertools.combinations(cand_tuple, 14):
        if sub in hist_14_set:
            return True
    return False


def get_current_cycle_info(contests):
    """
    Identifica o ciclo atual e as dezenas que ainda não foram sorteadas nele.
    Retorna (cycle_number, missing_numbers, length_so_far)
    """
    sorted_contests = sorted(contests, key=lambda c: c['concurso'])
    cycles, _ = calculate_cycles(sorted_contests)
    
    current_cycle = cycles[-1] if cycles else None
    if not current_cycle or current_cycle.get('status') == 'closed':
        # Se fechou no último concurso, o próximo concurso inicia um ciclo novo
        cycle_num = (current_cycle['cycle_number'] + 1) if current_cycle else 1
        return cycle_num, set(range(1, 26)), 0
        
    # Identifica as dezenas que já saíram no ciclo aberto atual
    seen = set()
    start_concurso = current_cycle['start_contest']
    for c in sorted_contests:
        if c['concurso'] >= start_concurso:
            seen.update(c['dezenas'])
            
    missing = set(range(1, 26)) - seen
    return current_cycle['cycle_number'], missing, current_cycle.get('length', 0)


def calc_rule_transitions(contests, extract_val_fn):
    """
    Calcula matriz de transição de um valor para o próximo concurso.
    extract_val_fn(contest_dict) -> valor comparável
    Retorna dicionário: { valor_anterior: Counter({ proximo_valor: contagem }) }
    """
    sorted_contests = sorted(contests, key=lambda c: c['concurso'])
    transitions = collections.defaultdict(collections.Counter)
    
    for i in range(len(sorted_contests) - 1):
        v1 = extract_val_fn(sorted_contests[i])
        v2 = extract_val_fn(sorted_contests[i + 1])
        transitions[v1][v2] += 1
        
    return transitions


def get_top_transitions(transitions, last_val, top_n=3):
    """
    Retorna as transições mais frequentes a partir do último valor.
    Lista de tuplas: [(proximo_valor, frequencia, percentual)]
    """
    counts = transitions.get(last_val, collections.Counter())
    total = sum(counts.values())
    if total == 0:
        return []
        
    res = []
    for val, count in counts.most_common(top_n):
        pct = (count / total) * 100.0
        res.append((val, count, pct))
    return res
