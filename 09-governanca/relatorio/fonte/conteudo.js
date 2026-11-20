// Conteúdo do relatório de Governança (EloBairro, GS 2026.2)
// Blocos: ["h1"], ["h2"], ["p"], ["fig", arq, w, h, título, fonte], ["tab", "Tabela"|"Quadro", título, cab, linhas, larguras, fonte]

module.exports = [
["h1", "INTRODUÇÃO"],
["p", "Boa parte dos serviços públicos de um município ainda depende de leitura, cadastro e linguagem administrativa. Para uma pessoa idosa que enxerga pouco, para quem tem baixa escolaridade ou para quem tem deficiência auditiva, descobrir o horário de uma Unidade Básica de Saúde (UBS) ou avisar a prefeitura sobre um buraco na rua pode exigir a ajuda de outra pessoa. O município usado como referência foi São José dos Campos, com 697.054 habitantes no Censo 2022 (IBGE, 2023), cujas páginas de serviços (SÃO JOSÉ DOS CAMPOS, 2026) formaram a base de informações oficiais do projeto."],
["p", "O EloBairro foi criado para reduzir essa barreira. O cidadão pergunta ou relata um problema por texto, voz ou foto. O sistema responde com base em fontes oficiais e, quando o assunto é um problema do bairro, organiza o relato, retira dados pessoais, pede a confirmação do cidadão e gera um protocolo rastreável. O projeto se relaciona com os Objetivos de Desenvolvimento Sustentável (ODS) 10, redução das desigualdades, e 16, instituições eficazes e acessíveis (ONU, 2015)."],
["p", "Desde o início, o grupo decidiu que cada disciplina entregaria uma parte do mesmo sistema, e não um trabalho isolado. A Figura 1 mostra essa ligação. A interface e a API de Front-end são o ponto de encontro: chamam o assistente de voz, o motor de respostas, a visão computacional e as regras de automação, e recebem os eventos do celular e os protocolos do robô. O cluster define a infraestrutura que processa as fotos do módulo de visão, e a análise quântica trabalha sobre os protocolos que o sistema gera."],
["fig", "arq.png", 520, 297, "Arquitetura do EloBairro e ligação entre as disciplinas", "Elaborado pelos autores (2026)."],
["p", "As seções 2 a 9 descrevem a contribuição de cada disciplina, os resultados medidos e o papel dela no sistema. A seção 10 trata da governança: como as partes se integram, o que ainda está fora, os cuidados com dados pessoais e as decisões que continuam com pessoas. Os números vêm das evidências guardadas no repositório do projeto."],

["h1", "FRONT-END EM SISTEMAS DE IA"],
["p", "A disciplina entregou a interface em Streamlit e a API em FastAPI, que reúnem todos os módulos. O cidadão pode tirar dúvidas, relatar um problema com foto e acompanhar os avisos da casa. O gestor vê um painel com filtros combináveis, gráficos, mapa por região e a fila de casos em revisão (Figura 2). Toda entrada da API é validada com Pydantic, e os erros aparecem em português."],
["fig", "f_painel.png", 440, 298, "Painel do gestor com filtros e indicadores", "Elaborado pelos autores (2026)."],
["p", "O modelo de linguagem é chamado só no *back-end* e precisa responder em JSON, com categoria e urgência de listas fechadas. Se ele estiver fora do ar, demorar mais de 20 segundos ou responder fora do formato, o sistema usa as regras do módulo de RPA e avisa o cidadão. Nenhum protocolo é gravado sem que o cidadão confira a proposta. A interface usa a fonte Atkinson Hyperlegible, criada para pessoas com baixa visão, e oferece alto contraste, letra grande e redução das animações quando o sistema operacional pede. O módulo tem 32 testes automáticos, e os três casos de teste da IA (telefone no texto, relato vago e tentativa de forçar a urgência) tiveram o resultado esperado."],

["h1", "PROCESSAMENTO DE LINGUAGEM NATURAL"],
["p", "O assistente de voz transforma a fala em texto, busca a resposta no motor da disciplina de Generative AI, gera o texto com um modelo de linguagem e o devolve em áudio. A configuração final usa o Whisper *small*, o qwen2.5:1.5b e o Piper, todos rodando no computador, para que a voz do usuário não saia dele. Antes da síntese, a resposta é adaptada para a fala, com frases curtas e números, siglas e horários escritos por extenso. Pedidos de emergência recebem uma resposta fixa com os números 192, 193 e 190, e, quando a base não encontra nada, o assistente diz que não tem a informação em vez de inventar."],
["p", "Em 20 gravações reais do grupo, com três vozes e cinco áudios com ruído, a taxa de erro de palavras (WER) foi de 0,183 com o modelo *base* e ficou entre 0,150 e 0,175 com o *small*. Com a base real do RAG, o modelo de linguagem acertou 82,6% das perguntas e recusou todas as que estavam fora do escopo. Na avaliação cega feita por seis pessoas, as vozes do edge-tts e do Piper tiveram notas praticamente iguais, 4,30 e 4,26 em uma escala de 1 a 5. Em 30 gravações reais, a resposta levou em média 17,8 s para começar a tocar, em uma máquina com 2 processadores virtuais, e a etapa mais lenta foi o modelo de linguagem. No EloBairro, a aba de perguntas por voz usa a transcrição e a síntese deste módulo, ligadas à mesma API e à mesma base de conhecimento da pergunta por texto."],

["h1", "GENERATIVE AI"],
["p", "O motor de respostas usa geração aumentada por recuperação (RAG). O *corpus* reúne 33 páginas de serviços da Prefeitura de São José dos Campos, com URL e data de consulta de cada fonte. A busca é vetorial, com o modelo multilingual-e5-large, e devolve os três trechos mais próximos ao gerador gpt-4o-mini, que precisa citar as fontes. Se o trecho mais parecido tiver similaridade abaixo de 0,84, o motor não responde, e as instruções escondidas nos documentos são neutralizadas antes de chegar ao modelo."],
["p", "O sistema acertou 29 de 30 perguntas respondíveis e se absteve em todas as perguntas sem resposta no *corpus*. Nenhum dos 9 ataques diretos e nenhuma das 4 injeções indiretas funcionou. Uma integrante do grupo conferiu 15 respostas contra as páginas de origem: 9 de 10 respondíveis estavam corretas, com 1 falsa abstenção, e as 5 restantes tiveram o comportamento esperado. No EloBairro, o motor atende a rota POST /rag/perguntar, usada tanto pela pergunta por texto quanto pela pergunta por voz."],

["h1", "VISÃO COMPUTACIONAL"],
["p", "O módulo classifica fotos de concreto em duas classes: com fissura e sem fissura. Foi usada a base Concrete Crack Images for Classification (ÖZGENEL; SORGUÇ, 2018), com 2.000 imagens por classe, e uma MobileNetV2 pré-treinada. O limiar de 0,45 foi escolhido na validação, buscando *recall* de pelo menos 0,99. No teste, com 600 imagens, a acurácia foi de 98,17%, com 8 falsos positivos e 3 falsos negativos (Tabela 1 e Figura 3), e a mediana foi de cerca de 60 ms por imagem em CPU."],
["tab", "Tabela", "Métricas da visão computacional no conjunto de teste", ["Classe", "Precisão", "Recall", "F1"], [["Sem fissura", "0,9898", "0,9733", "0,9815"], ["Com fissura", "0,9738", "0,9900", "0,9818"]], [3071, 2000, 2000, 2000], "Elaborado pelos autores (2026)."],
["fig", "f_visao.png", 270, 203, "Matriz de confusão da visão computacional", "Elaborado pelos autores (2026)."],
["p", "O resultado é otimista para fotos de cidadãos, porque todas as imagens vêm de prédios de um mesmo campus, e por isso a tela sempre avisa que se trata de uma triagem e não de um laudo. No EloBairro, a foto anexada ao relato passa pelas rotas /visao/imagem e /visao/video, e o resultado segue com o protocolo para o gestor."],

["h1", "IOT E EMBEDDED AI"],
["p", "O módulo OuviAí reconhece no celular a campainha e a batida na porta e as separa do som ambiente, para avisar quem não ouve com um alerta grande na tela. O modelo foi treinado no Edge Impulse com características MFE e uma rede convolucional, em janelas de 1 segundo, usando sons públicos do Visualfy (NARANJO-ALCAZAR *et al.*, 2022) e do ESC-50 (PICZAK, 2015). A acurácia na validação foi de 87,7%, e o teste ao vivo com o celular acertou 12 de 15 tentativas (80%). O modelo usa 14,7 KB de memória e leva 7 ms por inferência."],
["p", "No EloBairro, o *script* ponte_alertas.py envia apenas a classe e a confiança para a rota POST /iot/eventos. A API ignora o som ambiente, eventos abaixo de 80% de confiança e repetições, e o aviso aparece na página Avisos da casa e no painel do gestor. Nenhum áudio é gravado ou enviado."],

["h1", "RPA E IA"],
["p", "O robô lê os relatos confirmados, mascara telefone, CPF, e-mail e CEP, remove duplicados, classifica categoria e urgência por regras e gera um protocolo no formato ELB-AAAAMMDD-NNNNN. Rodar o robô de novo não cria protocolos repetidos, e os casos com confiança abaixo de 0,5 vão para revisão humana. Ele também lê fontes públicas sem API: a lista de UBS da prefeitura, o arquivo de notícias e os avisos meteorológicos do Inmet. Roda sob demanda ou duas vezes por dia e avisa o gestor por e-mail só nos casos de urgência alta, sem o texto do cidadão."],
["p", "Em uma execução com 125 linhas, o robô gerou 107 protocolos, descartou 14 duplicados e 3 registros inválidos e mandou 1 caso para revisão. Em 30 relatos de teste escritos à mão, acertou 90,0% das categorias e 86,7% das urgências, contra 60,0% de um modelo de TF-IDF com regressão logística, e por isso as regras foram mantidas. No EloBairro, a API grava no mesmo banco SQLite do robô, com a mesma numeração, recebe os protocolos dele pela rota POST /protocolos e usa a mesma máscara e as mesmas regras como plano B quando o modelo de linguagem falha."],

["h1", "CLUSTER COMPUTING"],
["p", "A tarefa simulada no iSPD foi a classificação de fotos em lote do módulo de visão, situação esperada depois de uma chuva forte, quando muitas imagens chegam juntas. Cada foto é independente, o que permite dividir o trabalho entre vários *workers*. Foram modeladas 1.000 tarefas de 2.000 MFLOPS, com 4 Mbits de comunicação cada, em um cluster com um mestre e escalonador Workqueue. Entre os cenários, só o número de *workers* mudou (Tabela 2)."],
["tab", "Tabela", "Parâmetros e resultados das simulações no iSPD", ["Item", "Cenário A", "Cenário B", "Unidade"], [
  ["Workers", "2", "4", "máquinas"],
  ["Capacidade por worker", "1.000", "1.000", "MFLOPS/s"],
  ["Banda e latência do link", "100 e 0,001", "100 e 0,001", "Mbits/s e s"],
  ["Tempo simulado total", "1.021,05", "510,63", "s"],
  ["Processamento por worker", "1.000,0", "500,0", "valor do iSPD"],
  ["Ociosidade do processamento", "2,06", "2,08", "%"],
  ["Ociosidade da comunicação", "95,89", "91,77", "%"]
], [3471, 1800, 1800, 2000], "Elaborado pelos autores (2026)."],
["fig", "f_cluster2.png", 520, 117, "Resultado global do iSPD nos dois cenários", "Elaborado pelos autores (2026)."],
["p", "Dobrar os *workers* reduziu o tempo em 49,99%, com razão T2/T4 de 2,000 e eficiência de 99,98%. O ganho foi quase ideal porque cada tarefa leva 2 s de processamento e só 0,042 s de comunicação. A diferença para os 1.000 s e 500 s teóricos vem do Workqueue, que só envia a próxima tarefa quando recebe a anterior. O gargalo possível é o mestre, por onde passam todas as fotos: a comunicação total fica em 42 s em qualquer cenário, e passaria a limitar o sistema com cerca de 48 *workers*."],
["p", "No EloBairro, a simulação define como o módulo de visão deve ser executado em dias de pico: vários *workers* recebendo as fotos que chegam pela API. A hipótese de 2 s por imagem é conservadora, já que a MobileNetV2 levou cerca de 60 ms por imagem, e deve ser trocada por medições reais antes de dimensionar um cluster de verdade."],

["h1", "COMPUTAÇÃO QUÂNTICA"],
["p", "A análise identificou que quase todas as etapas do EloBairro crescem bem com computação clássica, colocando mais servidores. O gargalo que não se resolve assim é o despacho das equipes de campo para os protocolos gerados pelo sistema: decidir qual equipe atende qual endereço e em que ordem, respeitando urgência, horários e especialidade. É um problema de roteamento com janelas de tempo, cujo número de combinações cresce de forma fatorial."],
["p", "A capacidade escolhida foi a otimização, com formulação QUBO para algoritmos como o QAOA. Como hoje não há vantagem quântica demonstrada para esse problema, o roteiro começa com otimização clássica, segue com pilotos pequenos entre 2027 e 2029 e só prevê uso híbrido se quatro critérios forem cumpridos. A criptografia pós-quântica entra como trilha obrigatória para proteger o banco e a API, seguindo os padrões do NIST (NIST, 2024), porque protocolos guardados por anos podem ser copiados hoje e decifrados no futuro."],

["h1", "GOVERNANÇA E INTEGRAÇÃO"],
["h2", "Como as disciplinas se integram"],
["p", "Todas as disciplinas fazem parte do EloBairro. O Quadro 1 mostra o papel de cada uma e o ponto em que ela se liga ao sistema."],
["tab", "Quadro", "Integração das disciplinas no EloBairro", ["Disciplina", "Papel no sistema", "Ponto de integração"], [
  ["01 Front-end", "Interface do cidadão e do gestor", "API FastAPI que chama os demais módulos"],
  ["02 PLN", "Pergunta e resposta por voz", "Rotas de voz da API, com o RAG do 03"],
  ["03 Generative AI", "Respostas com fontes oficiais", "Rota /rag/perguntar"],
  ["04 Visão", "Triagem das fotos dos relatos", "Rotas /visao/imagem e /visao/video"],
  ["05 IoT", "Avisos de campainha e batida", "Rota /iot/eventos e página Avisos da casa"],
  ["06 RPA", "Protocolos, máscara e regras", "Banco SQLite único e rota /protocolos"],
  ["07 Cluster", "Processamento das fotos em pico", "Execução do módulo de visão em workers"],
  ["08 Quântica", "Despacho das equipes e criptografia", "Protocolos do banco e proteção da API"]
], [1900, 3386, 3785], "Elaborado pelos autores (2026)."],
["h2", "Limites da integração atual"],
["p", "Todas as disciplinas estão ligadas ao sistema, mas algumas funções ficaram para uma próxima etapa. O alerta do OuviAí depende do modelo exportado rodando em um computador, e a vibração no próprio celular exigiria um aplicativo nativo. Os protocolos criados pelo robô chegam sem região e não aparecem no mapa. O painel usa dados sintéticos, porque o grupo não tem acesso a relatos reais. O cluster foi simulado e o despacho quântico é um roteiro, sem execução em hardware real."],
["h2", "Dados pessoais, supervisão humana e riscos"],
["p", "O EloBairro guarda o mínimo de dados, como pede a Lei Geral de Proteção de Dados (BRASIL, 2018). Não há cadastro do cidadão. Telefone, CPF, e-mail, CEP e nome são mascarados antes de qualquer classificação, gravação ou envio a um modelo de linguagem, e áudio e foto não são guardados. Quando um serviço em nuvem é usado, a tela de consentimento informa o que é enviado. As chaves de API ficam fora do repositório."],
["p", "Nenhum módulo decide sozinho. O cidadão confirma ou corrige a proposta da IA, a regra de risco mantém a urgência alta em casos como acidente ou água entrando em casa, e o gestor revisa os casos incertos e muda o status do protocolo. O Quadro 2 resume os principais riscos e controles."],
["tab", "Quadro", "Principais riscos e controles", ["Risco", "Controle", "Onde"], [
  ["Resposta inventada", "Limiar de similaridade, abstenção e citação de fontes", "02 e 03"],
  ["Manipulação por texto", "Saída em JSON validada e regra de risco", "01 e 03"],
  ["Vazamento de dados", "Máscara antes do modelo e do banco", "01 e 06"],
  ["Falso alerta", "Limiar de confiança, aviso de triagem e filtro de repetição", "04 e 05"],
  ["Bairro atendido mais devagar", "Indicadores por região e limite de espera no despacho", "01 e 08"]
], [2700, 4871, 1500], "Elaborado pelos autores (2026)."],
["p", "Para acompanhar o serviço, o painel já mostra protocolos por categoria, urgência, região e período, casos em revisão e alertas do IoT. Em uma operação real, recomenda-se medir também a taxa de abstenção do motor de respostas, a proporção de propostas corrigidas pelo cidadão e o tempo de atendimento por região."],

["h1", "LINKS"],
["p", "**Vídeo de apresentação:** https://youtu.be/peT0RJlUPe4"],
["p", "**Repositório GitHub:** https://github.com/juliaathar/global-solution-2026.2"],

["h1", "CONCLUSÃO"],
["p", "O objetivo do trabalho era construir um único sistema que atendesse às nove disciplinas e fosse útil para quem tem dificuldade com os canais atuais da prefeitura. Chegamos a um protótipo em que o cidadão pergunta por texto ou voz, relata um problema com foto e recebe um protocolo, e em que o gestor acompanha os casos em um painel. Cada disciplina ocupa um lugar nesse fluxo, da interface à infraestrutura e ao planejamento futuro."],
["p", "A parte mais difícil não foi configurar cada modelo, e sim fazer os módulos conversarem. Foi preciso resolver conflitos de configuração, combinar um formato único de protocolo entre o robô e a API e decidir o que fazer quando um serviço falha. Aprendemos que definir esses contratos logo no começo teria poupado retrabalho."],
["p", "Também aprendemos que um bom número de acerto não basta. A visão passou de 98% em fotos de laboratório, mas ainda não foi testada com fotos de cidadãos, e o painel usa dados sintéticos. Por isso registramos as limitações junto de cada resultado e mantivemos uma pessoa na decisão final. Os próximos passos são o teste com usuários do público-alvo, a redução do tempo de resposta por voz e o uso de dados reais da prefeitura, para saber se o EloBairro de fato facilita a vida de quem mais precisa."],
];
