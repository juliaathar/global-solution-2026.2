---
titulo: "EloBairro e a computação quântica: onde ela pode ajudar, quando e com que cuidados"
---

# EloBairro e a computação quântica

**Onde ela pode ajudar, quando e com que cuidados**

FIAP · Engenharia de Software · Global Solution 2026.2 · Computação Quântica

| Nome completo | RM |
|---|---|
| Bruno Fernandes Nascimento | 552574 |
| Edgar Lódula de Assis | 565260 |
| Júlia Aben-Athar | 566325 |

São Paulo, novembro de 2026

---

## 1. Resumo

O EloBairro recebe relatos de problemas do bairro (buraco, poste apagado, alagamento) por texto, voz ou foto e
transforma cada um em protocolo. Este documento responde a uma pergunta: **se o número de cidadãos crescer muito,
em que ponto o sistema trava, e a computação quântica ajuda nesse ponto?**

A resposta curta é esta:

- Quase tudo o que o protótipo faz hoje escala bem com computação clássica: mais servidores resolvem.
- O gargalo que **não** se resolve só com mais máquinas é decidir **qual equipe atende qual protocolo e em que
  ordem**, um problema de roteamento com janelas de tempo. Ele cresce de forma combinatória.
- Escolhemos a capacidade quântica de **otimização** para esse gargalo. Hoje ela **não** supera os métodos
  clássicos, então o plano é usar otimização clássica agora e só testar a quântica com critérios claros de adoção.
- Em paralelo, e independente de computador quântico, o EloBairro precisa migrar para **criptografia pós-quântica**,
  porque guarda dados de cidadãos por anos.

## 2. O gargalo real quando o número de cidadãos cresce

### 2.1 Tamanho do problema

São José dos Campos tinha 697.054 habitantes no Censo 2022 (IBGE). Para dimensionar, usamos uma **hipótese**:
1% da população faz um relato por mês. Isso dá cerca de **7.000 relatos por mês, ou 230 por dia útil**,
espalhados pelas 6 regiões da cidade. Em dias de chuva forte, o volume de alagamentos e quedas de árvore sobe muito
em poucas horas.

### 2.2 O que escala bem (e não precisa de quântico)

| Etapa do EloBairro | Como cresce | Solução clássica |
|---|---|---|
| Entender o relato (regras e LLM) | linear: 1 chamada por relato | mais instâncias da API |
| Busca nas fontes oficiais (RAG) | quase constante por pergunta (busca vetorial) | índice vetorial, cache |
| Visão computacional nas fotos | linear | mais workers: na simulação da disciplina de Cluster, passar de 2 para 4 workers reduziu o tempo de 1.021 s para 511 s com 1.000 imagens |
| Detectar duplicados | hoje compara cada relato com todos os abertos (cresce com o quadrado) | índice por região e categoria, *hashing* de similaridade |
| Banco de protocolos (SQLite) | linear | banco de dados servidor |

Todos esses pontos têm saída conhecida e barata. Colocar computação quântica neles seria tecnologia procurando
problema.

### 2.3 O que não escala: despachar as equipes

Depois que os protocolos existem, a prefeitura precisa decidir, todo dia, **quais equipes vão a quais endereços e
em que ordem**, respeitando:

- a urgência (alagamento com água entrando em casa vem antes de lixeira cheia);
- janelas de tempo (escola só pode ser atendida fora do horário de aula);
- a especialidade da equipe (eletricista não tapa buraco);
- a jornada de trabalho e o deslocamento.

Esse é o **problema de roteamento de veículos com janelas de tempo** (VRPTW), que é NP-difícil. Para uma única
equipe com *n* paradas, o número de ordens possíveis é *n!*:

| Paradas por equipe | Ordens possíveis |
|---|---|
| 5 | 120 |
| 10 | 3.628.800 |
| 15 | 1,3 × 10¹² |
| 20 | 2,4 × 10¹⁸ |

Com 20 equipes dividindo 230 protocolos, a escolha também envolve **qual** protocolo vai para **qual** equipe, o
que multiplica ainda mais as combinações. Mais servidores não mudam esse crescimento: só heurísticas melhores
mudam. É por isso que esse é o gargalo real, e é nele que faz sentido perguntar pela computação quântica.

## 3. A capacidade quântica escolhida e por quê

| Capacidade | Serve ao EloBairro? | Motivo |
|---|---|---|
| **Otimização** | **Sim (escolhida)** | é exatamente o formato do gargalo: escolher a melhor combinação entre bilhões |
| Simulação | Não | serve para química e materiais; o EloBairro não simula moléculas |
| Busca (Grover) | Não | a melhora é quadrática e exige máquina tolerante a falhas; nossa busca é semântica e já é rápida |
| Criptografia pós-quântica (PQC) | Sim, como **proteção obrigatória** | não usa computador quântico: é criptografia clássica que resiste a ele. Entra no roadmap como trilha paralela (seção 4) |

