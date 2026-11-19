"""Organiza as gravações do grupo: converte para WAV 16 kHz mono, nomeia, confere a qualidade e
preenche o manifesto de STT.

    python testes/organizar_audios.py                 # usa audios_teste/entrada/
    python testes/organizar_audios.py --so-conferir   # só confere, não grava nada
    python testes/organizar_audios.py --forcar        # sobrescreve áudios já organizados

Entrada (audios_teste/entrada/, fora do git porque guarda os originais):
  * os arquivos de áudio (wav, mp3, m4a, ogg, opus, aac, flac, webm...), um por frase;
  * vozes.csv  (modelo em audios_teste/modelos/vozes.csv): uma linha por voz A, B, C, com faixa etária,
    sotaque e consentimento ("sim"). Sem consentimento registrado, a voz não é processada;
  * mapeamento.csv (opcional, modelo em audios_teste/modelos/): original,codigo. Sem ele, o nome do
    arquivo (sem extensão) precisa ser o próprio código: stt_01, c03_t2...

Saída: audios_teste/stt/stt_XX.wav, audios_teste/e2e/cNN_tN.wav, manifesto_stt.csv com faixa etária e
sotaque preenchidos e evidencias/audios_qualidade.csv. Os originais não são alterados nem apagados.
Qualquer formato que não seja WAV PCM precisa do pacote `av` (já vem com o faster-whisper).
"""
import argparse
import hashlib
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import AUDIOS, EVIDENCIAS, TESTES, escrever_csv, ler_csv  # noqa: E402

TAXA = 16000
DURACAO_MIN, DURACAO_MAX = 1.0, 15.0
NIVEL_MIN_DBFS = -45.0      # abaixo disso a gravação está praticamente muda
CLIPPING_MAX = 0.01         # mais de 1% das amostras no limite = áudio estourado
EXTENSOES = {".wav", ".mp3", ".m4a", ".ogg", ".opus", ".aac", ".flac", ".webm", ".mp4", ".3gp", ".amr", ".wma"}


# ------------------------------------------------------------------ leitura e conversão
def _ler_wav(caminho: Path) -> tuple[np.ndarray, int] | None:
    """Lê WAV PCM 16 bits com a biblioteca padrão. Devolve None se não for esse formato."""
    try:
        with wave.open(str(caminho), "rb") as w:
            if w.getsampwidth() != 2:
                return None
            canais, taxa = w.getnchannels(), w.getframerate()
            dados = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    except (wave.Error, EOFError):
        return None
    if canais > 1:
        dados = dados.reshape(-1, canais).mean(axis=1)
    return dados, taxa


def _ler_com_av(caminho: Path) -> np.ndarray:
    import av  # import tardio: só para formatos que não são WAV PCM
    partes = []
    with av.open(str(caminho)) as c:
        ra = av.AudioResampler(format="s16", layout="mono", rate=TAXA)
        for quadro in c.decode(audio=0):
            for q in ra.resample(quadro):
                partes.append(q.to_ndarray().reshape(-1))
        for q in ra.resample(None) or []:
            partes.append(q.to_ndarray().reshape(-1))
    if not partes:
        raise ValueError("o arquivo não tem áudio")
    return np.concatenate(partes).astype(np.float32) / 32768.0


def _reamostrar(x: np.ndarray, de: int, para: int = TAXA) -> np.ndarray:
    if de == para or len(x) == 0:
        return x
    n = int(round(len(x) * para / de))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def carregar(caminho: Path) -> np.ndarray:
    """Devolve o áudio como float32 mono, 16 kHz, entre -1 e 1."""
    if caminho.suffix.lower() == ".wav":
        r = _ler_wav(caminho)
        if r is not None:
            return _reamostrar(*r)
    return _ler_com_av(caminho)


def gravar_wav(caminho: Path, x: np.ndarray) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ qualidade
def _dbfs(v: float) -> float:
    return 20 * np.log10(max(float(v), 1e-9))


def medir(x: np.ndarray) -> dict:
    """Duração, nível, piso de ruído (10º percentil da energia por janela de 50 ms) e clipping."""
    janela = TAXA // 20
    n = len(x) // janela
    rms = np.sqrt((x[:n * janela].reshape(n, janela) ** 2).mean(axis=1)) if n else np.array([0.0])
    return {
        "duracao_s": round(len(x) / TAXA, 2),
        "nivel_dbfs": round(_dbfs(np.sqrt((x ** 2).mean())) if len(x) else -120.0, 1),
        "piso_ruido_dbfs": round(_dbfs(np.percentile(rms, 10)), 1),
        "clipping_pct": round(100 * float((np.abs(x) >= 0.999).mean()) if len(x) else 0.0, 2),
    }


