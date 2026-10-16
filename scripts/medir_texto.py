"""Mede onde está cada linha de texto numa referência (para o remake bater pixel a pixel).

    .venv/bin/python medir_texto.py ref.png --cor "#FFF9ED" [--tol 60] [--largura 1080] [--regiao x1 y1 x2 y2] [--min-alt 8]

- Pega os pixels da cor do texto (tolerância em distância RGB), agrupa em LINHAS pela projeção horizontal e devolve
  a caixa justa de cada linha (x, y, w, h) já convertida para a largura do documento final (padrão 1080).
- `--regiao` limita a busca (em pixels da referência ORIGINAL), útil para separar título de apoio.
- Saída: JSON (uma lista) + prévia `*.medidas.png` com as caixas desenhadas para conferir.
Use as caixas no arte.jsx com `alvo: {x, y, w, h}` em Y.texto: o motor ajusta tamanho e posição até bater.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("img"); ap.add_argument("--cor", required=True); ap.add_argument("--tol", type=int, default=60)
    ap.add_argument("--largura", type=int, default=1080); ap.add_argument("--regiao", type=int, nargs=4)
    ap.add_argument("--min-alt", type=int, default=6); ap.add_argument("--juntar", type=int, default=3,
                    help="linhas separadas por até N px vazios viram uma só")
    a = ap.parse_args()
    im = Image.open(a.img).convert("RGB"); W0, H0 = im.size
    px = np.asarray(im, dtype=np.float32)
    alvo = np.array([int(a.cor[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)
    m = np.sqrt(((px - alvo) ** 2).sum(axis=2)) < a.tol
    if a.regiao:
        x1, y1, x2, y2 = a.regiao; z = np.zeros_like(m); z[y1:y2, x1:x2] = m[y1:y2, x1:x2]; m = z
    linhas_on = m.sum(axis=1) > max(2, m.shape[1] * 0.004)
    # agrupa faixas verticais contínuas
    faixas, ini, vazio = [], None, 0
    for y, on in enumerate(linhas_on):
        if on:
            if ini is None: ini = y
            vazio = 0
        elif ini is not None:
            vazio += 1
            if vazio > a.juntar:
                faixas.append((ini, y - vazio + 1)); ini = None; vazio = 0
    if ini is not None: faixas.append((ini, len(linhas_on)))
    k = a.largura / W0; res = []
    prev = im.copy(); d = ImageDraw.Draw(prev)
    for (ya, yb) in faixas:
        if yb - ya < a.min_alt: continue
        cols = np.where(m[ya:yb].sum(axis=0) > 0)[0]
        if len(cols) == 0: continue
        xa, xb = cols.min(), cols.max() + 1
        res.append({"x": round(xa * k), "y": round(ya * k), "w": round((xb - xa) * k), "h": round((yb - ya) * k)})
        d.rectangle([xa, ya, xb, yb], outline=(255, 0, 0), width=2)
    saida = os.path.splitext(a.img)[0] + ".medidas.png"; prev.save(saida)
    print(json.dumps(res)); print(saida)


if __name__ == "__main__":
    main()
