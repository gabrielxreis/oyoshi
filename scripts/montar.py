"""Roda um script de arte (.jsx que usa a biblioteca Y de jsx/yoshi.jsx) no Photoshop, com caminhos injetados.
    python3 montar.py arte.jsx VAR=valor VAR2=valor ...
As variáveis viram `var VAR="valor";` antes do script. Devolve o que o script devolver e mostra alertas fechados."""
import json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import ps_lib as PS
arte = os.path.abspath(sys.argv[1])
vars_ = dict(a.split("=", 1) for a in sys.argv[2:])
cab = f'$.evalFile({json.dumps(os.path.join(AQUI, "jsx", "yoshi.jsx"))});\n' + "".join(f"var {k}={json.dumps(v)};\n" for k, v in vars_.items())
r = PS.js(cab + open(arte, encoding="utf-8").read(), timeout=900)
print(r)
if PS.ALERTAS: print("ALERTAS:", PS.ALERTAS)
