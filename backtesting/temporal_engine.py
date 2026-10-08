"""
Motor de análises temporais: Matriz de Transições, Autocorrelação e Comparação de Eras.
"""

import collections
import math

def analyze_transitions(contests, rule_defs, top_k=3):
    """
    Calcula matriz de transição (estado atual -> próximo estado) para cada regra.
    """
    results = {}
    n = len(contests)

    for rule_key, rdef in rule_defs.items():
        extractor = rdef["extractor"]
        transitions = collections.defaultdict(collections.Counter)
        state_counts = collections.Counter()

        for i in range(1, n - 1):
            prev_c1 = contests[i - 1]
            c1 = contests[i]
            c2 = contests[i + 1]

            v1 = extractor(c1, prev_c1)
            v2 = extractor(c2, c1)

            if v1 is not None and v2 is not None:
                transitions[v1][v2] += 1
                state_counts[v1] += 1

        # Formata top transições para os estados mais frequentes
        top_states = [s for s, _ in state_counts.most_common(5)]
        rule_transition_data = []

        for st in top_states:
            total_trans = sum(transitions[st].values())
            if total_trans == 0:
                continue
            common = transitions[st].most_common(top_k)
            for next_st, cnt in common:
                pct = (cnt / total_trans) * 100.0
                rule_transition_data.append({
                    "from_state": str(st),
                    "to_state": str(next_st),
                    "count": cnt,
                    "total_from": total_trans,
                    "probability": round(pct, 1)
                })

        results[rule_key] = {
            "name": rdef["name"],
            "transitions": rule_transition_data
        }

    return results

def analyze_autocorrelation(contests, rule_defs, max_lag=10):
    """
    Calcula autocorrelação temporal para regras numéricas simples.
    Para regras categóricas, usa correspondência de repetição (lag-k match probability).
    """
    results = {}
    n = len(contests)

    for rule_key, rdef in rule_defs.items():
        extractor = rdef["extractor"]
        series = []
        for i in range(1, n):
            v = extractor(contests[i], contests[i - 1])
            if v is not None:
                series.append(v)

        if not series:
            continue

        lag_correlations = []
        # Verifica se é numérico
        is_numeric = isinstance(series[0], (int, float))

        if is_numeric:
            mean = sum(series) / len(series)
            var = sum((x - mean) ** 2 for x in series) / len(series)
            if var == 0:
                continue

            for lag in range(1, max_lag + 1):
                cov = sum((series[i] - mean) * (series[i - lag] - mean) for i in range(lag, len(series))) / (len(series) - lag)
                corr = cov / var
                lag_correlations.append({"lag": lag, "correlation": round(corr, 3)})
        else:
            # Mede probabilidade de manter o mesmo estado k passos depois
            for lag in range(1, max_lag + 1):
                matches = sum(1 for i in range(lag, len(series)) if series[i] == series[i - lag])
                rate = (matches / (len(series) - lag)) * 100.0
                lag_correlations.append({"lag": lag, "match_rate": round(rate, 2)})

        results[rule_key] = {
            "name": rdef["name"],
            "is_numeric": is_numeric,
            "lags": lag_correlations
        }

    return results

def analyze_eras(contests, rule_defs, num_eras=3):
    """
    Divide o histórico total em N eras (início, meio, recente) e compara estabilidade das métricas.
    """
    n = len(contests)
    era_size = n // num_eras
    eras_results = []

    for era_idx in range(num_eras):
        start = era_idx * era_size
        end = (era_idx + 1) * era_size if era_idx < num_eras - 1 else n
        sub_contests = contests[start:end]

        era_label = f"Era {era_idx + 1}: Concursos {sub_contests[0]['concurso']} a {sub_contests[-1]['concurso']}"
        era_stats = {}

        for rule_key, rdef in rule_defs.items():
            extractor = rdef["extractor"]
            vals = []
            for i in range(1, len(sub_contests)):
                v = extractor(sub_contests[i], sub_contests[i - 1])
                if v is not None:
                    vals.append(v)

            if not vals:
                continue

            counter = collections.Counter(vals)
            top_val, top_cnt = counter.most_common(1)[0]
            top_pct = (top_cnt / len(vals)) * 100.0

            era_stats[rule_key] = {
                "name": rdef["name"],
                "most_common_value": str(top_val),
                "frequency_pct": round(top_pct, 1),
                "unique_values_count": len(counter)
            }

        eras_results.append({
            "era_index": era_idx + 1,
            "label": era_label,
            "sample_size": len(sub_contests),
            "stats": era_stats
        })

    return eras_results
