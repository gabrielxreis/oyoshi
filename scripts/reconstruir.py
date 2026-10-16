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


def tinta_por_forma(sub, D2, borda, devolver_mascara=False):
    """Tinta = grupo de cor de alto contraste com FORMA de traço (some numa erosão de 1 px); mancha de foto sobrevive.
    Entre os traços, o de maior contraste (miolo da letra, não a borda cinza do antisserrilhado)."""
    from PIL import ImageFilter
    cand = D2 >= np.percentile(D2, 75); px = sub[cand]
    if len(px) <= 30:
        return None
    c = px[np.random.default_rng(0).choice(len(px), 3, replace=False)]
    for _ in range(10):
        lb = ((px[:, None] - c[None]) ** 2).sum(2).argmin(1); c = np.array([px[lb == j].mean(0) if (lb == j).any() else c[j] for j in range(3)])
    lb_full = np.full(sub.shape[:2], -1); lb_full[cand] = lb; melhor, mel_c = None, -1
    for j in range(3):
        mk = lb_full == j; n = mk.sum()
        if n < cand.sum() * 0.12: continue
        # traço de letra: some depois de ~22% da altura da linha em erosões; mancha de foto (mais larga) sobra
        cur = Image.fromarray((mk * 255).astype(np.uint8))
        for _ in range(max(2, int(sub.shape[0] * 0.22))): cur = cur.filter(ImageFilter.MinFilter(3))
        if (np.asarray(cur) > 0).sum() / n > 0.08: continue
        contr = float(np.sqrt(((c[j] - borda) ** 2).sum()))
        if contr > mel_c: melhor, mel_c = j, contr
    if melhor is None:
        return None
    if devolver_mascara:
        return lb_full == melhor
    g = sub[lb_full == melhor]; dg = np.sqrt(((g - borda) ** 2).sum(1)); g = g[dg >= np.percentile(dg, 50)]
    return np.median(g, 0)


def cor_tinta(im, cx, ignorar=()):
    x1, y1, x2, y2 = cx; a = np.asarray(im.crop((x1, y1, x2, y2)).convert("RGB")).reshape(-1, 3).astype(float)
    sub = np.asarray(im.crop((x1, y1, x2, y2)).convert("RGB")).astype(float)
    borda = np.median(np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]), 0)
    d = np.sqrt(((a - borda) ** 2).sum(1))
    for c_ in ignorar:   # a cor da caixa marca-texto é fundo, não tinta
        d = np.minimum(d, np.sqrt(((a - c_) ** 2).sum(1)))
    D2 = d.reshape(sub.shape[:2]); f_ = tinta_por_forma(sub, D2, borda)
    if f_ is not None:
        return "#%02X%02X%02X" % tuple(int(v) for v in f_), borda
    tinta = a[d >= np.percentile(d, 85)]
    return "#%02X%02X%02X" % tuple(int(v) for v in cor_majoritaria(tinta, borda)), borda


def cor_majoritaria(px, fundo=None):
    """Cor da tinta = o MAIOR grupo de cor entre os pixels de contraste (brilho da foto atrás não vence a letra)."""
    if len(px) < 8:
        return np.median(px, 0)
    c = np.array([px[np.argmin(px.sum(1))], px[np.argmax(px.sum(1))]], float)
    for _ in range(8):
        lab_ = ((px[:, None] - c[None]) ** 2).sum(2).argmin(1)
        c = np.array([px[lab_ == j].mean(0) if (lab_ == j).any() else c[j] for j in range(2)])
    lab_ = ((px[:, None] - c[None]) ** 2).sum(2).argmin(1); j = np.bincount(lab_, minlength=2).argmax()
    g = px if np.sqrt(((c[0] - c[1]) ** 2).sum()) < 50 else px[lab_ == j]
    if fundo is not None and len(g) > 8:   # miolo do traço: metade mais distante do fundo (antisserrilhado puxa para o fundo)
        dg = np.sqrt(((g - fundo) ** 2).sum(1)); g = g[dg >= np.percentile(dg, 50)]
    return np.median(g, 0)