def avisos_de(m: dict) -> list[str]:
    av = []
    if m["duracao_s"] < DURACAO_MIN:
        av.append("muito curto")
    if m["duracao_s"] > DURACAO_MAX:
        av.append("muito longo")
    if m["nivel_dbfs"] < NIVEL_MIN_DBFS:
        av.append("quase mudo")
    if m["clipping_pct"] > 100 * CLIPPING_MAX:
        av.append("áudio estourado (clipping)")
    return av


def conferir_ruido(linhas: list[dict]) -> None:
    """Indicativo: um áudio marcado com ruído deveria ter piso de ruído acima dos áudios silenciosos."""
    silenciosos = [l["piso_ruido_dbfs"] for l in linhas if l.get("ruido") == "nao"]
    if len(silenciosos) < 3:
        return
    base = float(np.median(silenciosos))
    for l in linhas:
        if l.get("ruido") == "sim" and l["piso_ruido_dbfs"] < base + 3:
            l["avisos"] = "; ".join([a for a in [l["avisos"], "ruído pouco perceptível (confira)"] if a])
        if l.get("ruido") == "nao" and l["piso_ruido_dbfs"] > base + 12:
            l["avisos"] = "; ".join([a for a in [l["avisos"], "mais ruidoso que os demais silenciosos (confira)"] if a])


# ------------------------------------------------------------------ códigos esperados
def codigos_esperados() -> dict[str, dict]:
    """código -> {pasta, arquivo, falante, ruido}. STT vem do manifesto; e2e, do conversas_e2e.csv."""
    esp = {}
    for l in ler_csv(AUDIOS / "manifesto_stt.csv"):
        esp[Path(l["arquivo"]).stem.lower()] = {"pasta": "stt", "arquivo": l["arquivo"],
                                                 "falante": l["falante"], "ruido": l["ruido"]}
    for l in ler_csv(TESTES / "conversas_e2e.csv"):
        esp[Path(l["arquivo"]).stem.lower()] = {"pasta": "e2e", "arquivo": l["arquivo"],
                                                 "falante": "", "ruido": "nao"}
    return esp


def identificar(entrada: Path, esperados: dict[str, dict]) -> tuple[dict[str, Path], list[str]]:
    """Liga cada código a um arquivo de `entrada`, pelo mapeamento.csv ou pelo nome do arquivo."""
    erros = []
    arquivos = {p.name.lower(): p for p in entrada.iterdir() if p.suffix.lower() in EXTENSOES}
    achados: dict[str, Path] = {}
    tratados: set[Path] = set()  # arquivos citados no mapeamento: não valem também pelo nome original
    mapa = entrada / "mapeamento.csv"
    if mapa.is_file():
        for l in ler_csv(mapa):
            orig, cod = l.get("original", "").lower(), l.get("codigo", "").lower()
            cod = Path(cod).stem
            if orig not in arquivos:
                erros.append(f"mapeamento.csv cita '{l.get('original')}', que não está em {entrada}")
                continue
            tratados.add(arquivos[orig])
            if cod in ("", "ignorar"):
                continue  # descartado de propósito (por exemplo, áudio repetido ou gravação errada)
            if cod not in esperados:
                erros.append(f"mapeamento.csv: código desconhecido '{l.get('codigo')}'")
            elif cod in achados:
                erros.append(f"código {cod} mapeado duas vezes")
            else:
                achados[cod] = arquivos[orig]
    for nome, p in arquivos.items():
        cod = p.stem.lower()
        if p not in tratados and cod in esperados and cod not in achados:
            achados[cod] = p
    usados = set(achados.values()) | tratados
    for p in arquivos.values():
        if p not in usados:
            erros.append(f"arquivo sem código (fora do mapeamento e do padrão de nome): {p.name}")
    return achados, erros


def ler_vozes(entrada: Path) -> dict[str, dict]:
    arq = entrada / "vozes.csv"
    return {l["falante"].upper(): l for l in ler_csv(arq)} if arq.is_file() else {}


