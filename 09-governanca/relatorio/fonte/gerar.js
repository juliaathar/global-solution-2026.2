const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
  HeadingLevel, Header, PageNumber, PageBreak, WidthType, BorderStyle, ShadingType,
  PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo, PositionalTabLeader,
  LevelFormat, VerticalAlign, TableLayoutType,
} = require("docx");

const conteudo = require("./conteudo.js");
const paginas = fs.existsSync("paginas.json") ? JSON.parse(fs.readFileSync("paginas.json", "utf8")) : {};
const FONTE = "Arial";
const CM = 567; // DXA por cm
const LARG = 9071; // 16 cm úteis

// ---------- texto com **negrito** e *itálico* ----------
function runs(texto, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|<<LINK_VIDEO>>)/g;
  let i = 0, m;
  while ((m = re.exec(texto))) {
    if (m.index > i) out.push(new TextRun({ text: texto.slice(i, m.index), ...base }));
    const t = m[0];
    if (t === "<<LINK_VIDEO>>") out.push(new TextRun({ text: "inserir o link do vídeo no YouTube (não listado)", highlight: "yellow", ...base }));
    else if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    i = m.index + t.length;
  }
  if (i < texto.length) out.push(new TextRun({ text: texto.slice(i), ...base }));
  return out;
}

const corpo = (t) => new Paragraph({
  children: runs(t), alignment: AlignmentType.JUSTIFIED,
  indent: { firstLine: Math.round(1.25 * CM) }, spacing: { line: 360, before: 0, after: 0 },
});
const vazio = (n = 1, line = 360) => Array.from({ length: n }, () => new Paragraph({ children: [], spacing: { line } }));
const centro = (t, op = {}) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { line: 360, ...(op.spacing || {}) },
  children: [new TextRun({ text: t, bold: !!op.bold, size: op.size || 24 })],
});
const quebra = () => new Paragraph({ children: [new PageBreak()] });
const tituloPre = (t) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { line: 360, after: 360 },
  children: [new TextRun({ text: t, bold: true })],
});

function linhaLista(rotulo, chave, op = {}) {
  const pg = paginas[chave] != null ? String(paginas[chave]) : "0";
  return new Paragraph({
    spacing: { line: 360 }, indent: { left: 0, right: 500 },
    tabStops: [{ type: "right", position: LARG, leader: "dot" }],
    children: [
      new TextRun({ text: rotulo + "\t" + pg, bold: !!op.bold }),
    ],
  });
}

// ---------- numeração de seções, figuras, tabelas ----------
let n1 = 0, n2 = 0, nFig = 0, nTab = 0, nQua = 0;
const sumario = [], figuras = [], tabelas = [], quadros = [];
const textual = [];

const borda = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const semBorda = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };

function legenda(t) {
  return new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { line: 240, before: 240, after: 120 }, children: [new TextRun({ text: t, size: 20 })] });
}
function fonte(t) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { line: 240, before: 80, after: 240 }, children: [new TextRun({ text: "Fonte: " + t, size: 20 })] });
}

