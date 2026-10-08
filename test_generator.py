"""
Testes unitários e de integração para o Módulo Gerador de Jogos da Lotofácil.
"""

import unittest
from engine.rules_evaluator import (
    PRIMES, FIBONACCI, MULTIPLES_OF_3, BORDER, CENTER,
    count_odds, count_evens, count_primes, count_border, count_center,
    count_fibonacci, count_multiples_of_3, calc_sum, count_cycle_numbers,
    eval_rows_distribution, eval_cols_distribution,
    eval_consecutives, eval_triple_jump, count_triple_jumps
)
from engine.candidate_generator import generate_candidate_pool
from engine.filter_pipeline import (
    FilterPipeline,
    build_historical_set,
    build_historical_14_set,
    is_historically_drawn,
    get_current_cycle_info,
    calc_rule_transitions,
    get_top_transitions
)


class TestRulesEvaluator(unittest.TestCase):
    def setUp(self):
        # Exemplo de jogo ordenado
        self.sample_comb = (1, 2, 3, 5, 8, 10, 11, 12, 13, 15, 17, 19, 21, 23, 25)

    def test_parity(self):
        # 1, 3, 5, 11, 13, 15, 17, 19, 21, 23, 25 = 11 ímpares
        # 2, 8, 10, 12 = 4 pares
        self.assertEqual(count_odds(self.sample_comb), 11)
        self.assertEqual(count_evens(self.sample_comb), 4)

    def test_primes(self):
        # 2, 3, 5, 11, 13, 17, 19, 23 = 8 primos
        self.assertEqual(count_primes(self.sample_comb), 8)

    def test_fibonacci(self):
        # 1, 2, 3, 5, 8, 13, 21 = 7 fibonacci
        self.assertEqual(count_fibonacci(self.sample_comb), 7)

    def test_multiples_of_3(self):
        # 3, 12, 15, 21 = 4 múltiplos de 3
        self.assertEqual(count_multiples_of_3(self.sample_comb), 4)

    def test_border_and_center(self):
        # Borda (16 posições) vs Centro (7, 8, 9, 12, 13, 14, 17, 18, 19)
        # Centro no sample: 8, 12, 13, 17, 19 (5 no centro, 10 na borda)
        self.assertEqual(count_center(self.sample_comb), 5)
        self.assertEqual(count_border(self.sample_comb), 10)

    def test_sum(self):
        self.assertEqual(calc_sum(self.sample_comb), sum(self.sample_comb))

    def test_consecutives_and_triple_jump(self):
        # 1, 2, 3 -> len 3
        # 10, 11, 12, 13 -> len 4
        # pairs: (1,2), (2,3), (10,11), (11,12), (12,13) = 5 pairs
        longest, pairs = eval_consecutives(self.sample_comb)
        self.assertEqual(longest, 4)
        self.assertEqual(pairs, 5)
        
        # Pulo triplo: entre 3 e 5 (gap 2), 5 e 8 (gap 3), 8 e 10 (gap 2), etc.
        # Não tem next - curr == 4
        self.assertFalse(eval_triple_jump(self.sample_comb))
        self.assertEqual(count_triple_jumps(self.sample_comb), 0)
        
        # Testando uma combinação com 1 pulo triplo (10 e 14 -> 14 - 10 = 4)
        comb_with_jump = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 16, 17, 18)
        self.assertTrue(eval_triple_jump(comb_with_jump))
        self.assertEqual(count_triple_jumps(comb_with_jump), 1)

        # Testando uma combinação com 2 pulos triplos (1->5 e 5->9)
        comb_with_2_jumps = (1, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21)
        self.assertTrue(eval_triple_jump(comb_with_2_jumps))
        self.assertEqual(count_triple_jumps(comb_with_2_jumps), 2)


class TestCandidateGenerator(unittest.TestCase):
    def setUp(self):
        self.prev = list(range(1, 16)) # 1 a 15

    def test_candidate_generation_counts(self):
        # 15 repetidas = 1
        pool_15 = generate_candidate_pool(self.prev, [15])
        self.assertEqual(len(pool_15), 1)
        self.assertEqual(pool_15[0], tuple(range(1, 16)))
        
        # 14 repetidas = C(15, 14) * C(10, 1) = 15 * 10 = 150
        pool_14 = generate_candidate_pool(self.prev, [14])
        self.assertEqual(len(pool_14), 150)

    def test_fixed_and_excluded_numbers(self):
        fixed = {1, 20} # 1 está no prev, 20 está no missing
        excluded = {2, 25} # 2 está no prev, 25 está no missing
        
        pool = generate_candidate_pool(
            self.prev,
            allowed_repetitions=[10],
            fixed_numbers=fixed,
            excluded_numbers=excluded
        )
        
        self.assertGreater(len(pool), 0)
        for comb in pool:
            # Fixas devem estar presentes
            self.assertIn(1, comb)
            self.assertIn(20, comb)
            # Excluídas não podem estar presentes
            self.assertNotIn(2, comb)
            self.assertNotIn(25, comb)
            # Repetições do prev devem ser exatamente 10
            rep = len(set(comb).intersection(set(self.prev)))
            self.assertEqual(rep, 10)