# ------------------------------------------------------------------ fluxo principal
def organizar(entrada: Path, saida: Path = AUDIOS, so_conferir: bool = False, forcar: bool = False,
              evidencias: Path = EVIDENCIAS) -> dict:
    """Devolve {'problemas': [...], 'avisos': [...], 'linhas': [...], 'faltando': [...]}."""
    esperados = codigos_esperados()
    achados, problemas = identificar(entrada, esperados)
    vozes = ler_vozes(entrada)
    avisos, linhas = [], []
    vistos: dict[str, str] = {}  # impressão digital do áudio -> código

    falantes_usados = {esperados[c]["falante"] for c in achados if esperados[c]["pasta"] == "stt"}
    for f in sorted(falantes_usados):
        v = vozes.get(f)
        if not v:
            problemas.append(f"voz {f}: faltam dados em vozes.csv (faixa etária, sotaque, consentimento)")
        elif v.get("consentimento", "").lower() not in ("sim", "s"):
            problemas.append(f"voz {f}: sem consentimento registrado (coluna 'consentimento' = sim). Não processada")

    for cod, origem in sorted(achados.items()):
        e = esperados[cod]
        if e["pasta"] == "stt" and not (vozes.get(e["falante"], {}).get("consentimento", "").lower() in ("sim", "s")):
            continue  # voz sem consentimento: não entra
        destino = saida / e["pasta"] / e["arquivo"]
        try:
            x = carregar(origem)
        except Exception as erro:  # noqa: BLE001 - arquivo corrompido ou formato sem suporte
            problemas.append(f"{origem.name}: não foi possível ler ({type(erro).__name__}: {erro})")
            continue
        digest = hashlib.sha1(x.tobytes()).hexdigest()
        if digest in vistos:
            problemas.append(f"{origem.name} ({cod}) é o MESMO áudio de {vistos[digest]}: uma das gravações está repetida")
            continue
        vistos[digest] = cod
        m = medir(x)
        linhas.append({"codigo": cod, "original": origem.name, "destino": f"{e['pasta']}/{e['arquivo']}",
                       "falante": e["falante"], "ruido": e["ruido"], **m, "avisos": "; ".join(avisos_de(m))})
        if not so_conferir:
            if destino.exists() and not forcar:
                problemas.append(f"{e['pasta']}/{e['arquivo']} já existe (use --forcar para sobrescrever)")
                continue
            gravar_wav(destino, x)
    conferir_ruido(linhas)

    faltando = sorted(c for c in esperados if c not in achados)
    if not so_conferir and linhas:
        escrever_csv(evidencias / "audios_qualidade.csv", linhas)
        if any(l["destino"].startswith("stt/") for l in linhas):  # só mexe no manifesto se houve áudio de STT
            _preencher_manifesto(saida / "manifesto_stt.csv", vozes)
    return {"problemas": problemas, "avisos": [f"{l['destino']}: {l['avisos']}" for l in linhas if l["avisos"]],
            "linhas": linhas, "faltando": faltando}


def _preencher_manifesto(caminho: Path, vozes: dict[str, dict]) -> None:
    linhas = ler_csv(caminho)
    for l in linhas:
        v = vozes.get(l["falante"].upper())
        if v:
            l["faixa_etaria"] = v.get("faixa_etaria", "") or l["faixa_etaria"]
            l["sotaque"] = v.get("sotaque", "") or l["sotaque"]
    escrever_csv(caminho, linhas, ["arquivo", "falante", "ruido", "faixa_etaria", "sotaque", "referencia"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", type=Path, default=AUDIOS / "entrada")
    ap.add_argument("--so-conferir", action="store_true", help="não grava nada, só relata")
    ap.add_argument("--forcar", action="store_true", help="sobrescreve áudios já organizados")
    a = ap.parse_args()
    if not a.entrada.is_dir():
        print(f"Pasta de entrada não existe: {a.entrada}\nCrie-a e coloque lá os áudios, o vozes.csv e, se preciso, "
              f"o mapeamento.csv (modelos em {AUDIOS / 'modelos'}).")
        return 2
    r = organizar(a.entrada, so_conferir=a.so_conferir, forcar=a.forcar)
    stt = sum(1 for l in r["linhas"] if l["destino"].startswith("stt/"))
    e2e = sum(1 for l in r["linhas"] if l["destino"].startswith("e2e/"))
    print(f"Áudios lidos: {stt} de 20 (STT) e {e2e} de 30 (conversas)" + (" [só conferência]" if a.so_conferir else ""))
    for t, itens in (("PROBLEMAS", r["problemas"]), ("AVISOS DE QUALIDADE", r["avisos"])):
        if itens:
            print(f"\n{t}:\n  " + "\n  ".join(itens))
    if r["faltando"]:
        from montar_stt_das_conversas import LIMPOS  # import tardio: o montador importa este módulo
        das_conversas = [c for c in r["faltando"] if c in LIMPOS]
        faltam = [c for c in r["faltando"] if c not in LIMPOS]
        print(f"\nAinda faltam {len(faltam)}: " + (", ".join(faltam) or "nada"))
        if das_conversas:
            print(f"Outros {len(das_conversas)} áudios do STT (stt_01, stt_02...) não precisam ser gravados: vêm das conversas "
                  "pelo testes/montar_stt_das_conversas.py")
    return 1 if r["problemas"] else 0


if __name__ == "__main__":
    sys.exit(main())
