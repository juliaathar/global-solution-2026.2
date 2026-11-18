# 05 IoT e Embedded AI: OuviAí

O celular reconhece **campainha** e **batida na porta** e o EloBairro mostra um aviso grande na tela para quem
não ouve. O modelo (MFE + CNN) é treinado no Edge Impulse e roda no aparelho; só a classe do som sai dele.

**Dados:** gravações públicas, sem gravação própria: campainhas do Visualfy (Zenodo, CC BY 4.0), batidas e sons
domésticos do ESC-50 (CC BY-NC 3.0) e sons indesejados do Visualfy. Montados por `codigo/montar_dataset_publico.py`.
Detalhes e créditos no relatório, seção 3, e em `dados_audio/creditos_sons.csv`.

**Integrantes:**

| Nome completo | RM |
|---|---|
| Bruno Fernandes Nascimento | 552574 |
| Edgar Lódula de Assis | 565260 |
| Júlia Aben-Athar | 566325 |

- Relatório (com capa): [relatorio/relatorio_ouviai.md](relatorio/relatorio_ouviai.md)
- Passo a passo no Edge Impulse: [GUIA_EDGE_IMPULSE.md](GUIA_EDGE_IMPULSE.md)

## Integração com o EloBairro

```
celular (Edge Impulse) ─► ponte_alertas.py ─► POST /iot/eventos ─► API (01-front-end) ─► página "Avisos da casa"
                          só {classe, confianca}                    ignora ambiente,          e gráfico no painel
                                                                    < 80% e repetição
```

Para testar sem celular: na interface, **Avisos da casa > Testar sem o celular**, ou `python codigo/ponte_alertas.py --simular`.

## Código

| Script | Para quê |
|---|---|
| `codigo/montar_dataset_publico.py` | monta os 60 clipes (ESC-50 + Visualfy) e os 15 sons do teste ao vivo |
| `codigo/preparar_audios.py` | converte as gravações para 16 kHz, mono, PCM16, 5 s e sorteia 15 Training e 5 Test por classe, sem reuso |
| `codigo/verificar_dataset.py` | confere cada WAV e gera `evidencias/verificacao_dataset.md` |
| `codigo/enviar_edge_impulse.py` | envia ao Edge Impulse pela Ingestion API (chave só em `EI_API_KEY`) |
| `codigo/avaliar.py` | acerto, matriz de confusão e falsos positivos do Model testing e das 15 tentativas ao vivo |
| `codigo/ponte_alertas.py` | roda o modelo `.eim` no microfone e avisa a API (ou `--simular`) |
| `codigo/gravar_no_pc.py` | opcional: grava os clipes de 5 s pelo microfone do computador |

As gravações brutas (`dados_audio/brutos/`) não vão para o Git. Os arquivos prontos ficam em `dados_audio/preparados/`.

## Checklist


- [x] 3 classes: campainha, batida na porta, ambiente
- [x] Edge Impulse: 20 gravações de 5 s por classe (15 Training, 5 Test), sons públicos do ESC-50 e Visualfy
- [x] 16 kHz, mono, PCM16; rótulos conferidos (`verificar_dataset.py`)
- [x] Impulse: bloco Audio (MFE) + CNN; parâmetros, validação (87,7%), matriz de confusão
- [x] Model testing (Classify all) nos 5 arquivos de Test por classe, sem reuso no Training (80% por arquivo, 64,4% por janela)
- [x] Run this model: QR code, microfone, celular (prints em `evidencias/ei_06` e `ei_07`)
- [x] 15 tentativas ao vivo (5 por classe): som, classe prevista, acerto/erro, % de acertos: **12 de 15 (80%)**
- [x] Falsos positivos na classe ambiente (passos virou campainha) e limitações
- [x] Capturas: Data acquisition, Impulse design, Generate features, Classifier, Model testing (`evidencias/ei_0*.jpg`)
- [x] Explicar evolução para notificações e vibração (relatório, seção 9; a API já devolve o padrão de vibração)
- [x] Problema, público, ODS, privacidade (sem gravar conversas) (relatório, seções 1 e 10)
- [x] Capa com título, nomes e RMs (relatório)