class TestFilterPipeline(unittest.TestCase):
    def test_pipeline_execution(self):
        prev = list(range(1, 16))
        pool = generate_candidate_pool(prev, [14]) # 150 candidatos
        pipeline = FilterPipeline(pool)
        
        # Filtra apenas soma > 140
        stat = pipeline.apply("sum_test", lambda c: calc_sum(c) > 140)
        self.assertEqual(stat["input_count"], 150)
        self.assertEqual(stat["remaining_count"], len(pipeline.candidates))
        self.assertEqual(stat["removed_count"], 150 - len(pipeline.candidates))
        self.assertEqual(len(pipeline.history), 1)

    def test_real_dataset_pipeline(self):
        import json
        with open("lotofacil_resultados.json", "r", encoding="utf-8") as f:
            contests = json.load(f)
        self.assertGreater(len(contests), 1000)
        last = contests[-1]['dezenas']
        
        # Gera pool com 9 repetidas
        avail_to_exclude = list(set(range(1, 26)) - {last[0]})
        pool = generate_candidate_pool(last, [9], fixed_numbers={last[0]}, excluded_numbers={avail_to_exclude[-1]})
        self.assertGreater(len(pool), 0)
        
        pipeline = FilterPipeline(pool)
        # Exclusão histórica (15 dezenas)
        hist_set = build_historical_set(contests)
        stat_hist = pipeline.apply("hist", lambda c: c not in hist_set)
        self.assertGreaterEqual(stat_hist["remaining_count"], 0)
        
        # Filtro de pares/ímpares
        stat_par = pipeline.apply("parity", lambda c: 6 <= count_odds(c) <= 9)
        self.assertGreater(stat_par["remaining_count"], 0)

    def test_historical_14_and_15_exclusion(self):
        # Cria conjunto fictício com 1 concurso
        sample_contest = [{'concurso': 1, 'dezenas': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]}]
        hist_15 = build_historical_set(sample_contest)
        hist_14 = build_historical_14_set(sample_contest)
        
        # Deve ter exatamente 15 combinações de 14 dezenas
        self.assertEqual(len(hist_14), 15)
        self.assertEqual(len(hist_15), 1)
        
        # Jogo com 15 acertos exatos -> rejeitado
        game_15 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
        self.assertTrue(is_historically_drawn(game_15, hist_14, hist_15))
        
        # Jogo com 14 acertos (troca 15 por 25) -> rejeitado
        game_14 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 25)
        self.assertTrue(is_historically_drawn(game_14, hist_14, hist_15))
        
        # Jogo com 13 acertos (troca 14 e 15 por 24 e 25) -> aceito
        game_13 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 24, 25)
        self.assertFalse(is_historically_drawn(game_13, hist_14, hist_15))
        
        # Teste com pipeline de filtros
        pipeline = FilterPipeline([game_15, game_14, game_13])
        stat = pipeline.apply("historical_14_15", lambda c: not is_historically_drawn(c, hist_14, hist_15))
        self.assertEqual(stat["input_count"], 3)
        self.assertEqual(stat["removed_count"], 2)
        self.assertEqual(stat["remaining_count"], 1)
        self.assertEqual(pipeline.candidates, [game_13])

    def test_consecutive_and_triple_jump_pipeline(self):
        # comb_a: 1-15 (seq 15, 0 pulos triplos)
        comb_a = tuple(range(1, 16))
        # comb_b: 1,2,3,4, 8,9,10,11, 15,16,17,18, 22,23,24 (seq 4, pulos triplos: 4->8 gap 3, 11->15 gap 3, 18->22 gap 3 -> 3 pulos)
        comb_b = (1, 2, 3, 4, 8, 9, 10, 11, 15, 16, 17, 18, 22, 23, 24)
        # comb_c: 1,2,3,4,5, 9,10,11,12, 16,17,18,19, 23,24 (seq 5, pulos triplos: 5->9 gap 3, 12->16 gap 3, 19->23 gap 3 -> 3 pulos)
        comb_c = (1, 2, 3, 4, 5, 9, 10, 11, 12, 16, 17, 18, 19, 23, 24)

        pipeline = FilterPipeline([comb_a, comb_b, comb_c])

        # Filtro de sequências consecutivas (máx 5 seguidas) -> elimina comb_a (seq 15), mantém comb_b (seq 4) e comb_c (seq 5)
        stat_seq = pipeline.apply("consecutives", lambda c: eval_consecutives(c)[0] <= 5)
        self.assertEqual(stat_seq["remaining_count"], 2)
        self.assertNotIn(comb_a, pipeline.candidates)
        self.assertIn(comb_b, pipeline.candidates)
        self.assertIn(comb_c, pipeline.candidates)

        # Filtro de pulo triplo (exatamente 3 pulos triplos) -> mantém ambos comb_b e comb_c
        stat_tj = pipeline.apply("triple_jump", lambda c: count_triple_jumps(c) == 3)
        self.assertEqual(stat_tj["remaining_count"], 2)

        # Agora se exigirmos seq <= 4:
        pipeline2 = FilterPipeline([comb_b, comb_c])
        stat_seq2 = pipeline2.apply("consecutives", lambda c: eval_consecutives(c)[0] <= 4)
        self.assertEqual(stat_seq2["remaining_count"], 1)
        self.assertEqual(pipeline2.candidates, [comb_b])

    def test_group_distribution_repetition_stats(self):
        import json
        from engine.stats import calc_group_distribution_repetition
        with open("lotofacil_resultados.json", "r", encoding="utf-8") as f:
            contests = json.load(f)
        
        res = calc_group_distribution_repetition(contests)
        self.assertIsNotNone(res)
        self.assertEqual(res["total_transitions"], len(contests) - 1)
        self.assertEqual(len(res["matching_groups"]), 6)
        self.assertEqual(len(res["group_individuals"]), 5)
        # 4 grupos repetidos deve ser 0
        self.assertEqual(res["matching_groups"][4][1], 0)

    def test_consecutive_draws_stats(self):
        import json
        from engine.stats import calc_consecutive_draws
        with open("lotofacil_resultados.json", "r", encoding="utf-8") as f:
            contests = json.load(f)

        res = calc_consecutive_draws(contests)
        self.assertIsNotNone(res)
        self.assertEqual(res["total_contests"], len(contests))
        self.assertEqual(len(res["ranking"]), 25)
        self.assertEqual(len(res["results_by_number"]), 25)

        # Dezena 7 tem o recorde com 25 concursos consecutivos (2866 ao 2890)
        rec = res["overall_record"]
        self.assertEqual(rec["number"], 7)
        self.assertEqual(rec["max_streak"], 25)
        self.assertIn((2866, 2890), rec["max_occurrences"])

        # Dezena 25 tem a 2ª maior sequência com 21 concursos (3183 ao 3203)
        num_25 = res["results_by_number"][25]
        self.assertEqual(num_25["max_streak"], 21)
        self.assertIn((3183, 3203), num_25["max_occurrences"])

        # Dezena 3 tem max_streak de 18 concursos (852 ao 869)
        num_3 = res["results_by_number"][3]
        self.assertEqual(num_3["max_streak"], 18)
        self.assertIn((852, 869), num_3["max_occurrences"])

        # Teste sintético com sequência ativa até o final e empates
        mock_contests = [
            {"concurso": 1, "dezenas": [1, 2]},
            {"concurso": 2, "dezenas": [1, 2]},
            {"concurso": 3, "dezenas": [2, 3]},
            {"concurso": 4, "dezenas": [1, 3]},
            {"concurso": 5, "dezenas": [1, 3]},
        ]
        mock_res = calc_consecutive_draws(mock_contests)
        # Dezena 1: concurso 1-2 (len 2), concurso 4-5 (len 2) -> max_streak = 2, 2 ocorrências, current_streak = 2
        d1 = mock_res["results_by_number"][1]
        self.assertEqual(d1["max_streak"], 2)
        self.assertEqual(d1["max_occurrences"], [(1, 2), (4, 5)])
        self.assertEqual(d1["current_streak"], 2)

        # Dezena 2: concurso 1-3 (len 3) -> max_streak = 3, current_streak = 0
        d2 = mock_res["results_by_number"][2]
        self.assertEqual(d2["max_streak"], 3)
        self.assertEqual(d2["max_occurrences"], [(1, 3)])
        self.assertEqual(d2["current_streak"], 0)


