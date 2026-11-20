# Roteiro do vídeo de Governança (6 a 7 min)

O enunciado pede: mostrar a **integração de todos os módulos**, de 5 a 7 minutos, **sem leitura massiva de
documento**. Mostre o sistema funcionando e fale com suas palavras. Os relatórios aparecem só de relance.

## Antes de gravar

1. Suba o sistema: `docker compose up`, ou a API (`uvicorn api.main:app --port 8000`, dentro de `01-front-end`)
   e a interface (`streamlit run web/app.py`).
2. Faça uma pergunta de teste antes de gravar, porque a primeira busca do RAG demora.
3. Deixe abertos em abas ou janelas: a interface (http://localhost:8501), um terminal em `06-rpa/codigo`, as
   capturas do iSPD (`07-cluster/evidencias/cenario_a_resumo.png` e `cenario_b_resumo.png`), o PDF de Quântica e
   o PDF de Governança.
4. Tenha à mão o celular com o OuviAí do Edge Impulse. Se não der, use o simulador da página Avisos da casa.
5. Grave a tela em 1080p, com o microfone perto e o celular no silencioso.

## Roteiro

| Tempo | O que mostrar | O que falar (resumo, com suas palavras) |
|---|---|---|
| 0:00–0:30 | Tela inicial do EloBairro | Quem somos (nomes). O problema: idosos, pessoas com baixa escolaridade ou com deficiência têm dificuldade com os canais da prefeitura. ODS 10 e 16. |
| 0:30–1:00 | Figura 1 do relatório (arquitetura), por 10 s | Um único sistema: a interface e a API (01) chamam todos os outros módulos. Cada disciplina é uma peça do mesmo fluxo. |
| 1:00–1:45 | **Tirar uma dúvida**: pergunta escrita ("documentos para o Cadastro Único") e depois a aba de voz | A resposta vem do RAG (03), com fonte oficial de São José dos Campos. Pela voz, quem transcreve e fala é o módulo de PLN (02). Se não houver informação, ele diz que não sabe. |
| 1:45–2:50 | **Relatar um problema**: texto com telefone ("buraco na rua X, me liga 12 99999-0000") + foto de rachadura | A foto passou pela visão computacional (04), com o aviso de que é triagem. O telefone sumiu do texto: é a máscara do robô de RPA (06). A IA só propõe categoria e urgência; o cidadão confere, marca e confirma. Mostrar o número do protocolo. |
| 2:50–3:30 | Terminal em `06-rpa/codigo`: `python main.py` | O robô processa os relatos do dia, remove duplicados e grava no mesmo banco de protocolos da API. |
| 3:30–4:10 | Perfil **Gestor**: painel, filtros, mapa, botão "Importar do robô RPA", fila de revisão | O gestor vê os protocolos do app e do robô juntos. Casos incertos vão para revisão humana; quem muda o status é a pessoa. |
| 4:10–4:40 | **Avisos da casa** com o celular tocando uma campainha (ou o simulador) | O OuviAí (05) reconhece a campainha no celular e o aviso aparece aqui. Nenhum áudio sai do celular, só a classe do som. |
| 4:40–5:20 | Capturas do iSPD lado a lado (cenário A e B) | Cluster (07): em dia de chuva chegam muitas fotos. Com 2 workers, 1.021 s; com 4, 511 s. Redução de 49,99%. É assim que o módulo de visão seria executado em pico. |
| 5:20–5:50 | PDF de Quântica, só o roteiro (seção 4) | Quântica (08): o gargalo do crescimento é despachar as equipes para os protocolos. Hoje se resolve com otimização clássica; a quântica só entra se provar ganho. A criptografia pós-quântica protege o banco e a API. |
| 5:50–6:30 | PDF de Governança, Quadro 1 e Quadro 2, por poucos segundos | Governança: todas as disciplinas ligadas; dados pessoais mascarados e nada de áudio ou foto guardados (LGPD); a pessoa sempre decide. O que falta: teste com dados reais da prefeitura. |
| 6:30–6:50 | Volta à tela inicial | Fechamento: o que aprendemos (fazer os módulos conversarem foi o mais difícil) e o link do repositório. |

## Dicas

- Não leia os slides nem o PDF. Os documentos aparecem só para mostrar que existem.
- Se algo falhar ao vivo, mostre o erro tratado. A mensagem de "sistema fora do ar" também é uma evidência.
- Depois de publicar como **não listado**, mande o link para entrar na seção 11 do relatório e no README da pasta 09.
