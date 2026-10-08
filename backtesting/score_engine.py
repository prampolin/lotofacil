"""
Motor de avaliação e pontuação de regras.
Calcula Hit Rate, Sobrevivência e Redução de Pool com amostras pré-computadas.
"""

import collections
import random
import itertools

SAMPLE_POOL_SIZE = 50000

def generate_sample_pool(size=SAMPLE_POOL_SIZE, seed=42):
    """
    Gera uma amostra representativa e fixa de 50.000 combinações possíveis da Lotofácil.
    """
    rng = random.Random(seed)
    # Total de combinações C(25, 15) = 3.268.760
    # Amostragem com reservoir sampling ou amostragem direta de 15 números
    sample = set()
    numbers = list(range(1, 26))
    while len(sample) < size:
        comb = tuple(sorted(rng.sample(numbers, 15)))
        sample.add(comb)
    return list(sample)

def evaluate_windows(windows, rule_defs, sample_pool=None, max_windows=None):
    """
    Avalia uma lista ou gerador de janelas para todas as regras fornecidas.
    Retorna métricas consolidadas por regra.
    """
    if sample_pool is None:
        sample_pool = generate_sample_pool()

    # Pre-calcula os atributos da amostra para agilizar a filtragem
    sample_attributes = {}
    for rule_key, rdef in rule_defs.items():
        if rule_key != "repetitions":
            extractor = rdef["extractor"]
            sample_attributes[rule_key] = [extractor({"dezenas": cand}) for cand in sample_pool]

    rule_stats = {
        k: {
            "total_tests": 0,
            "hits_interval": 0,       # O valor alvo esteve entre os top valores observados na janela
            "survival_count": 0,       # O valor alvo esteve dentro do conjunto de valores da janela
            "pool_reduction_sum": 0.0, # % médio de candidatos da amostra eliminados pelo filtro top
            "pool_tests": 0
        }
        for k in rule_defs.keys()
    }

    count = 0
    for train, target, prev_target, idx in windows:
        count += 1
        if max_windows and count > max_windows:
            break

        for rule_key, rdef in rule_defs.items():
            extractor = rdef["extractor"]

            # Valores na janela de treino
            train_vals = []
            for j in range(len(train)):
                c = train[j]
                prev_c = train[j - 1] if j > 0 else None
                v = extractor(c, prev_c)
                if v is not None:
                    train_vals.append(v)

            if not train_vals:
                continue

            target_val = extractor(target, prev_target)
            if target_val is None:
                continue

            stats = rule_stats[rule_key]
            stats["total_tests"] += 1

            counter = collections.Counter(train_vals)
            # Top-3 mais frequentes na janela
            top_3 = set([item[0] for item in counter.most_common(3)])
            # Todos os observados na janela (critério de sobrevivência do filtro)
            observed = set(counter.keys())

            is_hit = target_val in top_3
            is_survived = target_val in observed

            if is_hit:
                stats["hits_interval"] += 1
            if is_survived:
                stats["survival_count"] += 1

            # Redução de pool (calculada com os top_3 valores aceitos pela regra)
            if rdef["support_pool_reduction"]:
                if rule_key == "repetitions":
                    if prev_target:
                        prev_set = set(prev_target["dezenas"])
                        # Contar na amostra quantos tem interseção em top_3
                        # Para não ficar lento, podemos usar amostragem de 2000 combinações por janela
                        sub_sample = sample_pool[:2000]
                        kept = sum(1 for cand in sub_sample if len(prev_set.intersection(cand)) in top_3)
                        elimination_pct = ((len(sub_sample) - kept) / len(sub_sample)) * 100.0
                        stats["pool_reduction_sum"] += elimination_pct
                        stats["pool_tests"] += 1
                else:
                    sub_sample_attrs = sample_attributes[rule_key][:2000]
                    kept = sum(1 for val in sub_sample_attrs if val in top_3)
                    elimination_pct = ((len(sub_sample_attrs) - kept) / len(sub_sample_attrs)) * 100.0
                    stats["pool_reduction_sum"] += elimination_pct
                    stats["pool_tests"] += 1

    # Compilação dos resultados finais
    summary = {}
    for rule_key, s in rule_stats.items():
        total = s["total_tests"]
        if total == 0:
            continue
        hit_rate = (s["hits_interval"] / total) * 100.0
        survival_rate = (s["survival_count"] / total) * 100.0
        avg_reduction = (s["pool_reduction_sum"] / s["pool_tests"]) if s["pool_tests"] > 0 else 0.0

        # Score Composto:
        # 40% Sobrevivência + 35% Redução de Pool (filtragem útil) + 25% Hit Top-3
        # Penaliza se sobrevivência for muito baixa (filtro que elimina o certo é inútil)
        composite_score = (survival_rate * 0.40) + (avg_reduction * 0.35) + (hit_rate * 0.25)

        summary[rule_key] = {
            "name": rule_defs[rule_key]["name"],
            "total_tests": total,
            "hit_rate": round(hit_rate, 2),
            "survival_rate": round(survival_rate, 2),
            "avg_reduction": round(avg_reduction, 2),
            "composite_score": round(composite_score, 2)
        }

    return summary
