"""Texto ATRÁS de objeto numa reconstrução: onde a referência não mostra tinta (objeto na frente), mascara o texto.

    python3 ocultar.py pasta_reconstrucao [--limiar 0.88]

Para cada linha (medidas.json + alvos.json): compara a tinta da cor da linha na referência com a do editavel.png.
Cobertura (tinta ref / tinta remake) < limiar = parte da palavra está escondida -> gera máscara (branco = mostra) a
partir da tinta da referência dilatada 3 px, só dentro da caixa da linha, e aplica como máscara de camada no PSD
(continua editável: dá para pintar a máscara). Remonta e salva editavel.psd/png.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))


def tinta(img, cores, caixa, tol=70):
    x1, y1, x2, y2 = caixa; a = np.asarray(img.crop(caixa).convert("RGB")).astype(float); m = np.zeros(a.shape[:2], bool)
    for c in cores:
        al = np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float); m |= np.sqrt(((a - al) ** 2).sum(2)) < tol
    return m


def main():
    pasta = os.path.abspath(sys.argv[1]); lim = float(sys.argv[sys.argv.index("--limiar") + 1]) if "--limiar" in sys.argv else 0.88
    med = json.load(open(os.path.join(pasta, "medidas.json"))); alv = json.load(open(os.path.join(pasta, "alvos.json")))
    # mede sempre sobre a montagem SEM máscaras (rodar duas vezes não pode achar "nada escondido")
    subprocess.run([sys.executable, os.path.join(AQUI, "montar.py"), os.path.join(pasta, "arte.jsx"), f"SAIDA={pasta}", f"PASTA={pasta}"], capture_output=True, text=True)
    rem = Image.open(os.path.join(pasta, "editavel.png")).convert("RGB"); W, H = rem.size
    ref = Image.open(med["ref"]).convert("RGB").resize((W, round(Image.open(med["ref"]).height * W / Image.open(med["ref"]).width)))
    ref = ref.crop((0, 0, W, H)) if ref.height >= H else ref
    aplicar = []
    for it in med["itens"]:
        n = it["nome"]; a = alv.get(n)
        if not a: continue
        cx = (max(0, a["x"] - 6), max(0, a["y"] - 6), min(W, a["x"] + a["w"] + 6), min(H, a["y"] + a["h"] + 6))
        cores = it["cor"].split(","); mr, mm = tinta(ref, cores, cx), tinta(rem, cores, cx)
        cob = mr.sum() / max(1, mm.sum())
        print(f"{n}: cobertura {cob:.2f}", flush=True)
        if cob >= lim or mm.sum() < 50:
            continue
        # abertura: tira traços finos (contorno desenhado sobre o objeto) antes de dilatar; senão a máscara sai pontilhada
        esp = max(3, int(round((a["h"] * 0.06)))) | 1
        vis = Image.fromarray((mr * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(esp)).filter(ImageFilter.MaxFilter(esp)).filter(ImageFilter.MaxFilter(7))
        full = Image.new("L", (W, H), 255); full.paste(Image.new("L", (cx[2] - cx[0], cx[3] - cx[1]), 0), cx[:2]); full.paste(vis, cx[:2])
        p = os.path.join(pasta, f"mascara_{n}.png"); rgba = Image.new("RGBA", (W, H), (255, 255, 255, 0)); rgba.putalpha(full); rgba.save(p)
        # contorno desenhado sobre o objeto (o "fantasma" da letra na tela do celular): traço fino que a abertura tirou
        aberto = np.asarray(Image.fromarray((mr * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(esp)).filter(ImageFilter.MaxFilter(esp))) > 0
        fino = mr & ~aberto
        pc = None
        if fino.sum() > 80:
            oc = Image.new("L", (W, H), 0); oc.paste(Image.fromarray(((~np.asarray(vis.convert("L")).astype(bool)) * 255).astype(np.uint8)), cx[:2])
            pc = os.path.join(pasta, f"contorno_{n}.png"); r2 = Image.new("RGBA", (W, H), (255, 255, 255, 0)); r2.putalpha(oc); r2.save(pc)
            print(f"   contorno sobre o objeto: {int(fino.sum())} px", flush=True)
        aplicar.append((n, p, pc, cores[0]))
    if not aplicar:
        print("nenhum texto escondido"); return
    js = open(os.path.join(pasta, "arte.jsx")).read().rsplit("Y.salvar(", 1)
    bloco = "".join((f'Y.contornoOculto("{n} ", {json.dumps(pc)}, {json.dumps(cor)});\n' if pc else "") + f'Y.mascaraDeImagem("{n} ", {json.dumps(p)});\n' for n, p, pc, cor in aplicar)
    nova = js[0] + "// texto atrás do objeto (ocultar.py): máscara pela tinta visível na referência\n" + bloco + "Y.salvar(" + js[1]
    open(os.path.join(pasta, "arte_ocultar.jsx"), "w").write(nova)
    r = subprocess.run([sys.executable, os.path.join(AQUI, "montar.py"), os.path.join(pasta, "arte_ocultar.jsx"), f"SAIDA={pasta}", f"PASTA={pasta}"], capture_output=True, text=True)
    print((r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else "?", "| máscaras:", [x[0] for x in aplicar])


if __name__ == "__main__":
    main()
