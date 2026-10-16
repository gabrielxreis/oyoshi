"""Mede a caixa de um objeto/pessoa na referência (para o remake encaixar a foto no mesmo lugar e tamanho).

    .venv/bin/python medir_objeto.py ref.png --regiao x1 y1 x2 y2 [--limiar 45] [--largura 1080]

- `--ps "the camera"` (RECOMENDADO para objeto/pessoa): abre a referência no Photoshop, seleciona por IA
  (selection_select_by_prompt, prompt em inglês; vários separados por "|") e devolve a caixa da seleção.
  Pega partes escuras do objeto e ignora brilho/sombra em volta, onde o limiar de cor falha.
- Sem --ps: o fundo é estimado pela cor da borda da região; pixels que se afastam dele mais que --limiar viram objeto.
  Fica só o maior bloco conectado (sem partículas, brilhos soltos, textos pequenos).
- Saída em pixels do documento: {"x","y","w","h"} + prévia *.objeto.png. No arte.jsx:
  Y.colocar(foto, nome, grupo, {x,y,w,h}, "cobrir"|"conter") e depois Y.recortar; ou medir o remake também e
  corrigir escala/posição pela diferença (o recorte do remake tem a mesma lógica de caixa).
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def maior_bloco(m):
    from collections import deque
    h, w = m.shape; vis = np.zeros_like(m); melhor = None; tam = 0
    ys, xs = np.where(m)
    for y0, x0 in zip(ys[::7], xs[::7]):
        if vis[y0, x0]:
            continue
        q = deque([(y0, x0)]); vis[y0, x0] = True; pts = []
        while q:
            y, x = q.popleft(); pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not vis[yy, xx]:
                    vis[yy, xx] = True; q.append((yy, xx))
        if len(pts) > tam:
            tam = len(pts); melhor = pts
    return melhor


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("img"); ap.add_argument("--regiao", type=int, nargs=4)
    ap.add_argument("--limiar", type=float, default=45); ap.add_argument("--largura", type=int, default=1080)
    ap.add_argument("--escala-doc", action="store_true", help="regiao já em pixels do documento (1080)")
    ap.add_argument("--ps", help='prompt(s) em inglês para a seleção por IA do Photoshop, ex.: "the camera|the lens"')
    a = ap.parse_args()
    im = Image.open(a.img).convert("RGB"); k = a.largura / im.width
    if a.ps:
        import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ps_lib as PS
        lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jsx", "yoshi.jsx")
        r = PS.js(f"""$.evalFile({json.dumps(lib)}); var d = app.open(new File({json.dumps(os.path.abspath(a.img))})); Y.usar(d);
var out; try {{ Y.selecionarPorPrompt(d.activeLayer, {json.dumps(a.ps.split("|"))});
  var bb = d.selection.bounds; out = [bb[0].as("px"), bb[1].as("px"), bb[2].as("px"), bb[3].as("px")].join(",");
}} catch (e) {{ out = "ERRO " + e; }} d.close(SaveOptions.DONOTSAVECHANGES); out""", timeout=300)
        if r.startswith("ERRO"):
            print(r); return
        bx1, by1, bx2, by2 = [float(v) for v in r.split(",")]
        print(json.dumps({"x": round(bx1 * k), "y": round(by1 * k), "w": round((bx2 - bx1) * k), "h": round((by2 - by1) * k)}))
        return
    if not a.regiao:
        ap.error("--regiao é obrigatória sem --ps")
    x1, y1, x2, y2 = [round(v / k) for v in a.regiao] if a.escala_doc else a.regiao
    sub = np.asarray(im.crop((x1, y1, x2, y2)).filter(ImageFilter.MedianFilter(3)), dtype=np.float32)
    borda = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]); fundo = np.median(borda, axis=0)
    m = np.sqrt(((sub - fundo) ** 2).sum(axis=2)) > a.limiar
    pts = maior_bloco(m)
    if not pts:
        print("{}"); return
    ys = np.array([p[0] for p in pts]); xs = np.array([p[1] for p in pts])
    bx, by, bw, bh = xs.min() + x1, ys.min() + y1, xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    res = {"x": round(bx * k), "y": round(by * k), "w": round(bw * k), "h": round(bh * k)}
    prev = im.copy(); ImageDraw.Draw(prev).rectangle([bx, by, bx + bw, by + bh], outline=(255, 0, 0), width=2)
    saida = os.path.splitext(a.img)[0] + ".objeto.png"; prev.save(saida)
    print(json.dumps(res)); print(saida)


if __name__ == "__main__":
    main()
