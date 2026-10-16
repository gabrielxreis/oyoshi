"""Imagem chapada -> PSD editável: fundo limpo (texto apagado com sensível ao conteúdo) + textos vivos medidos.

    python3 reconstruir.py ref.png pasta_saida [--filtro "Montserrat,GoodPro,Owners,Franklin"] [--largura 1080]

1. OCR nativo do macOS (scripts/swift/ocr, Vision): texto e caixa de cada linha.
2. Por linha: cor da tinta (o grupo de pixels de maior contraste com a borda da caixa), medidas pelo medir_texto
   (x, w, cy/ch ou xy/xh) e fonte pelo comparar_fonte (filtro opcional = mais rápido e mais certo).
3. Gera em pasta_saida: `medidas.json` (para o ciclo.py), `arte.jsx` (fundo limpo + uma camada por linha com alvo)
   e roda o ciclo: monta, mede o remake, corrige até <= 1 px.
Limites: linha com duas cores sai com a cor principal (ajustar `faixas` à mão); foto continua a da referência
(é um PSD da referência, não um remake com foto nova).
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__)); PY = os.path.join(AQUI, "..", ".venv", "bin", "python")


def cor_tinta(im, cx):
    x1, y1, x2, y2 = cx; a = np.asarray(im.crop((x1, y1, x2, y2)).convert("RGB")).reshape(-1, 3).astype(float)
    sub = np.asarray(im.crop((x1, y1, x2, y2)).convert("RGB")).astype(float)
    borda = np.median(np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]), 0)
    d = np.sqrt(((a - borda) ** 2).sum(1)); tinta = a[d >= np.percentile(d, 85)]
    return "#%02X%02X%02X" % tuple(int(v) for v in np.median(tinta, 0)), borda


def faixas_palavras(im, linha, cor_linha, fonte_neg):
    """Negrito e cor por palavra: densidade de tinta (negrito tem ~25%+ mais tinta que a média da linha) e cor
    da tinta muito diferente da principal (palavra em vermelho). Devolve faixas para o Y.texto."""
    pal = linha.get("palavras") or []
    if len(pal) < 2:
        return [], cor_linha
    info = []
    for w in pal:
        cx = (w["x"], w["y"], w["x"] + max(2, w["w"]), w["y"] + max(2, w["h"]))
        sub = np.asarray(im.crop(cx).convert("RGB")).astype(float)
        if sub.size == 0: info.append(None); continue
        borda = np.median(np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]), 0)
        d = np.sqrt(((sub - borda) ** 2).sum(2)); tinta = d > max(60, d.max() * 0.5)
        dens = tinta.mean(); cor = np.median(sub[tinta], 0) if tinta.any() else borda
        info.append((dens, cor))
    ok = [x for x in info if x]
    # negrito: maior salto entre densidades ordenadas (só se o salto for >= 22%)
    ds = sorted(x[0] for x in ok); corte = None
    if len(ds) > 1:
        saltos = [(ds[i + 1] / max(1e-6, ds[i]), i) for i in range(len(ds) - 1)]; s_, i_ = max(saltos)
        if s_ >= 1.22: corte = (ds[i_] + ds[i_ + 1]) / 2
    # cor-base = a cor da MAIORIA das palavras (pesada pela largura), não a mediana da linha (o vermelho puxava)
    larguras = [w["w"] for w, x in zip(pal, info) if x]; cores = [x[1] for x in ok]
    def grupo(c): return sum(lw for lw, o in zip(larguras, cores) if np.sqrt(((o - c) ** 2).sum()) < 60)
    base = max(cores, key=grupo); dens_med = None
    fx = []
    for w, x in zip(pal, info):
        if not x: continue
        f = {"de": w["i"], "ate": w["i"] + w["n"] + (1 if w["i"] + w["n"] < len(linha["texto"]) and linha["texto"][w["i"] + w["n"]] in ".,!?:;" else 0)}
        if corte is not None and x[0] > corte and fonte_neg: f["fonte"] = fonte_neg
        if np.sqrt(((x[1] - base) ** 2).sum()) > 70: f["cor"] = "#%02X%02X%02X" % tuple(int(v) for v in x[1])
        if len(f) > 2: fx.append(f)
    # junta palavras vizinhas com o mesmo estilo (inclui o espaço entre elas)
    out = []
    for f in fx:
        if out and out[-1].get("fonte") == f.get("fonte") and out[-1].get("cor") == f.get("cor") and f["de"] - out[-1]["ate"] <= 1:
            out[-1]["ate"] = f["ate"]
        else:
            out.append(dict(f))
    return out, "#%02X%02X%02X" % tuple(int(v) for v in base)


def ui_instagram(W, H):
    """Interface do Instagram que vem no print: seta do carrossel (direita/esquerda, meio) e bolinhas (base)."""
    return [[round(W * 0.915), round(H * 0.465), W, round(H * 0.535)], [0, round(H * 0.465), round(W * 0.085), round(H * 0.535)],
            [round(W * 0.40), round(H * 0.965), round(W * 0.60), H]]


def roda(*cmd, timeout=600):
    return subprocess.run(list(cmd), capture_output=True, text=True, timeout=timeout).stdout


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("pasta"); ap.add_argument("--filtro", default="")
    ap.add_argument("--largura", type=int, default=1080); ap.add_argument("--sem-ciclo", action="store_true")
    ap.add_argument("--fonte-texto", default="", help="fonte do texto pequeno (da marca), ex. Montserrat-Regular")
    ap.add_argument("--fonte-negrito", default="", help="negrito do texto pequeno, ex. Montserrat-Bold")
    ap.add_argument("--pequeno", type=int, default=56, help="linha com altura < N px (doc) usa --fonte-texto")
    ap.add_argument("--logos", default="", help="textos que são logo (ficam como imagem), ex. Calverstone")
    ap.add_argument("--limpar-ui", action="store_true", help="apaga seta e bolinhas do carrossel do Instagram (print)")
    ap.add_argument("--nota-min", type=float, default=0.62, help="abaixo disso a linha fica como imagem (logo)")
    a = ap.parse_args(); os.makedirs(a.pasta, exist_ok=True)
    im = Image.open(a.ref).convert("RGB"); W0, H0 = im.size; k = a.largura / W0; H = round(H0 * k)
    linhas = json.loads(roda(os.path.join(AQUI, "swift", "ocr"), a.ref))
    itens, camadas = [], []
    for i, l in enumerate(linhas):
        txt = l["texto"].strip()
        if not txt or l["conf"] < 0.4: continue
        if any(txt.lower() == g.strip().lower() for g in a.logos.split(",") if g.strip()):
            print(f"{txt:<30} logo: fica como IMAGEM", flush=True); continue
        pad = max(3, int(l["h"] * 0.35)); cx = (max(0, l["x"] - pad), max(0, l["y"] - pad), min(W0, l["x"] + l["w"] + pad), min(H0, l["y"] + l["h"] + pad))
        cor, _ = cor_tinta(im, cx)
        nome = f"L{i + 1:02d} {txt[:22]}"
        pequeno = l["h"] * k < a.pequeno
        fonte, nota = a.fonte_texto, 1.0
        pj = max(2, int(l["h"] * 0.08)); cj = (max(0, l["x"] - pj), max(0, l["y"] - pj), min(W0, l["x"] + l["w"] + pj), min(H0, l["y"] + l["h"] + pj))
        out = "" if pequeno and a.fonte_texto else roda(PY, os.path.join(AQUI, "comparar_fonte.py"), a.ref, *map(str, cj), txt, "--cor", cor, "--top", "3", *(["--filtro", a.filtro] if a.filtro else []))
        if out.strip():
            fonte = out.strip().splitlines()[0].split()[-1]; nota = float(out.split()[0])
        fx, cor_base = faixas_palavras(im, l, cor, a.fonte_negrito if pequeno else None) if len(l.get("palavras") or []) > 1 else ([], cor)
        if fx or cor_base != cor:
            cor = cor_base; fx = [f for f in fx if f.get("fonte") or (f.get("cor") and np.sqrt(sum((int(f["cor"][i:i + 2], 16) - int(cor[i:i + 2], 16)) ** 2 for i in (1, 3, 5))) > 70)]
            for f in fx:
                if f.get("cor") and np.sqrt(sum((int(f["cor"][i:i + 2], 16) - int(cor[i:i + 2], 16)) ** 2 for i in (1, 3, 5))) <= 70: f.pop("cor")
        if nota < a.nota_min:   # nenhuma fonte parecida: é logo/lettering -> fica como imagem do fundo
            print(f"{txt[:30]:<30} nota {nota:.2f}: fica como IMAGEM (logo/lettering)", flush=True); continue
        print(f"{nome:<30} cor {cor}  fonte {fonte} ({nota:.2f})", flush=True)
        cores_med = ",".join([cor] + sorted({f["cor"] for f in fx if f.get("cor")}))   # mede a linha com TODAS as cores dela
        itens.append({"nome": nome, "texto": txt, "cor": cores_med, "regiao": list(cx)})
        camadas.append({"nome": nome, "txt": txt, "cor": cor, "fonte": fonte, "faixas": fx, "caixa": [round(v * k) for v in cx]})
    json.dump({"ref": os.path.abspath(a.ref), "itens": itens}, open(os.path.join(a.pasta, "medidas.json"), "w"), ensure_ascii=False, indent=1)
    js = [f"// Reconstruído automaticamente de {os.path.basename(a.ref)} (reconstruir.py): fundo limpo + textos vivos medidos.",
          f"var W = {a.largura}, H = {H}; Y.doc(W, H, {json.dumps(os.path.splitext(os.path.basename(a.ref))[0] + '-editavel')});",
          "var ALV = Y.lerJSON(PASTA + \"/alvos.json\");",
          "var gF = Y.grupo(\"FUNDO\");",
          f"var ref = Y.colocar({json.dumps(os.path.abspath(a.ref))}, \"REFERENCIA (original, oculta)\", gF, {{ x: 0, y: 0, w: W, h: H }}, \"cobrir\", \"centro\"); ref.visible = false;",
          f"var limpo = Y.colocar({json.dumps(os.path.abspath(a.ref))}, \"FUNDO LIMPO (texto apagado)\", gF, {{ x: 0, y: 0, w: W, h: H }}, \"cobrir\", \"centro\");",
          "limpo = Y.apagarAreas(limpo, " + json.dumps([c["caixa"] for c in camadas] + (ui_instagram(a.largura, H) if a.limpar_ui else [])) + ");",
          "var gT = Y.grupo(\"TEXTOS\");"]
    for c in camadas:
        fxs = f", faixas: {json.dumps(c['faixas'], ensure_ascii=False)}" if c["faixas"] else ""
        js.append(f"Y.texto({{ txt: {json.dumps(c['txt'], ensure_ascii=False)}, nome: {json.dumps(c['nome'], ensure_ascii=False)}, fonte: {json.dumps(c['fonte'])}, px: 40, cor: {json.dumps(c['cor'])}, tracking: 0{fxs}, alvo: ALV[{json.dumps(c['nome'], ensure_ascii=False)}] }}, gT);")
    js += ["Y.salvar(SAIDA + \"/editavel.psd\", SAIDA + \"/editavel.png\");", "\"ok\";"]
    open(os.path.join(a.pasta, "arte.jsx"), "w").write("\n".join(js) + "\n")
    print("arte.jsx e medidas.json em", a.pasta)
    if not a.sem_ciclo:
        print(roda(sys.executable, os.path.join(AQUI, "ciclo.py"), a.pasta, timeout=3600))


if __name__ == "__main__":
    main()