from ui.generator_view import (
    parse_filter_choice,
    parse_repetition_choice,
    parse_single_int_choice,
    parse_boolean_choice,
    parse_sequence_choice,
    parse_triple_jump_choice
)


class TestFilterChoiceParsing(unittest.TestCase):
    def test_parse_filter_choice_disabled(self):
        self.assertIsNone(parse_filter_choice("N", 3, 5))
        self.assertIsNone(parse_filter_choice("n", 3, 5))
        self.assertIsNone(parse_filter_choice("nao", 3, 5))
        self.assertIsNone(parse_filter_choice("não", 3, 5))
        self.assertIsNone(parse_filter_choice("no", 3, 5))

    def test_parse_filter_choice_default(self):
        self.assertEqual(parse_filter_choice("P", 3, 5), (3, 5))
        self.assertEqual(parse_filter_choice("p", 3, 5), (3, 5))
        self.assertEqual(parse_filter_choice("", 3, 5), (3, 5))
        self.assertEqual(parse_filter_choice("  ", 3, 5), (3, 5))
        self.assertEqual(parse_filter_choice("padrao", 3, 5), (3, 5))
        self.assertEqual(parse_filter_choice("padrão", 3, 5), (3, 5))

    def test_parse_filter_choice_custom_range(self):
        self.assertEqual(parse_filter_choice("4-6", 3, 5), (4, 6))
        self.assertEqual(parse_filter_choice("4..6", 3, 5), (4, 6))
        self.assertEqual(parse_filter_choice("4, 6", 3, 5), (4, 6))
        self.assertEqual(parse_filter_choice("4", 3, 5), (4, 4))

    def test_parse_repetition_choice(self):
        # N deve permitir todas as 5 a 15 repetidas
        self.assertEqual(parse_repetition_choice("N", [8, 9, 10]), list(range(5, 16)))
        self.assertEqual(parse_repetition_choice("n", [8, 9, 10]), list(range(5, 16)))
        # P ou vazio deve usar padrão
        self.assertEqual(parse_repetition_choice("P", [8, 9, 10]), [8, 9, 10])
        self.assertEqual(parse_repetition_choice("", [8, 9, 10]), [8, 9, 10])
        # Customizado
        self.assertEqual(parse_repetition_choice("9-11", [8, 9, 10]), [9, 10, 11])
        self.assertEqual(parse_repetition_choice("9", [8, 9, 10]), [9])

    def test_parse_single_int_choice(self):
        self.assertIsNone(parse_single_int_choice("N", 5))
        self.assertIsNone(parse_single_int_choice("n", 5))
        self.assertEqual(parse_single_int_choice("P", 5), 5)
        self.assertEqual(parse_single_int_choice("", 5), 5)
        self.assertEqual(parse_single_int_choice("4", 5), 4)
        self.assertEqual(parse_single_int_choice("1-4", 5), 4)

    def test_parse_sequence_choice(self):
        # Desativado
        self.assertIsNone(parse_sequence_choice("N"))
        self.assertIsNone(parse_sequence_choice("nao"))
        self.assertIsNone(parse_sequence_choice("não"))
        # Padrão
        self.assertEqual(parse_sequence_choice("P", 5), (1, 5))
        self.assertEqual(parse_sequence_choice("", 5), (1, 5))
        # Número único (máximo)
        self.assertEqual(parse_sequence_choice("4", 5), (1, 4))
        # Intervalo
        self.assertEqual(parse_sequence_choice("3-5", 5), (3, 5))
        self.assertEqual(parse_sequence_choice("3..5", 5), (3, 5))

    def test_parse_triple_jump_choice(self):
        # Desativado / qualquer quantidade
        self.assertIsNone(parse_triple_jump_choice("N"))
        self.assertIsNone(parse_triple_jump_choice("nao"))
        self.assertIsNone(parse_triple_jump_choice("não"))
        self.assertIsNone(parse_triple_jump_choice("todos"))
        # Padrão: 0 a 1 pulo
        self.assertEqual(parse_triple_jump_choice("P"), (0, 1))
        self.assertEqual(parse_triple_jump_choice(""), (0, 1))
        # Sem pulo triplo (0)
        self.assertEqual(parse_triple_jump_choice("0"), (0, 0))
        self.assertEqual(parse_triple_jump_choice("sem"), (0, 0))
        self.assertEqual(parse_triple_jump_choice("nenhum"), (0, 0))
        # Exatamente 1 pulo triplo
        self.assertEqual(parse_triple_jump_choice("1"), (1, 1))
        # Com pulo triplo (>= 1)
        self.assertEqual(parse_triple_jump_choice("S"), (1, 3))
        self.assertEqual(parse_triple_jump_choice("sim"), (1, 3))
        self.assertEqual(parse_triple_jump_choice("com"), (1, 3))
        self.assertEqual(parse_triple_jump_choice(">=1"), (1, 3))
        # Intervalos customizados
        self.assertEqual(parse_triple_jump_choice("0-2"), (0, 2))
        self.assertEqual(parse_triple_jump_choice("1-2"), (1, 2))

    def test_parse_boolean_choice(self):
        self.assertFalse(parse_boolean_choice("N", True))
        self.assertFalse(parse_boolean_choice("n", True))
        self.assertTrue(parse_boolean_choice("P", True))
        self.assertTrue(parse_boolean_choice("p", True))
        self.assertTrue(parse_boolean_choice("S", True))
        self.assertTrue(parse_boolean_choice("s", True))
        self.assertTrue(parse_boolean_choice("", True))


if __name__ == "__main__":
    unittest.main()

