import subprocess, json, re, sys
pdf = sys.argv[1]
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
pags = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-"], capture_output=True, text=True).stdout for i in range(1, n+1)]
norm = lambda s: re.sub(r"\s+", " ", s)
ini = max(i for i, p in enumerate(pags) if "SUMÁRIO" in p) + 1
chaves = json.load(open("chaves.json"))
out = {}
for c in chaves:
    k = norm(c)
    for i in range(ini, n):
        t = norm(pags[i])
        # heading: no início de linha
        if k[:60] in t:
            out[c] = i  # página do PDF (1-based) - 1 = número ABNT (capa não conta)
            break
    else:
        print("NAO ACHOU", c)
json.dump(out, open("paginas.json", "w"), ensure_ascii=False, indent=1)
print("paginas pdf:", n, "textual de", ini+1-1, "a", n-1)
