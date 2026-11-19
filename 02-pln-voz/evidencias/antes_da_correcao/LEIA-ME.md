# Antes da correção da regra de continuação

Resultado do `qwen2.5:3b` sobre a base real (RAG do 03), **antes** de corrigir a regra de continuação do assistente. Nesta versão, a continuação "E onde eu faço isso?" (q02) não era reconhecida e caía na guarda de "não sei".

- `acerto_manual` e `obs_manual` são uma **revisão assistida por IA**, feita lendo cada resposta contra o texto da página de origem (`03-generative-ai/corpus/documentos.jsonl`). Uma pessoa do grupo deve conferir uma amostra antes de ela valer como revisão humana.
- A correção automática (palavras-chave) deu 82,6%; a revisão deu 73,9%, porque a automática aceitou 3 respostas erradas (q10, q20 e q22).
- Latência medida em um GitHub Codespace (AMD EPYC 7763, 2 vCPUs, sem GPU), com a primeira chamada incluindo o carregamento do modelo.
