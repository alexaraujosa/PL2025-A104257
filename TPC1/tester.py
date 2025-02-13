import unittest
from io import StringIO
from unittest.mock import patch
from somador import somador

class TestSomador(unittest.TestCase):

    def run_test_somador(self, input_text, expected_output):
        with patch('sys.stdout', new = StringIO()) as out:
            somador(input_text)
            self.assertEqual(out.getvalue().strip(), expected_output)

    def test_somador_sem_alteracao(self):
        self.run_test_somador("182 19230 =", "19412")
        
    def test_somador_intercalado(self):
        self.run_test_somador("1821 oFf 19230 oN 1=", "1822")
    
    def test_somador_desligado(self):
        self.run_test_somador("Off 12 123 123=", "0")

    def test_somador_newlines_intercalado(self):
        self.run_test_somador("Off = 12=On=asd12mkas\nadji12m\n\n\naas9id=ONasd12d==", "0\n0\n0\n33\n45\n45")
    
    def test_somador_aula(self):
        self.run_test_somador("opwaodsok45okaSknwIskndPOAWKs\noiwJAkjsndkasdj2025-02-07lkawmSDPMwkmoAnjsd\n=OIJWklamsdknwaOFfiawodam,awkmasd.\nawdisad789wands43akjwdasd\njawndkasndonoiijwdasd2auindiasnd\nAWOIJasjdnAW5jiawdasd=", "2079\n2086")
    
if __name__ == "__main__":
    unittest.main()