**Como a otimização quântica entraria.** O despacho de um dia, ou de uma região, é escrito como um problema
QUBO (otimização binária quadrática sem restrições): cada variável diz "a equipe *e* atende o protocolo *p* na
posição *k*". Esse formato é o que algoritmos como o **QAOA** (em computadores de portas) e o **recozimento
quântico** (*quantum annealing*) recebem. A literatura já formula o roteamento de veículos dessa forma e testa o
QAOA em instâncias pequenas.

**O limite prático.** Na formulação mais comum, *n* paradas pedem cerca de *n²* variáveis binárias: 15 paradas são
225 qubits e 50 paradas são 2.500 qubits, sem contar os qubits extras de correção de erro. É por isso que os
trabalhos atuais dividem o problema em pedaços pequenos e combinam partes clássicas e quânticas.

## 4. Roadmap

O roadmap tem duas trilhas. A trilha de **otimização** só avança de fase se a anterior provar valor. A trilha de
**proteção (PQC)** tem datas fixas, porque o risco existe mesmo antes do computador quântico chegar.

### Fase 0: hoje (2026). Tudo clássico

- **O que a IA clássica entrega:** o EloBairro já classifica, prioriza e gera protocolos. O próximo passo é um
  despacho diário com otimização clássica (por exemplo, OR-Tools ou heurísticas de busca local), com urgência e
  janelas de tempo.
- **O que o quântico agrega:** nada ainda. Esta fase cria a **linha de base**: tempo de atendimento, distância
  percorrida e protocolos urgentes atendidos no prazo. Sem ela não dá para saber se algo quântico é melhor.
- **Proteção:** inventariar onde o EloBairro usa criptografia (HTTPS, banco, assinaturas de protocolo) e ligar a
  troca de chaves híbrida (clássica + ML-KEM) onde as bibliotecas já permitem.
- **Benefício ao público:** atendimento mais rápido dos casos urgentes já com métodos que existem hoje.

### Fase 1: experimentos controlados (2027 a 2029)

- **O que a IA clássica entrega:** continua sendo o despacho oficial.
- **O que o quântico agrega:** pilotos **fora da produção**. Pegamos um pedaço real e pequeno (uma região, uma
  equipe, até 15 paradas), escrevemos como QUBO e rodamos QAOA em simuladores e em máquinas na nuvem, comparando
  com o solver clássico **na mesma instância**: custo da rota, tempo de cálculo e custo em reais.
- **Proteção:** migrar assinaturas e troca de chaves para os padrões do NIST (ML-KEM, ML-DSA, SLH-DSA) nos sistemas
  que guardam dados por mais tempo, como o histórico de protocolos.
- **Benefício ao público:** nenhum direto ainda. O ganho é saber, com dados, se vale a pena continuar.

### Fase 2: uso híbrido, se a Fase 1 provar valor (2030 a 2035)

- **O que a IA clássica entrega:** a maior parte do planejamento, o plano B e a validação de todo resultado.
- **O que o quântico agrega:** se as máquinas tolerantes a falhas anunciadas para o fim da década funcionarem e os
  pilotos mostrarem ganho, o otimizador quântico vira **um** componente do planejamento: recalcula rotas de
  emergência em dias de chuva, quando tudo muda em poucas horas. O resultado sempre passa por checagem clássica e
  por aprovação do gestor.
- **Proteção:** concluir a migração antes de 2030, quando o NIST passa a considerar RSA e curvas elípticas
  obsoletos, e muito antes de 2035, quando deixam de ser permitidos.
- **Benefício ao público:** menos tempo com rua alagada ou poste apagado nos piores dias, que são os que mais
  afetam quem tem mobilidade reduzida.

### Fase 3: depois de 2035

Só se a vantagem for estável e barata. Se não for, o EloBairro segue clássico, e isso é um resultado aceitável.

## 5. Ética, LGPD e ODS em cada fase

| Fase | Ética e LGPD | ODS |
|---|---|---|
| 0 | O otimizador recebe só **endereço do problema, categoria e urgência**, nunca nome, telefone ou texto do cidadão (o EloBairro já tira esses dados do texto antes de guardar). Inventário de criptografia é exigência de segurança da LGPD. | ODS 16: atendimento rastreável por protocolo |
| 1 | Os pilotos usam **dados sintéticos ou anonimizados**. Enviar dados para nuvem quântica fora do Brasil é transferência internacional (LGPD, art. 33): só com base legal e contrato. | ODS 9: inovação com teste antes de adoção |
| 2 | **Equidade:** um otimizador que só minimiza quilômetros tende a deixar bairros afastados para depois. A função objetivo terá um limite de espera máximo por região, e o gestor verá a explicação de cada rota. Decisão final sempre humana. | ODS 10: bairros periféricos não ficam para trás. ODS 11: cidade mais resiliente em chuva forte |
| Todas | **Colher agora, decifrar depois:** alguém pode copiar hoje dados criptografados e abri-los quando houver um computador quântico capaz. Protocolos guardados por anos são alvo disso, por isso a PQC começa já. Custo e energia dos experimentos são registrados e comparados ao ganho. | ODS 16: instituições confiáveis |

