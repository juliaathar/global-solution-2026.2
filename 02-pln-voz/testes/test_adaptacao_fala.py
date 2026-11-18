import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from adaptacao_fala import adaptar_para_fala, numero_por_extenso  # noqa: E402


class TestExtenso(unittest.TestCase):
    def test_numeros(self):
        casos = {0: "zero", 7: "sete", 21: "vinte e um", 100: "cem", 101: "cento e um",
                 250: "duzentos e cinquenta", 1000: "mil", 1500: "mil e quinhentos",
                 1234: "mil duzentos e trinta e quatro", 2026: "dois mil e vinte e seis",
                 1_000_000: "um milhão", 2_500_000: "dois milhões e quinhentos mil"}
        for n, esperado in casos.items():
            self.assertEqual(numero_por_extenso(n), esperado, n)

    def test_feminino(self):
        self.assertEqual(numero_por_extenso(2, feminino=True), "duas")
        self.assertEqual(numero_por_extenso(21, feminino=True), "vinte e uma")


class TestAdaptacao(unittest.TestCase):
    def test_siglas(self):
        self.assertEqual(adaptar_para_fala("Vá à UBS."), "Vá à U B S.")
        self.assertIn("crás", adaptar_para_fala("Procure o CRAS."))

    def test_moeda(self):
        self.assertEqual(adaptar_para_fala("Custa R$ 50."), "Custa cinquenta reais.")
        self.assertEqual(adaptar_para_fala("R$ 1,50"), "um real e cinquenta centavos")

    def test_data(self):
        self.assertEqual(adaptar_para_fala("Dia 15/03/2026"), "Dia quinze de março de dois mil e vinte e seis")
        self.assertEqual(adaptar_para_fala("01/05"), "primeiro de maio")

    def test_hora(self):
        self.assertEqual(adaptar_para_fala("das 7h às 17h30"),
                         "das sete horas às dezessete horas e trinta minutos")
        self.assertEqual(adaptar_para_fala("às 2h"), "às duas horas")

    def test_telefone_emergencia(self):
        self.assertEqual(adaptar_para_fala("Ligue 192"), "Ligue um nove dois")

    def test_porcentagem_e_decimal(self):
        self.assertEqual(adaptar_para_fala("10%"), "dez por cento")
        self.assertEqual(adaptar_para_fala("1,5 km"), "um vírgula cinco km")

    def test_markdown_e_emoji(self):
        out = adaptar_para_fala("## Título\n- **Leve** o RG 😀\n- [site](http://x.com)")
        for proibido in ("#", "*", "-", "😀", "http", "["):
            self.assertNotIn(proibido, out)
        self.assertIn("Leve o R G", out)

    def test_frase_longa_e_quebrada(self):
        longa = ("Para tirar a segunda via do documento você precisa ir ao posto de identificação mais próximo, "
                 "levando a certidão de nascimento e também o comprovante de residência atualizado.")
        self.assertGreaterEqual(adaptar_para_fala(longa).count("."), 2)


if __name__ == "__main__":
    unittest.main()