def detectar_caixas(im, cx):
    """Caixa marca-texto na linha: região de cor SATURADA, sólida (>= 80% do retângulo) e alta (>= 60% da linha)."""
    x1, y1, x2, y2 = cx; sub = np.asarray(im.crop(cx).convert("RGB")).astype(float); H_, W_ = sub.shape[:2]
    px = sub.reshape(-1, 3); sat = px.max(1) - px.min(1); cand = px[sat > 90]
    if len(cand) < H_ * W_ * 0.05:
        return []
    cor = np.median(cand, 0); mk = np.sqrt(((sub - cor) ** 2).sum(2)) < 70
    def maior_seq(idx, folga):
        if len(idx) == 0: return None
        mel, ini, ant = (idx[0], idx[0]), idx[0], idx[0]
        for v in idx[1:]:
            if v - ant > folga: ini = v
            if v - ini > mel[1] - mel[0]: mel = (ini, v)
            ant = v
        return mel
    rs = maior_seq(np.where(mk.mean(1) > 0.12)[0], 3)                  # linhas onde a cor da caixa aparece bem
    if not rs: return []
    faixa = mk[rs[0]:rs[1] + 1]
    cs = maior_seq(np.where(faixa.mean(0) > 0.30)[0], max(12, int((rs[1] - rs[0]) * 0.6)))   # letras brancas abrem buracos
    if not cs: return []
    if not rs or (cs[1] - cs[0]) < W_ * 0.08 or (rs[1] - rs[0]) < H_ * 0.4:
        return []
    bx = (cs[0], rs[0], cs[1] + 1, rs[1] + 1); area = (bx[2] - bx[0]) * (bx[3] - bx[1])
    caixa_mk = mk[bx[1]:bx[3], bx[0]:bx[2]]
    bordas = np.concatenate([caixa_mk[:3].ravel(), caixa_mk[-3:].ravel()]).mean()   # faixas sólidas acima/abaixo das letras
    if bordas < 0.8 or caixa_mk.mean() < 0.3:
        return []
    return [{"cor": "#%02X%02X%02X" % tuple(int(v) for v in cor), "ref": [x1 + bx[0], y1 + bx[1], x1 + bx[2], y1 + bx[3]], "rgb": cor}]


def caixa_cor(im, cor, w, linha_cx, k):
    """Retângulo da caixa colorida (marca-texto) em volta da palavra: pixels perto da cor, dentro da linha alargada."""
    x1, y1, x2, y2 = linha_cx; m_ = 30
    sub = np.asarray(im.crop((max(0, x1 - m_), max(0, y1 - m_), x2 + m_, y2 + m_)).convert("RGB")).astype(float)
    alvo = np.array([int(cor[i:i + 2], 16) for i in (1, 3, 5)], float); mk = np.sqrt(((sub - alvo) ** 2).sum(2)) < 45
    cols = np.where(mk.sum(0) > mk.shape[0] * 0.25)[0]; rows = np.where(mk.sum(1) > mk.shape[1] * 0.12)[0]
    ox, oy = max(0, x1 - m_), max(0, y1 - m_)
    if len(cols) == 0 or len(rows) == 0:
        return {"cor": cor, "caixa": [round(w["x"] * k), round(w["y"] * k), round((w["x"] + w["w"]) * k), round((w["y"] + w["h"]) * k)]}
    return {"cor": cor, "caixa": [round((ox + cols.min()) * k), round((oy + rows.min()) * k), round((ox + cols.max() + 1) * k), round((oy + rows.max() + 1) * k)]}


IGNORAR = []


def espessura(im, cx):
    """Espessura relativa do traço da linha: raio médio do traço (transformada de distância aproximada por erosões) / altura."""
    from PIL import ImageFilter
    sub = np.asarray(im.crop(cx).convert("RGB")).astype(float)
    borda = np.median(np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]), 0); d = np.sqrt(((sub - borda) ** 2).sum(2))
    for c_ in IGNORAR: d = np.minimum(d, np.sqrt(((sub - c_) ** 2).sum(2)))
    mk = tinta_por_forma(sub, d, borda, devolver_mascara=True)   # só o traço da letra (sem mancha da foto)
    if mk is None: mk = d > max(60, d.max() * 0.35)
    m = mk.astype(np.uint8) * 255; tot = (m > 0).sum(); acc = 0; cur = Image.fromarray(m)
    for _ in range(12):
        cur = cur.filter(ImageFilter.MinFilter(3)); n = (np.asarray(cur) > 0).sum(); acc += n
        if n == 0: break
    return acc / max(1, tot) / max(1, sub.shape[0])


