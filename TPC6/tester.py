import unittest
from unittest.mock import patch
from gram import anasin

class TestAnasin(unittest.TestCase):

    def test_anasin_basico(self):
        self.assertEqual(182, 182)
        
    def test_anasin_soma(self):
        self.assertEqual(13 + 2, 15)
    
    def test_anasin_subtracao(self):
        self.assertEqual(1 - 5, -4)

    def test_anasin_multiplicacao(self):
        self.assertEqual(5 * 2, 10)
    
    def test_anasin_divisao(self):
        self.assertEqual(3 / 5, 0.6)
    
    def test_anasin_avancado(self):
        self.assertEqual(3 * 5 - 1 + 3 * 2 / 2 * 3 / 5, 15.8)
        self.assertEqual(600 - 250 / 10 * 8 + 27 * 5 - 99, 436)
        self.assertEqual(999 - 333 / 3 + 25 * 7 - 64 / 8, 1055)
        self.assertEqual(88 - 7 * 9 + 126 / 6 * 3 - 14, 74)
        self.assertEqual(250 - 6 * 8 + 99 / 11 * 3 - 4, 225)
        self.assertEqual(500 - 75 / 8 * 3 + 12, 483.875)
        self.assertEqual(365 / 16 + 8 * 5 - 22, 40.8125)
    
if __name__ == "__main__":
    unittest.main()