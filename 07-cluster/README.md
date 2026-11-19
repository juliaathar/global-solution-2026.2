# 07 Cluster Computing (iSPD)

Projeto **EloBairro**: simulação no iSPD da classificação de fotos em lote com 2 e 4 workers.

**Ligação com as outras disciplinas:** a tarefa simulada é o classificador de fissuras da `04-visao-computacional` (MobileNetV2), que no app recebe as fotos dos relatos do cidadão antes de virarem protocolo no robô da `06-rpa`. A carga simulada (2000 MFLOPS por foto) é uma hipótese conservadora, cerca de 3 vezes o custo do modelo (cerca de 600 MFLOPS, 60 ms por imagem medidos na 04). A comparação e o efeito sobre o gargalo do mestre estão em [`cenarios_ispd/parametros.md`](cenarios_ispd/parametros.md#comparação-com-a-medição-da-04-visao-computacional).

**Integrantes:**

| Nome completo | RM |
|---|---|
| Bruno Fernandes Nascimento | 552574 |
| Edgar Lódula de Assis | 565260 |
| Júlia Aben-Athar | 566325 |

## Entregas
- Relatório (4 páginas): [`relatorio/relatorio_cluster.pdf`](relatorio/relatorio_cluster.pdf). A fonte é `relatorio/relatorio_cluster.html`; para regerar o PDF: `pip install weasyprint` e `python relatorio/gerar_pdf.py`.
- Modelos do iSPD, parâmetros e resultados: `cenarios_ispd/` (`parametros.md`, `resultados.md`, `.imsx`).
- Capturas das simulações: `evidencias/`.

## Checklist
- [x] Tarefa repetida do sistema justificada (ex.: classificar imagens em lote)
- [x] Número de tarefas, tamanho computacional e comunicação declarados (valores estimados permitidos)
- [x] Cenário 1: 2 workers. Cenário 2: 4 workers
- [x] Mesma carga, capacidade, escalonador, banda e latência nos dois
- [x] Total Simulated Time (s) e uso dos workers (aba Resources)
- [x] Tabela comparativa com unidades e capturas legíveis
- [x] Redução percentual e razão T2/T4
- [x] Discussão de ganho (ou falta), gargalos e limites
- [x] Arquivos do iSPD ou capturas suficientes para reproduzir