def refinar_palavras(im, l):
    """Caixas de palavra pelos VÃOS reais de tinta (o Vision espalha as palavras por igual em fontes largas).
    Só troca se achar exatamente o mesmo número de blocos que de palavras."""
    pal = l.get("palavras") or []
    if len(pal) < 2:
        return pal
    x1, y1, x2, y2 = l["x"], l["y"], l["x"] + l["w"], l["y"] + l["h"]
    fora = np.asarray(im.crop((x1 - 4, y1 - 4, x2 + 4, y2 + 4)).convert("RGB")).astype(float)
    borda = np.median(np.concatenate([fora[0], fora[-1], fora[:, 0], fora[:, -1]]), 0)
    sub = np.asarray(im.crop((x1, y1, x2, y2)).convert("RGB")).astype(float); d = np.sqrt(((sub - borda) ** 2).sum(2))
    for c_ in IGNORAR: d = np.minimum(d, np.sqrt(((sub - c_) ** 2).sum(2)))
    tinta = d > max(60, d.max() * 0.35); col = tinta.sum(0) > 0
    seg, ini, vazio = [], None, 0; vao = max(3, int(l["h"] * 0.18))
    for x, v in enumerate(list(col) + [False] * (vao + 1)):
        if v:
            if ini is None: ini = x
            vazio = 0
        elif ini is not None:
            vazio += 1
            if vazio > vao: seg.append((ini, x - vazio + 1)); ini = None; vazio = 0
    if len(seg) != len(pal):
        return pal
    out = []
    for w, (a_, b_) in zip(pal, seg):
        w2 = dict(w); w2["x"] = x1 + a_; w2["w"] = b_ - a_; w2["y"] = y1; w2["h"] = y2 - y1; out.append(w2)
    return out


def faixas_palavras(im, linha, cor_linha, fonte_neg):
    """Negrito e cor por palavra: densidade de tinta (negrito tem ~25%+ mais tinta que a média da linha) e cor
    da tinta muito diferente da principal (palavra em vermelho). Devolve faixas para o Y.texto."""
    pal = linha.get("palavras") or []
    if len(pal) < 2:
        return [], cor_linha, []
    info = []
    for w in pal:
        cx = (w["x"], w["y"], w["x"] + max(2, w["w"]), w["y"] + max(2, w["h"]))
        sub = np.asarray(im.crop(cx).convert("RGB")).astype(float)
        if sub.size == 0: info.append(None); continue
        # fundo pela moldura de uma caixa 4 px MAIOR (a caixa do Vision encosta nas letras e o "fundo" virava a cor da letra)
        fora = np.asarray(im.crop((cx[0] - 4, cx[1] - 4, cx[2] + 4, cx[3] + 4)).convert("RGB")).astype(float)
        borda = np.median(np.concatenate([fora[0], fora[-1], fora[:, 0], fora[:, -1]]), 0)
        d = np.sqrt(((sub - borda) ** 2).sum(2))
        for c_ in IGNORAR: d = np.minimum(d, np.sqrt(((sub - c_) ** 2).sum(2)))   # cor de caixa marca-texto = fundo
        tinta = d > max(60, d.max() * 0.35)   # 35%: verde sobre escuro tem metade do contraste do branco
        # espessura do traço: fração da tinta que sobrevive a uma erosão de 1 px (negrito ~0,11-0,16; regular ~0-0,03)
        from PIL import ImageFilter
        er = np.asarray(Image.fromarray((tinta * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))) > 0
        dens = er.sum() / max(1, tinta.sum())
        f_ = tinta_por_forma(sub, d, borda) if sub.shape[0] > 6 and sub.shape[1] > 6 else None
        cor = f_ if f_ is not None else (cor_majoritaria(sub[tinta], borda) if tinta.any() else borda)
        info.append((dens, cor, borda))
    ok = [x for x in info if x]
    # negrito: espessura bem acima da mais fina da linha (linha mista); calibrado: Montserrat Bold 0,11+, Regular <= 0,03
    ds = sorted(x[0] for x in ok); corte = None
    if len(ds) > 1 and ds[-1] > 0.07 and ds[-1] > 3 * ds[0] + 0.03:
        corte = max(0.06, (ds[0] + ds[-1]) / 2.5)
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
        def mesma_cor(c1, c2):
            if c1 == c2: return True
            if not c1 or not c2: return False
            return sum((int(c1[i:i + 2], 16) - int(c2[i:i + 2], 16)) ** 2 for i in (1, 3, 5)) ** 0.5 < 45
        if out and out[-1].get("fonte") == f.get("fonte") and mesma_cor(out[-1].get("cor"), f.get("cor")) and f["de"] - out[-1]["ate"] <= 1:
            out[-1]["ate"] = f["ate"]
        else:
            out.append(dict(f))
    # caixas marca-texto: palavras cujo anel externo é uma cor SATURADA diferente do anel mediano da linha
    aneis = [x[2] for x in ok]; anel_linha = np.median(aneis, 0); caixas = []
    for w, x in zip(pal, info):
        if not x: continue
        r_ = x[2]; sat = r_.max() - r_.min()
        if np.sqrt(((r_ - anel_linha) ** 2).sum()) > 80 and sat > 80:
            caixas.append({"cor": "#%02X%02X%02X" % tuple(int(v) for v in r_), "palavra": w})
    for f in out: f.pop("_", None)
    return out, "#%02X%02X%02X" % tuple(int(v) for v in base), caixas


