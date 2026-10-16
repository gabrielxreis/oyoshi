"""Comparador de fonte local: descobre qual fonte instalada/ativada mais se parece com uma linha de texto da referência.

    ~/.claude/skills/oyoshi/.venv/bin/python comparar_fonte.py imagem.png X1 Y1 X2 Y2 "TEXTO EXATO" [--filtro Good,Anton,Bebas] [--top 12]

- Renderiza o MESMO texto em cada fonte (sistema, ~/Library/Fonts e fontes ativadas pelo Adobe Fonts) e compara
  com o recorte da referência: forma (IoU dos pixels depois de igualar altura e largura) + proporção largura/altura.
- Devolve o ranking (PostScript name, nota) e salva uma folha `*.comparacao.png` com a referência em cima e as
  melhores candidatas embaixo (conferir com Read).
- Use junto com o reconhecer_fonte.py (Adobe): o Adobe sugere, ative as sugeridas da nuvem, e este aqui decide pela largura.
- `--filtro`: só fontes cujo nome contém algum dos termos (mais rápido). Sem filtro varre tudo (~1-3 min).
Dica: TEXTO EXATO tem que ser o que aparece no recorte (maiúsculas/minúsculas e acentos iguais).
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
from fontTools.ttLib import TTCollection, TTFont
from PIL import Image, ImageDraw, ImageFont, ImageOps

CACHE = os.path.expanduser("~/.claude/skills/oyoshi/.venv/fontes_indice.json")
PASTAS = ["/System/Library/Fonts", "/Library/Fonts", os.path.expanduser("~/Library/Fonts"),
          os.path.expanduser("~/Library/Application Support/Adobe/CoreSync/plugins/livetype")]


def indice():
    """Mapa PostScript name -> (arquivo, índice dentro do .ttc). Fica em cache; refaz se aparecerem arquivos novos."""
    arquivos = []
    for p in PASTAS:
        for raiz, _, nomes in os.walk(p):  # os.walk enxerga as pastas ocultas do Adobe Fonts (.r/.12345.otf)
            for n in nomes:
                f = os.path.join(raiz, n)
                if f.lower().endswith((".ttf", ".otf", ".ttc")):
                    arquivos.append(f)
    try:
        c = json.load(open(CACHE))
        if c.get("n") == len(arquivos):
            return c["fontes"]
    except Exception:
        pass
    fontes = {}
    for f in arquivos:
        try:
            faces = TTCollection(f).fonts if f.lower().endswith(".ttc") else [TTFont(f, lazy=True)]
        except Exception:
            continue
        for i, ft in enumerate(faces):
            try:
                ps = ft["name"].getDebugName(6)
                if ps and ps not in fontes and not ps.startswith("."):
                    cm = ft.getBestCmap() or {}
                    cob = "".join(chr(c) for c in cm if 32 <= c < 0x180)
                    fontes[ps] = [f, i, cob]
            except Exception:
                pass
    json.dump({"n": len(arquivos), "fontes": fontes}, open(CACHE, "w"))
    return fontes


def binarizar(im):
    """Texto vira branco (255) sobre preto. Decide a cor do texto pela minoria de pixels."""
    g = np.asarray(ImageOps.grayscale(im), dtype=np.float32)
    borda = np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]]).mean()   # o fundo é a cor das bordas
    lim = (g.max() + g.min()) / 2
    claro = g > lim
    return ~claro if borda > lim else claro


def apertar(m):
    ys, xs = np.where(m)
    if len(xs) == 0:
        return None
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def render(caminho, idx, texto, alt=120):
    try:
        fnt = ImageFont.truetype(caminho, alt, index=idx)
    except Exception:
        return None
    try:
        bx = fnt.getbbox(texto)
    except Exception:
        return None
    w, h = bx[2] - bx[0] + 20, bx[3] - bx[1] + 20
    if w <= 0 or h <= 0 or w > 8000:
        return None
    im = Image.new("L", (w, h), 0)
    try:
        ImageDraw.Draw(im).text((10 - bx[0], 10 - bx[1]), texto, font=fnt, fill=255)
    except Exception:
        return None
    return apertar(np.asarray(im) > 128)


def nota(ref, cand, H=64):
    if cand is None or cand.shape[0] < 4:
        return 0, 0
    ar_ref, ar_c = ref.shape[1] / ref.shape[0], cand.shape[1] / cand.shape[0]
    larg = min(ar_ref, ar_c) / max(ar_ref, ar_c)          # 1 = mesma proporção (largura)
    W = max(8, int(H * ar_ref))
    a = np.asarray(Image.fromarray(ref.astype(np.uint8) * 255).resize((W, H))) > 128
    b = np.asarray(Image.fromarray(cand.astype(np.uint8) * 255).resize((W, H))) > 128
    iou = (a & b).sum() / max(1, (a | b).sum())
    return iou * 0.65 + larg * 0.35, larg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("img"); ap.add_argument("x1", type=int); ap.add_argument("y1", type=int)
    ap.add_argument("x2", type=int); ap.add_argument("y2", type=int); ap.add_argument("texto")
    ap.add_argument("--filtro", default="")
    ap.add_argument("--cor", default="", help="cor do texto na referência (#RRGGBB): pega só os pixels perto dessa cor (use quando há foto/objeto atrás ou na frente)")
    ap.add_argument("--tol", type=int, default=70); ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()
    crop = Image.open(a.img).convert("RGB").crop((a.x1, a.y1, a.x2, a.y2))
    if a.cor:
        px = np.asarray(crop, dtype=np.float32); m = np.zeros(px.shape[:2], dtype=bool)
        for c in a.cor.split(","):  # várias cores: "#FFFFFF,#3ED6A6" (linha com palavra destacada)
            c = c.strip(); alvo = np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)
            m |= np.sqrt(((px - alvo) ** 2).sum(axis=2)) < a.tol
        ref = apertar(m)
    else:
        ref = apertar(binarizar(crop))
    fontes = indice()
    termos = [t.strip().lower() for t in a.filtro.split(",") if t.strip()]
    res = []
    precisa = set(a.texto) - {" ", "\n"}
    for ps, (f, i, cob) in fontes.items():
        if termos and not any(t in ps.lower() for t in termos):
            continue
        if not precisa.issubset(set(cob)):
            continue
        n, larg = nota(ref, render(f, i, a.texto))
        if n > 0:
            res.append((n, larg, ps, f, i))
    res.sort(reverse=True)
    top = res[:a.top]
    for n, larg, ps, f, i in top:
        print(f"{n:.3f}  largura {larg:.2f}  {ps}")
    # folha de comparação
    linhas = [Image.fromarray(ref.astype(np.uint8) * 255)]
    for n, larg, ps, f, i in top[:8]:
        linhas.append(Image.fromarray(render(f, i, a.texto).astype(np.uint8) * 255))
    H = 60; ims = [im.resize((max(1, int(im.width * H / im.height)), H)) for im in linhas]
    W = max(im.width for im in ims) + 360
    folha = Image.new("L", (W, (H + 14) * len(ims)), 0); d = ImageDraw.Draw(folha)
    rot = ["REFERÊNCIA"] + [f"{t[0]:.2f} {t[2]}" for t in top[:8]]
    for k, im in enumerate(ims):
        folha.paste(im, (350, k * (H + 14))); d.text((6, k * (H + 14) + 20), rot[k], fill=200)
    saida = os.path.splitext(a.img)[0] + ".comparacao.png"
    folha.save(saida); print(saida)


if __name__ == "__main__":
    main()
