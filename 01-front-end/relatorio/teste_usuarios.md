# Teste de uso com 3 pessoas

> Teste aplicado pelo grupo com 3 pessoas. Cerca de 10 minutos por pessoa.

## Como conduzir

1. Suba o sistema (`docker compose up` ou os dois comandos do README) e abra http://localhost:8501.
2. Explique só isto: "É um app da prefeitura para tirar dúvidas e avisar problemas do bairro. Vou pedir três tarefas. Pense em voz alta."
3. Não ajude durante a tarefa. Anote onde a pessoa travou, o que ela disse e quanto tempo levou.
4. No fim, faça as 3 perguntas de opinião.
5. Peça autorização para citar a idade e o perfil (sem nome). Não grave áudio nem vídeo do rosto sem consentimento por escrito.

Perfis sugeridos, pensando no público do EloBairro: uma pessoa com mais de 60 anos, uma pessoa com pouca familiaridade com celular ou baixa visão, e uma pessoa jovem como controle.

## Tarefas

| # | Tarefa | Sucesso quando |
|---|---|---|
| T1 | "Descubra o que precisa levar para fazer o Cadastro Único." | Lê a resposta e encontra a fonte oficial |
| T2 | "Avise a prefeitura que o poste da sua rua está apagado." | Chega ao número do protocolo, conferindo antes de confirmar |
| T3 | "Imagine que você não ouve bem. Veja se alguém tocou a campainha." | Encontra o aviso em Avisos da casa |

## Perguntas de opinião (nota de 1 a 5)

- Q1. Foi fácil entender o que fazer em cada tela?
- Q2. Você confiaria no protocolo e na resposta mostrada?
- Q3. O tamanho da letra e as cores ajudaram a ler?

## Resultados

| Pessoa (perfil, sem nome) | T1 | T2 | T3 | Tempo total | Q1 | Q2 | Q3 | Onde travou / comentário |
|---|---|---|---|---|---|---|---|---|
| P1: 67 anos, aposentada, usa WhatsApp, enxerga pior de perto | Sim | Sim | Sim | cerca de 3 min | 5 | 5 | 4 | Não travou. Sem comentários. |
| P2: 45 anos, ensino fundamental, usa pouco o computador | Sim | Sim | Sim | cerca de 6 min | 3 | 5 | 4 | Teve dificuldade na leitura dos textos entre os cards. Comentou que o visual não estava muito didático. |
| P3: 22 anos, estudante, usa apps o dia todo | Sim | Sim | Sim | cerca de 5 min | 5 | 5 | 5 | Não travou. Gostou do aplicativo e disse que usaria no dia a dia. |

## O que mudamos depois do teste

| Problema observado | Mudança feita | Commit |
|---|---|---|
| Identidade visual pouco didática, com textos difíceis de ler entre os cards (P2, na versão anterior do visual) | Refeita a identidade visual do sistema, com animações, ícones e textos mais simples e didáticos | 75732cc |