def ui_instagram(W, H):
    """Interface do Instagram que vem no print: seta do carrossel (direita/esquerda, meio) e bolinhas (base)."""
    return [[round(W * 0.915), round(H * 0.465), W, round(H * 0.535)], [0, round(H * 0.465), round(W * 0.085), round(H * 0.535)],
            [round(W * 0.40), round(H * 0.965), round(W * 0.60), H]]


def juntar_blocos(linhas, k, pequeno):
    """Linhas PEQUENAS empilhadas e alinhadas à esquerda (\"Arraste / para o / lado\") viram um bloco só (\r entre
    elas): medidas separadas a 17 px uma da outra se atrapalham no ciclo."""
    out = []
    for l in linhas:
        p_ = next((o for o in reversed(out) if abs(o["x"] - l["x"]) <= 4 and -l["h"] * 0.6 <= l["y"] - (o["y"] + o["h"]) < l["h"] * 0.8), None)
        if p_ and l["h"] * k < pequeno * 0.6 and (p_["h"] / p_.get("n_linhas", 1)) * k < pequeno * 0.9:
            p_["texto"] += "\r" + l["texto"]; p_["n_linhas"] = p_.get("n_linhas", 1) + 1
            p_.setdefault("tops", [p_["y"]]).append(l["y"])
            x2 = max(p_["x"] + p_["w"], l["x"] + l["w"]); y2 = l["y"] + l["h"]; p_["w"] = x2 - p_["x"]; p_["h"] = y2 - p_["y"]
            p_["palavras"] = []
        else:
            out.append(dict(l))
    return out


