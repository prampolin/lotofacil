"""
Testes automatizados para o sistema de backtesting.
"""

import unittest
from backtesting.extractors import (
    extract_parity, extract_sum_range, extract_primes,
    extract_fibonacci, extract_multiples_of_3, extract_border,
    extract_center, extract_row_distribution, extract_repetitions,
    RULE_DEFINITIONS
)
from backtesting.window_engine import generate_sliding_windows, generate_fixed_blocks
from backtesting.score_engine import generate_sample_pool, evaluate_windows

class TestBacktestingSuite(unittest.TestCase):
    def setUp(self):
        self.mock_contests = [
            {"concurso": i, "dezenas": list(range(1, 16))} for i in range(1, 25)
        ]

    def test_extractors(self):
        dezenas = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        # Odds: 1, 3, 5, 7, 9, 11, 13, 15 = 8 ímpares, 7 pares
        self.assertEqual(extract_parity(dezenas), "8I-7P")
        self.assertEqual(extract_primes(dezenas), 6) # 2, 3, 5, 7, 11, 13
        self.assertEqual(extract_fibonacci(dezenas), 6) # 1, 2, 3, 5, 8, 13
        self.assertEqual(extract_repetitions(dezenas, dezenas), 15)

    def test_window_generation(self):
        w10 = list(generate_sliding_windows(self.mock_contests, window_size=10))
        # 24 concursos, window 10 => alvos de índice 10 a 23 = 14 janelas
        self.assertEqual(len(w10), 14)

        b10 = list(generate_fixed_blocks(self.mock_contests, block_size=10))
        # 24 concursos => alvos nos índices 10 e 20 = 2 blocos
        self.assertEqual(len(b10), 2)

    def test_sample_pool_and_evaluate(self):
        pool = generate_sample_pool(size=100)
        self.assertEqual(len(pool), 100)
        w = list(generate_sliding_windows(self.mock_contests, window_size=5))
        # Testa apenas com a regra de paridade para ser instantâneo
        defs = {"parity": RULE_DEFINITIONS["parity"]}
        res = evaluate_windows(w, defs, sample_pool=pool, max_windows=5)
        self.assertIn("parity", res)
        self.assertGreater(res["parity"]["total_tests"], 0)

if __name__ == "__main__":
    unittest.main()
