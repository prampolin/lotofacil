"""
Orquestrador de execução em etapas do Backtesting Autônomo da Lotofácil.
Controla o tempo de execução, gera checkpoints no cache e evita sobrecarga da máquina.
"""

import os
import sys
import json
import time

from backtesting.extractors import RULE_DEFINITIONS
from backtesting.window_engine import generate_sliding_windows, generate_fixed_blocks
from backtesting.score_engine import evaluate_windows, generate_sample_pool
from backtesting.temporal_engine import analyze_transitions, analyze_autocorrelation, analyze_eras
from backtesting.report_builder import generate_html_report

DATA_FILE = "lotofacil_resultados.json"
CACHE_DIR = "backtesting/cache"

def load_contests():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Erro: Arquivo {DATA_FILE} não encontrado.")
        sys.exit(1)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return sorted(data, key=lambda c: c['concurso'])

def save_checkpoint(name, data):
    path = os.path.join(CACHE_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_checkpoint(name):
    path = os.path.join(CACHE_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def run_backtest(clean_cache=False):
    os.makedirs(CACHE_DIR, exist_ok=True)
    contests = load_contests()
    total_contests = len(contests)

    print("=========================================================")
    print("       🚀 LOTOFÁCIL - SISTEMA DE BACKTESTING AUTÔNOMO    ")
    print("=========================================================")
    print(f"Total de concursos carregados: {total_contests}")
    print(f"Número de regras a testar: {len(RULE_DEFINITIONS)}")
    print("---------------------------------------------------------")

    if clean_cache:
        print("🧹 Limpando cache anterior...")
        for f in os.listdir(CACHE_DIR):
            if f.endswith(".json"):
                os.remove(os.path.join(CACHE_DIR, f))

    # Pré-geração da amostra única fixa para testes de pool
    sample_pool = generate_sample_pool()

    # ETAPA 1: Avaliação Janelas Deslizantes (10 e 50 concursos)
    print("\n▶ [Etapa 1/4] Testando Janelas Deslizantes (10 e 50)...")
    sliding_results = load_checkpoint("etapa_1_sliding")
    if not sliding_results:
        t0 = time.time()
        print("  - Processando Janela Deslizante 10...")
        w10 = list(generate_sliding_windows(contests, window_size=10))
        # Para evitar aquecimento sem perder representatividade, avalia passo amostrado
        step = 1 if len(w10) <= 1500 else 2
        w10_sampled = w10[::step]
        res10 = evaluate_windows(w10_sampled, RULE_DEFINITIONS, sample_pool)

        print("  - Processando Janela Deslizante 50...")
        w50 = list(generate_sliding_windows(contests, window_size=50))
        w50_sampled = w50[::step]
        res50 = evaluate_windows(w50_sampled, RULE_DEFINITIONS, sample_pool)

        sliding_results = {
            "sliding10": res10,
            "sliding50": res50
        }
        save_checkpoint("etapa_1_sliding", sliding_results)
        print(f"  ✅ Etapa 1 concluída em {round(time.time() - t0, 1)}s. Checkpoint salvo.")
    else:
        print("  ⚡ Carregado do checkpoint.")

    time.sleep(2) # Pausa térmica suave

    # ETAPA 2: Avaliação Blocos Fixos (10 em 10 e 50 em 50)
    print("\n▶ [Etapa 2/4] Testando Blocos Fixos (10 em 10 e 50 em 50)...")
    fixed_results = load_checkpoint("etapa_2_fixed")
    if not fixed_results:
        t0 = time.time()
        print("  - Processando Blocos de 10 em 10 (concurso 11, 21, 31...)...")
        b10 = list(generate_fixed_blocks(contests, block_size=10))
        res_b10 = evaluate_windows(b10, RULE_DEFINITIONS, sample_pool)

        print("  - Processando Blocos de 50 em 50 (concurso 51, 101, 151...)...")
        b50 = list(generate_fixed_blocks(contests, block_size=50))
        res_b50 = evaluate_windows(b50, RULE_DEFINITIONS, sample_pool)

        fixed_results = {
            "fixed10": res_b10,
            "fixed50": res_b50
        }
        save_checkpoint("etapa_2_fixed", fixed_results)
        print(f"  ✅ Etapa 2 concluída em {round(time.time() - t0, 1)}s. Checkpoint salvo.")
    else:
        print("  ⚡ Carregado do checkpoint.")

    time.sleep(2)

    # ETAPA 3: Análise Temporal (Transições, Autocorrelação e Eras)
    print("\n▶ [Etapa 3/4] Calculando Análises Temporais e Eras...")
    temporal_results = load_checkpoint("etapa_3_temporal")
    if not temporal_results:
        t0 = time.time()
        print("  - Calculando Matrizes de Transição de Estado...")
        transitions = analyze_transitions(contests, RULE_DEFINITIONS)

        print("  - Calculando Autocorrelação Temporal...")
        autocorr = analyze_autocorrelation(contests, RULE_DEFINITIONS)

        print("  - Comparando Eras Históricas...")
        eras = analyze_eras(contests, RULE_DEFINITIONS)

        temporal_results = {
            "transitions": transitions,
            "autocorrelation": autocorr,
            "eras": eras
        }
        save_checkpoint("etapa_3_temporal", temporal_results)
        print(f"  ✅ Etapa 3 concluída em {round(time.time() - t0, 1)}s. Checkpoint salvo.")
    else:
        print("  ⚡ Carregado do checkpoint.")

    # ETAPA 4: Consolidação do Ranking Geral e Geração do HTML
    print("\n▶ [Etapa 4/4] Consolidando Ranking e Gerando Relatório HTML...")
    # Consolida a média do Score Composto ponderando Janela Deslizante 50 e 10
    consolidated_ranking = {}
    r10 = sliding_results["sliding10"]
    r50 = sliding_results["sliding50"]

    for rule_key, rdef in RULE_DEFINITIONS.items():
        score10 = r10.get(rule_key, {})
        score50 = r50.get(rule_key, {})

        comp10 = score10.get("composite_score", 0)
        comp50 = score50.get("composite_score", 0)
        final_composite = round((comp50 * 0.6) + (comp10 * 0.4), 2)

        surv10 = score10.get("survival_rate", 0)
        surv50 = score50.get("survival_rate", 0)
        final_survival = round((surv50 * 0.6) + (surv10 * 0.4), 2)

        red10 = score10.get("avg_reduction", 0)
        red50 = score50.get("avg_reduction", 0)
        final_reduction = round((red50 * 0.6) + (red10 * 0.4), 2)

        hit10 = score10.get("hit_rate", 0)
        hit50 = score50.get("hit_rate", 0)
        final_hit = round((hit50 * 0.6) + (hit10 * 0.4), 2)

        consolidated_ranking[rule_key] = {
            "name": rdef["name"],
            "composite_score": final_composite,
            "survival_rate": final_survival,
            "avg_reduction": final_reduction,
            "hit_rate": final_hit
        }

    final_payload = {
        "ranking": consolidated_ranking,
        "windows": {
            "sliding10": sliding_results["sliding10"],
            "sliding50": sliding_results["sliding50"],
            "fixed10": fixed_results["fixed10"],
            "fixed50": fixed_results["fixed50"]
        },
        "transitions": temporal_results["transitions"],
        "autocorrelation": temporal_results["autocorrelation"],
        "eras": temporal_results["eras"]
    }

    report_path = generate_html_report(final_payload, "relatorio_backtesting.html")
    print(f"\n🎉 SUCESSO! Relatório HTML gerado em: {os.path.abspath(report_path)}")
    print("Abra 'relatorio_backtesting.html' em qualquer navegador para visualizar o painel completo interativo.")

if __name__ == "__main__":
    clean = "--clean" in sys.argv
    run_backtest(clean_cache=clean)