for (const b of conteudo) {
  const tipo = b[0];
  if (tipo === "h1") {
    n1++; n2 = 0;
    const rot = `${n1} ${b[1]}`;
    sumario.push({ rot, chave: rot, nivel: 1 });
    if (n1 === 1) { /* a introdução já começa em página nova */ }
    textual.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(rot)] }));
  } else if (tipo === "h2") {
    n2++;
    const rot = `${n1}.${n2} ${b[1]}`;
    sumario.push({ rot, chave: rot, nivel: 2 });
    textual.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(rot)] }));
  } else if (tipo === "p") {
    textual.push(corpo(b[1]));
  } else if (tipo === "pend") {
    textual.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { firstLine: Math.round(1.25 * CM) }, spacing: { line: 360 }, children: [new TextRun({ text: b[1], highlight: "yellow" })] }));
  } else if (tipo === "fig") {
    nFig++;
    const [, arq, w, h, tit, fon] = b;
    const rot = `Figura ${nFig} – ${tit}`;
    figuras.push({ rot, chave: rot });
    textual.push(legenda(rot));
    textual.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, children: [new ImageRun({ type: "png", data: fs.readFileSync(require("path").join(__dirname, "figuras", arq)), transformation: { width: w, height: h }, altText: { title: tit, description: tit, name: arq } })] }));
    textual.push(fonte(fon));
  } else if (tipo === "tab") {
    const [, especie, tit, cab, linhas, larg, fon] = b;
    let rot;
    if (especie === "Tabela") { nTab++; rot = `Tabela ${nTab} – ${tit}`; tabelas.push({ rot, chave: rot }); }
    else { nQua++; rot = `Quadro ${nQua} – ${tit}`; quadros.push({ rot, chave: rot }); }
    textual.push(legenda(rot));
    const tabela = especie === "Tabela";
    // Tabela (IBGE): sem bordas laterais; Quadro: fechado
    const bordas = (ultima, primeira) => tabela
      ? { top: primeira ? borda : semBorda, bottom: ultima || primeira ? borda : semBorda, left: semBorda, right: semBorda }
      : { top: borda, bottom: borda, left: borda, right: borda };
    const celula = (t, j, cabecalho, ultima) => new TableCell({
      width: { size: larg[j], type: WidthType.DXA }, borders: bordas(ultima, cabecalho),
      margins: { top: 50, bottom: 50, left: 90, right: 90 }, verticalAlign: VerticalAlign.CENTER,
      shading: cabecalho && !tabela ? { type: ShadingType.CLEAR, color: "auto", fill: "E7E7E7" } : undefined,
      children: [new Paragraph({ alignment: tabela && j > 0 ? AlignmentType.CENTER : AlignmentType.LEFT, spacing: { line: 240 }, children: [new TextRun({ text: t, size: 20, bold: cabecalho })] })],
    });
    const rows = [new TableRow({ tableHeader: true, cantSplit: true, children: cab.map((t, j) => celula(t, j, true, false)) })];
    linhas.forEach((l, k) => rows.push(new TableRow({ cantSplit: true, children: l.map((t, j) => celula(t, j, false, k === linhas.length - 1)) })));
    textual.push(new Table({ width: { size: LARG, type: WidthType.DXA }, columnWidths: larg, layout: TableLayoutType.FIXED, alignment: AlignmentType.CENTER, rows }));
    textual.push(fonte(fon));
  }
}

// ---------- referências ----------
const referencias = [
  "BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). **Diário Oficial da União**: seção 1, Brasília, DF, 15 ago. 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: 19 nov. 2026.",
  "IBGE. **Cidades e Estados**: São José dos Campos. Rio de Janeiro: IBGE, 2023. Disponível em: https://www.ibge.gov.br/cidades-e-estados/sp/sao-jose-dos-campos.html. Acesso em: 18 nov. 2026.",
  "NARANJO-ALCAZAR, J. *et al*. An open-set recognition and few-shot learning dataset for audio event classification in domestic environments. **Pattern Recognition Letters**, [*s. l.*], v. 164, p. 40-45, 2022. DOI: 10.1016/j.patrec.2022.10.019.",
  "NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST). **FIPS 203**: module-lattice-based key-encapsulation mechanism standard. Gaithersburg: NIST, 2024. DOI: 10.6028/NIST.FIPS.203.",
  "ORGANIZAÇÃO DAS NAÇÕES UNIDAS (ONU). **Transformando nosso mundo**: a Agenda 2030 para o Desenvolvimento Sustentável. Nova York: ONU, 2015. Disponível em: https://brasil.un.org/pt-br/sdgs. Acesso em: 19 nov. 2026.",
  "ÖZGENEL, Ç. F.; SORGUÇ, A. G. Performance comparison of pretrained convolutional neural networks on crack detection in buildings. *In*: INTERNATIONAL SYMPOSIUM ON AUTOMATION AND ROBOTICS IN CONSTRUCTION, 35., 2018, Berlim. **Proceedings** [...]. Berlim: IAARC, 2018. p. 693-700.",
  "PICZAK, K. J. ESC: dataset for environmental sound classification. *In*: ACM INTERNATIONAL CONFERENCE ON MULTIMEDIA, 23., 2015, Brisbane. **Proceedings** [...]. Nova York: ACM, 2015. p. 1015-1018.",
  "SÃO JOSÉ DOS CAMPOS (SP). Prefeitura Municipal. **Serviços**. São José dos Campos, 2026. Disponível em: https://www.sjc.sp.gov.br/servicos/. Acesso em: 10 nov. 2026.",
];
sumario.push({ rot: "REFERÊNCIAS", chave: "REFERÊNCIAS", nivel: 0 });
textual.push(new Paragraph({ heading: HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER, pageBreakBefore: true, children: [new TextRun("REFERÊNCIAS")] }));
for (const r of referencias) textual.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { line: 240, after: 240 }, children: runs(r) }));