def roda(*cmd, timeout=600):
    return subprocess.run(list(cmd), capture_output=True, text=True, timeout=timeout).stdout


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("pasta"); ap.add_argument("--filtro", default="")
    ap.add_argument("--largura", type=int, default=1080); ap.add_argument("--sem-ciclo", action="store_true")
    ap.add_argument("--fonte-texto", default="", help="fonte do texto pequeno (da marca), ex. Montserrat-Regular")
    ap.add_argument("--fonte-negrito", default="", help="negrito do texto pequeno, ex. Montserrat-Bold")
    ap.add_argument("--pequeno", type=int, default=56, help="linha com altura < N px (doc) usa --fonte-texto")
    ap.add_argument("--logos", default="", help="textos que são logo (ficam como imagem), ex. Calverstone")
    ap.add_argument("--fonte-linha", default="", help='força a fonte de linhas: "L02=Owners-Bold;L01=OwnersWide-XLight"')
    ap.add_argument("--estilo", default="", help='faixas manuais: "L03:6-14=OwnersWide-Bold;L04:0-7=@#FF0000"')
    ap.add_argument("--corrigir", default="", help='trocas de texto do OCR: "para or=para o;0F=05"')
    ap.add_argument("--zonas", default="", help='áreas (px da referência) onde mora o texto de design: "x1,y1,x2,y2;..." (texto fora = da foto)')
    ap.add_argument("--limpar-ui", action="store_true", help="apaga seta e bolinhas do carrossel do Instagram (print)")
    ap.add_argument("--nota-min", type=float, default=0.45, help="abaixo disso a linha fica como imagem (logo)")
    a = ap.parse_args(); os.makedirs(a.pasta, exist_ok=True)
    im = Image.open(a.ref).convert("RGB"); W0, H0 = im.size; k = a.largura / W0; H = round(H0 * k)
    linhas = juntar_blocos(json.loads(roda(os.path.join(AQUI, "swift", "ocr"), a.ref)), k, a.pequeno)
    itens, camadas, caixas_mt = [], [], []
    # passada prévia: caixas marca-texto de TODAS as linhas (a cor da caixa vira fundo em qualquer linha vizinha)
    todas_caixas = []
    for l in linhas:
        pad = max(2, int(l["h"] * 0.35)); cx0 = (max(0, l["x"] - pad), max(0, l["y"] - pad), min(W0, l["x"] + l["w"] + pad), min(H0, l["y"] + l["h"] + pad))
        for c_ in detectar_caixas(im, cx0):
            if not any(abs(c_["ref"][0] - o["ref"][0]) < 8 and abs(c_["ref"][1] - o["ref"][1]) < 8 for o in todas_caixas): todas_caixas.append(c_)
    zonas = [[int(v) for v in z.split(",")] for z in a.zonas.split(";") if z.strip()]
    for i, l in enumerate(linhas):
        txt = l["texto"].strip()
        for par in [x for x in a.corrigir.split(";") if "=" in x]:   # erros de leitura do OCR: "para or=para o"
            de_, para_ = par.split("=", 1); txt = txt.replace(de_, para_)
        if not txt or l["conf"] < 0.4: continue
        if zonas and not any(z[0] <= l["x"] + l["w"] / 2 <= z[2] and z[1] <= l["y"] + l["h"] / 2 <= z[3] for z in zonas):
            print(f"{txt[:30]:<30} fora das zonas de texto: fica na imagem (texto da foto)", flush=True); continue
        if any(txt.lower() == g.strip().lower() for g in a.logos.split(",") if g.strip()):
            print(f"{txt:<30} logo: fica como IMAGEM", flush=True); continue
        pad = max(2, int(l["h"] * (0.2 if l["h"] * k < a.pequeno else 0.35))); cx = (max(0, l["x"] - pad), max(0, l["y"] - pad), min(W0, l["x"] + l["w"] + pad), min(H0, l["y"] + l["h"] + pad))
        cxs_ = todas_caixas
        cor, _ = cor_tinta(im, cx, [c_["rgb"] for c_ in cxs_])
        nome = f"L{i + 1:02d} {txt.replace(chr(13), ' / ')[:22]}"
        IGNORAR[:] = [c_["rgb"] for c_ in cxs_]
        l["palavras"] = refinar_palavras(im, l)
        fx, cor_base, cxs = faixas_palavras(im, l, cor, a.fonte_negrito if (l["h"] * k < a.pequeno) else None) if len(l.get("palavras") or []) > 1 else ([], cor, [])

        if fx or cor_base != cor:
            cor = cor_base; fx = [f for f in fx if f.get("fonte") or (f.get("cor") and np.sqrt(sum((int(f["cor"][i:i + 2], 16) - int(cor[i:i + 2], 16)) ** 2 for i in (1, 3, 5))) > 70)]
            for f in fx:
                if f.get("cor") and np.sqrt(sum((int(f["cor"][i:i + 2], 16) - int(cor[i:i + 2], 16)) ** 2 for i in (1, 3, 5))) <= 70: f.pop("cor")
        pequeno = l["h"] * k < a.pequeno
        fonte, nota = a.fonte_texto, 1.0
        pj = max(2, int(l["h"] * 0.08)); cj = (max(0, l["x"] - pj), max(0, l["y"] - pj), min(W0, l["x"] + l["w"] + pj), min(H0, l["y"] + l["h"] + pj))
        import ciclo as _C   # recorte JUSTO pela medida (a caixa do Vision é folgada e invade a linha vizinha)
        mj = _C.medir(a.ref, ",".join([cor] + sorted({f["cor"] for f in fx if f.get("cor")})), list(cx))
        if mj:
            cj = (max(0, int(mj["x"] / k) - 2), max(0, int(mj["y"] / k) - 2), min(W0, int((mj["x"] + mj["w"]) / k) + 3), min(H0, int((mj["y"] + mj["h"]) / k) + 3))
        out = "" if pequeno and a.fonte_texto else roda(PY, os.path.join(AQUI, "comparar_fonte.py"), a.ref, *map(str, cj), txt, "--cor", ",".join([cor] + sorted({f["cor"] for f in fx if f.get("cor")})), "--top", "12", *(["--filtro", a.filtro] if a.filtro else []))
        ranking = {}
        for ln in out.strip().splitlines():
            ps = ln.split()
            if len(ps) >= 4 and ps[0].replace(".", "").isdigit():
                ranking[ps[-1]] = float(ps[0]) * (0.97 if "Italic" in ps[-1] or "Oblique" in ps[-1] else 1.0)
        if ranking:
            fonte = max(ranking, key=ranking.get); nota = ranking[fonte]
        if nota < a.nota_min:   # nenhuma fonte parecida: é logo/lettering -> fica como imagem do fundo
            print(f"{txt[:30]:<30} nota {nota:.2f}: fica como IMAGEM (logo/lettering)", flush=True); continue
        print(f"{nome:<30} cor {cor}  fonte {fonte} ({nota:.2f})", flush=True)
        cores_med = ",".join([cor] + sorted({f["cor"] for f in fx if f.get("cor")}))   # mede a linha com TODAS as cores dela
        it_ = {"nome": nome, "texto": txt, "cor": cores_med, "regiao": list(cx)}
        if l.get("n_linhas"): it_["juntar"] = 30; it_["bloco"] = True
        itens.append(it_)
        if l.get("n_linhas"):
            passo = round(np.mean(np.diff(l["tops"])) * k, 1)
        camadas.append({"nome": nome, "txt": txt, "cor": cor, "fonte": fonte, "faixas": fx, "caixa": [round(v * k) for v in cx],
                        "passo": passo if l.get("n_linhas") else None,
                        "ranking": ranking, "alt": l["h"], "pequeno": pequeno, "esp": espessura(im, cj)})
    for c_ in todas_caixas:
        caixas_mt.append({"cor": c_["cor"], "caixa": [round(v * k) for v in c_["ref"]]}); print(f"caixa marca-texto {c_['cor']} em {[int(v) for v in c_['ref']]}", flush=True)
    for c in camadas: print(f"   espessura {c['nome'][:24]:<24} {c['esp']:.3f}")
    # linhas grandes de altura parecida (±18%) = mesmo bloco de título: mesma fonte, a de maior soma de notas
    grandes = [c for c in camadas if not c["pequeno"] and c["ranking"]]
    usados_ = set()
    for c in grandes:
        if id(c) in usados_: continue
        bloco = [d for d in grandes if abs(d["alt"] - c["alt"]) <= c["alt"] * 0.18
                 and min(d["esp"], c["esp"]) / max(d["esp"], c["esp"], 1e-6) > 0.6]   # só linhas de traço parecido (fina x pesada não votam juntas)
        for d in bloco: usados_.add(id(d))
        if len(bloco) > 1:
            soma = {}
            for d in bloco:
                for f_, v in d["ranking"].items(): soma[f_] = soma.get(f_, 0) + v
            venc = max(soma, key=soma.get)
            for d in bloco: d["fonte"] = venc
            print(f"bloco de {len(bloco)} linhas -> {venc} (soma {soma[venc]:.2f})", flush=True)
    # ajustes manuais (quando a detecção automática erra): --fonte-linha "L02=Owners-Bold;L01=OwnersWide-XLight"
    for par in [x for x in a.fonte_linha.split(";") if "=" in x]:
        n_, f_ = par.split("=", 1)
        for c in camadas:
            if c["nome"].startswith(n_.strip() + " "): c["fonte"] = f_.strip(); print(f"ajuste manual: {c['nome']} -> {f_}")
    # --estilo "L03:6-14=OwnersWide-Bold" (faixa de caracteres com outra fonte; cor opcional depois de @: "...=Fonte@#FF0000")
    for par in [x for x in a.estilo.split(";") if ":" in x and "=" in x]:
        n_, resto = par.split(":", 1); faixa_, fonte_ = resto.split("=", 1); de_, ate_ = map(int, faixa_.split("-"))
        cor_ = None
        if "@" in fonte_: fonte_, cor_ = fonte_.split("@", 1)
        for c in camadas:
            if c["nome"].startswith(n_.strip() + " "):
                f = {"de": de_, "ate": ate_}
                if fonte_: f["fonte"] = fonte_.strip()
                if cor_: f["cor"] = cor_.strip()
                c["faixas"] = [x for x in c["faixas"] if x["ate"] <= de_ or x["de"] >= ate_] + [f]; print(f"ajuste manual: {c['nome']} faixa {f}")
    json.dump({"ref": os.path.abspath(a.ref), "itens": itens}, open(os.path.join(a.pasta, "medidas.json"), "w"), ensure_ascii=False, indent=1)
    js = [f"// Reconstruído automaticamente de {os.path.basename(a.ref)} (reconstruir.py): fundo limpo + textos vivos medidos.",
          f"var W = {a.largura}, H = {H}; Y.doc(W, H, {json.dumps(os.path.splitext(os.path.basename(a.ref))[0] + '-editavel')});",
          "var ALV = Y.lerJSON(PASTA + \"/alvos.json\");",
          "var gF = Y.grupo(\"FUNDO\");",
          f"var ref = Y.colocar({json.dumps(os.path.abspath(a.ref))}, \"REFERENCIA (original, oculta)\", gF, {{ x: 0, y: 0, w: W, h: H }}, \"cobrir\", \"centro\"); ref.visible = false;",
          f"var limpo = Y.colocar({json.dumps(os.path.abspath(a.ref))}, \"FUNDO LIMPO (texto apagado)\", gF, {{ x: 0, y: 0, w: W, h: H }}, \"cobrir\", \"centro\");",
          "limpo = Y.apagarAreas(limpo, " + json.dumps([c["caixa"] for c in camadas] + [b_["caixa"] for b_ in caixas_mt] + (ui_instagram(a.largura, H) if a.limpar_ui else [])) + ");",
          "var gT = Y.grupo(\"TEXTOS\");"]
    for j_, b_ in enumerate(caixas_mt):   # marca-texto como forma editável, atrás do texto
        x1_, y1_, x2_, y2_ = b_["caixa"]
        js.append(f"Y.retangulo({{ x: {x1_}, y: {y1_}, w: {x2_ - x1_}, h: {y2_ - y1_}, cor: {json.dumps(b_['cor'])}, nome: \"CAIXA MARCA-TEXTO {j_ + 1}\" }}, gT);")
    for c in camadas:
        fxs = f", faixas: {json.dumps(c['faixas'], ensure_ascii=False)}" if c["faixas"] else ""
        if c.get("passo"):   # bloco de várias linhas: largura + entrelinha medida
            fxs += f", entrelinha: {c['passo']}"
            c["nome_alvo"] = f"Y.mesclar(ALV[{json.dumps(c['nome'], ensure_ascii=False)}], {{ por: \"largura\", passo: {c['passo']} }})"
        js.append(f"Y.texto({{ txt: {json.dumps(c['txt'], ensure_ascii=False)}, nome: {json.dumps(c['nome'], ensure_ascii=False)}, fonte: {json.dumps(c['fonte'])}, px: 40, cor: {json.dumps(c['cor'])}, tracking: 0{fxs}, alvo: {c.get('nome_alvo') or 'ALV[' + json.dumps(c['nome'], ensure_ascii=False) + ']'} }}, gT);")
    js += ["Y.salvar(SAIDA + \"/editavel.psd\", SAIDA + \"/editavel.png\");", "\"ok\";"]
    open(os.path.join(a.pasta, "arte.jsx"), "w").write("\n".join(js) + "\n")
    print("arte.jsx e medidas.json em", a.pasta)
    if not a.sem_ciclo:
        print(roda(sys.executable, os.path.join(AQUI, "ciclo.py"), a.pasta, timeout=3600))


if __name__ == "__main__":
    main()