## 6. Realismo: quando faz sentido

- **A vantagem quântica em otimização ainda não foi demonstrada de forma geral.** Algoritmos como QAOA e
  recozimento quântico são heurísticas sem prova de que superam os melhores métodos clássicos em instâncias reais.
  Revisões recentes sobre transporte urbano concluem que vantagens estáveis e reproduzíveis ainda precisam ser
  demonstradas, e recomendam que órgãos públicos priorizem validação.
- **O roteamento de uma prefeitura de médio porte é bem atendido por métodos clássicos.** Centenas de paradas por
  dia estão dentro do que solvers clássicos resolvem com qualidade em minutos. O quântico só entraria em
  replanejamento de emergência, e mesmo assim só se ganhar na comparação.
- **O hardware ainda está chegando.** A IBM, por exemplo, anuncia para 2029 o Starling, com 200 qubits lógicos.
  Isso permitiria instâncias pequenas, não a cidade inteira de uma vez.
- **A ameaça à criptografia está mais perto do que a vantagem em otimização.** Em 2019 estimava-se que quebrar
  RSA-2048 exigiria 20 milhões de qubits; em 2025 a estimativa caiu para menos de 1 milhão, em menos de uma semana
  de cálculo. Por isso a trilha de proteção tem prazo e a de otimização, não.

**Critérios para adotar otimização quântica no EloBairro** (todos ao mesmo tempo):

1. ganho medido sobre o melhor solver clássico, na mesma instância real, em tempo ou qualidade da rota;
2. custo por execução menor que o ganho operacional;
3. resultado explicável ao gestor e com plano B clássico;
4. dados tratados conforme a LGPD, sem identificar cidadãos.

Se esses critérios não forem atendidos, a decisão correta é **não usar** computação quântica para otimização e
manter apenas a trilha de criptografia pós-quântica.

## 7. Conclusão

Para o EloBairro, a computação quântica não é uma peça para hoje. O gargalo que aparece com o crescimento é
combinatório (despachar equipes) e, por isso, é o único lugar onde a otimização quântica poderia ajudar no futuro.
O plano é resolver com métodos clássicos agora, medir, testar o quântico em pilotos pequenos e só adotar com
critérios objetivos. Já a criptografia pós-quântica é uma necessidade presente: os dados dos cidadãos guardados
hoje precisam continuar protegidos quando os computadores quânticos ficarem capazes.

## Referências

- IBGE. Cidades e Estados: São José dos Campos. Censo Demográfico 2022. https://www.ibge.gov.br/cidades-e-estados/sp/sao-jose-dos-campos.html
- NIST. NIST Releases First 3 Finalized Post-Quantum Encryption Standards (FIPS 203, 204 e 205), 13 ago. 2024. https://www.nist.gov/node/1856616
- NIST. IR 8547, Transition to Post-Quantum Cryptography Standards (versão final, out. 2026), resumida em: Cloud Security Alliance, *NIST IR 8547 Final*. https://labs.cloudsecurityalliance.org/research/csa-research-note-nist-ir8547-pqc-transition-20261030-csa-st/
- GIDNEY, C. How to factor 2048 bit RSA integers with less than a million noisy qubits. arXiv:2505.15917, 2025. https://arxiv.org/abs/2505.15917v1
- AZFAR, T. et al. Quantum-Assisted Vehicle Routing: Realizing QAOA-based Approach on Gate-Based Quantum Computer. arXiv:2505.01614, 2025. https://arxiv.org/html/2505.01614v1
- ONAH, C.; MICHIELSEN, K. Requirements for Early Quantum Advantage and Quantum Utility in the Capacitated Vehicle Routing Problem. arXiv:2509.11469, 2025. https://arxiv.org/abs/2509.11469v1
- The Quantum Insider. IBM Offers Roadmap Toward Large-Scale, Fault-Tolerant Quantum Computer, 10 jun. 2025. https://thequantuminsider.com/2025/06/10/ibm-offers-roadmap-toward-large-scale-fault-tolerant-quantum-computer/
- Quantum Zeitgeist. Quantum Transport: Classical Methods Beat Quantum for Now (revisão de J. Xu et al., UNSW). https://quantumzeitgeist.com/quantum-transport-networks-scalability/
- BRASIL. Lei nº 13.709/2018 (LGPD), arts. 33 (transferência internacional) e 46 (segurança).
- EloBairro. Resultados da simulação no iSPD, pasta `07-cluster/cenarios_ispd/resultados.md`.