// ---------- pré-textuais ----------
const autores = ["BRUNO FERNANDES NASCIMENTO – RM 552574", "EDGAR LÓDULA DE ASSIS – RM 565260", "JÚLIA ABEN-ATHAR – RM 566325"];
const TITULO = "ELOBAIRRO: ASSISTENTE DE SERVIÇOS PÚBLICOS DO BAIRRO COM INTELIGÊNCIA ARTIFICIAL";
const SUB = "Relatório de integração e governança";

const capa = [
  centro("FACULDADE DE INFORMÁTICA E ADMINISTRAÇÃO PAULISTA", { bold: true }),
  centro("TECNOLOGIA EM INTELIGÊNCIA ARTIFICIAL", { bold: true }),
  ...vazio(3),
  ...autores.map((a) => centro(a)),
  ...vazio(6),
  centro(TITULO, { bold: true }),
  centro(SUB),
  ...vazio(9),
  centro("SÃO PAULO"),
  centro("2026"),
];

const natureza = "Relatório apresentado à Faculdade de Informática e Administração Paulista (FIAP), como requisito parcial da Global Solution 2026.2 do 2º ano do curso superior de Tecnologia em Inteligência Artificial, para a disciplina de Governança em Inteligência Artificial e Business Analytics, com a integração das entregas de Front-end em Sistemas de IA, Processamento de Linguagem Natural, Generative AI, Visão Computacional, IoT e Embedded AI, RPA e IA, Cluster Computing e Computação Quântica.";
const folhaRosto = [
  ...autores.map((a) => centro(a)),
  ...vazio(7),
  centro(TITULO, { bold: true }),
  centro(SUB),
  ...vazio(2),
  new Paragraph({ indent: { left: 8 * CM }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 240 }, children: [new TextRun({ text: natureza, size: 20 })] }),
  ...vazio(8),
  centro("SÃO PAULO"),
  centro("2026"),
];

const resumoTxt = "Este relatório apresenta o EloBairro, assistente de serviços públicos voltado a pessoas idosas, com baixa alfabetização ou com deficiência, desenvolvido na Global Solution 2026.2 da FIAP. O cidadão pergunta ou relata um problema do bairro por texto, voz ou foto, e o sistema responde com base em fontes oficiais de São José dos Campos ou gera um protocolo após a confirmação do próprio cidadão. Oito disciplinas contribuíram com módulos do mesmo sistema: interface e API, assistente de voz, motor de respostas com recuperação de documentos, classificação de fissuras em fotos, reconhecimento de sons domésticos no celular, robô de automação de protocolos, simulação de processamento em cluster e análise de computação quântica. O documento descreve cada módulo, os resultados medidos e a forma de integração, e reúne na seção de governança o que foi e o que não foi integrado, os cuidados com dados pessoais segundo a LGPD, os pontos de supervisão humana e os riscos com seus controles.";
const abstractTxt = "This report presents EloBairro, a public services assistant designed for older people, people with low literacy and people with disabilities, developed for the FIAP Global Solution 2026.2. Citizens ask questions or report neighborhood problems by text, voice or photo, and the system answers from official sources of São José dos Campos or creates a ticket after the citizen confirms it. Eight courses contributed modules to the same system: interface and API, voice assistant, retrieval-augmented answer engine, crack classification in photos, recognition of household sounds on a mobile phone, ticket automation robot, cluster processing simulation and a quantum computing analysis. The document describes each module, its measured results and how it was integrated, and the governance section summarizes what was and was not integrated, personal data protection under the Brazilian LGPD, human oversight points and the main risks with their controls.";
const chaves = (rot, t) => new Paragraph({ spacing: { line: 360, before: 240 }, children: [new TextRun({ text: rot, bold: true }), new TextRun(t)] });
const paraSimples = (t) => new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { line: 360 }, children: [new TextRun(t)] });

