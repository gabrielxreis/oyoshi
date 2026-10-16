"""Ciclo fechado "idêntico": mede a referência, monta, MEDE O REMAKE com a mesma regra e corrige os alvos até bater.

    python3 ciclo.py pasta_da_arte MARCA=... [--voltas 3]

A pasta tem `arte.jsx` e `medidas.json`:
    {"ref": "caminho/ref.png",
     "itens": [{"nome": "TITULO 1", "cor": "#FFFFFF,#3ED6A6", "regiao": [x1, y1, x2, y2]}, ...]}
  - regiao em pixels da REFERÊNCIA (a mesma usada no medir_texto.py), uma linha de texto por item.
  - "texto": o conteúdo da linha (decide se confere pelo corpo da maiúscula ou pela faixa do x).
O ciclo grava `alvos.json` ({nome: {x,y,w,h,cy,ch,xy,xh,cor}}) que o arte.jsx lê com
    var ALV = Y.lerJSON(PASTA + "/alvos.json");   ...  alvo: ALV["TITULO 1"]
Volta 1: alvos = medida da referência. Depois de montar, mede o remake (mesma cor, mesma região convertida) e
corrige cada alvo pelo erro (alvo += ref - remake), cancelando vieses do Photoshop (borda antisserrilhada na caixa
da camada, métrica da fonte). Para quando o erro máximo fica <= 1 px ou acabam as voltas.
"""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(AQUI, "..", ".venv", "bin", "python")
CAMPOS = ("x", "y", "w", "h", "cy", "ch", "xy", "xh")


def usados(texto, r):
    """Campos que o Y.encaixarTexto usa: caixa alta encaixa pelo corpo (cy/ch), minúscula pela faixa do x (xy/xh)."""
    if texto and texto == texto.upper():
        return ("x", "w", "cy", "ch")
    if texto:
        return ("x", "w", "xy", "xh")
    return ("x", "w", "cy", "ch", "xy", "xh")


def medir(img, cor, regiao):
    out = subprocess.run([PY, os.path.join(AQUI, "medir_texto.py"), img, "--cor", cor, "--regiao", *map(str, regiao)],
                         capture_output=True, text=True).stdout.splitlines()
    linhas = json.loads(out[0]) if out else []
    if not linhas:
        return None
    return max(linhas, key=lambda d: d["w"] * d["h"])   # a linha principal da região


def main():
    pasta = os.path.abspath(sys.argv[1]); extras = [a for a in sys.argv[2:] if "=" in a and not a.startswith("--")]
    voltas = int(sys.argv[sys.argv.index("--voltas") + 1]) if "--voltas" in sys.argv else 3
    cfg = json.load(open(os.path.join(pasta, "medidas.json")))
    from PIL import Image
    wref = Image.open(cfg["ref"]).width
    ref = {}
    for it in cfg["itens"]:
        m = medir(cfg["ref"], it["cor"], it["regiao"])
        if not m:
            print("sem medida na referência:", it["nome"]); continue
        ref[it["nome"]] = m
    alvos = {n: dict(v) for n, v in ref.items()}
    for volta in range(1, voltas + 1):
        json.dump(alvos, open(os.path.join(pasta, "alvos.json"), "w"), ensure_ascii=False, indent=1)
        r = subprocess.run([sys.executable, os.path.join(AQUI, "montar.py"), os.path.join(pasta, "arte.jsx"),
                            f"SAIDA={pasta}", f"PASTA={pasta}", *extras], capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-800:], r.stderr[-800:]); return
        png = [f for f in os.listdir(pasta) if f.endswith(".png") and not any(s in f for s in (".medidas", "sobrepos", ".objeto", ".mascara"))]
        png = max((os.path.join(pasta, f) for f in png), key=os.path.getmtime)
        wrm = Image.open(png).width; k = wrm / wref
        pior = 0; print(f"volta {volta}:")
        for it in cfg["itens"]:
            n = it["nome"]
            if n not in ref:
                continue
            # no remake mede só em volta da caixa da referência (+14 px): foto/mão diferente perto não contamina
            R_ = ref[n]; rg = [max(0, round(R_["x"] - 14)), max(0, round(R_["y"] - 14)), round(R_["x"] + R_["w"] + 14), round(R_["y"] + R_["h"] + 14)]
            m = medir(png, it.get("cor_remake", it["cor"]), rg)
            if not m:
                print(f"  {n}: não achei no remake"); continue
            usa = usados(it.get("texto", ""), ref[n])
            err = {c: ref[n][c] - m[c] for c in usa if c in m and c in ref[n]}
            e = max(abs(v) for v in err.values()); pior = max(pior, e)
            print(f"  {n:<22} erro máx {e:>3} px  " + " ".join(f"{c}{v:+d}" for c, v in err.items() if v))
            for c, v in err.items():
                alvos[n][c] = alvos[n][c] + v
        if pior <= 1:
            print("bateu (<= 1 px)"); break
    json.dump(alvos, open(os.path.join(pasta, "alvos.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