const siglas = [
  ["API", "Interface de Programação de Aplicações"], ["CNN", "Rede Neural Convolucional"], ["CORS", "Compartilhamento de Recursos entre Origens"],
  ["FIAP", "Faculdade de Informática e Administração Paulista"], ["IA", "Inteligência Artificial"], ["IBGE", "Instituto Brasileiro de Geografia e Estatística"],
  ["Inmet", "Instituto Nacional de Meteorologia"], ["IoT", "Internet das Coisas"], ["JSON", "JavaScript Object Notation"],
  ["LGPD", "Lei Geral de Proteção de Dados Pessoais"], ["LLM", "Modelo de Linguagem de Grande Escala"], ["MFE", "Mel-filterbank Energy"],
  ["NIST", "National Institute of Standards and Technology"], ["ODS", "Objetivo de Desenvolvimento Sustentável"], ["PLN", "Processamento de Linguagem Natural"],
  ["QAOA", "Quantum Approximate Optimization Algorithm"], ["QUBO", "Quadratic Unconstrained Binary Optimization"], ["RAG", "Geração Aumentada por Recuperação"],
  ["RPA", "Automação Robótica de Processos"], ["STT", "Conversão de Fala em Texto"], ["TTS", "Conversão de Texto em Fala"],
  ["UBS", "Unidade Básica de Saúde"], ["WER", "Taxa de Erro de Palavras"],
];

const pre = [
  ...folhaRosto, quebra(),
  tituloPre("LISTA DE ILUSTRAÇÕES"),
  ...figuras.map((f) => linhaLista(f.rot, f.chave)),
  ...quadros.map((f) => linhaLista(f.rot, f.chave)),
  ...vazio(1),
  tituloPre("LISTA DE TABELAS"),
  ...tabelas.map((f) => linhaLista(f.rot, f.chave)), quebra(),
  tituloPre("SUMÁRIO"),
  ...sumario.map((s) => linhaLista(s.rot, s.chave, { bold: s.nivel !== 2 })),
];

const cabecalho = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ children: [PageNumber.CURRENT], size: 20 })] })] });
const margens = { top: 3 * CM, left: 3 * CM, bottom: 2 * CM, right: 2 * CM, header: 2 * CM };
const pagina = { size: { width: 11906, height: 16838 }, margin: margens };

const doc = new Document({
  creator: "Bruno Fernandes Nascimento; Edgar Lódula de Assis; Júlia Aben-Athar",
  title: "EloBairro: relatório de integração e governança",
  styles: {
    default: { document: { run: { font: FONTE, size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONTE, size: 24, bold: true, color: "000000" }, paragraph: { spacing: { before: 480, after: 360, line: 360 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONTE, size: 24, bold: true, color: "000000" }, paragraph: { spacing: { before: 360, after: 240, line: 360 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  sections: [
    { properties: { page: pagina }, children: capa },
    { properties: { page: { ...pagina, pageNumbers: { start: 1 } } }, children: pre },
    { properties: { page: pagina }, headers: { default: cabecalho }, children: textual },
  ],
});

Packer.toBuffer(doc).then((b) => { fs.writeFileSync("relatorio_governanca.docx", b); console.log("ok", { figuras: nFig, tabelas: nTab, quadros: nQua }); });
