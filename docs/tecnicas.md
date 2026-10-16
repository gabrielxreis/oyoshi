# Técnicas do laboratório (engenharia reversa, testadas no Photoshop 2026)

Cada técnica tem função no motor `Y` (scripts/jsx/yoshi.jsx) ou script em `scripts/`. Status: ✅ testada e conferida
no PNG, ⚠️ funciona com ressalva.

## Como descobrir descritores novos (método)
1. **Dicionário de terminologia embutido no binário**: `strings -n 20 ".../Adobe Photoshop 2026.app/Contents/MacOS/Adobe Photoshop 2026" | grep '\[(\$\$\$/Actions/'` lista TODO evento (`/transform [... <</offset ... /warp ...>>]`) e toda classe com as chaves e os tipos (`/rationalPoint <</horizontal /floatType ...>>`). Cópias em `docs/catalogo/local/terminologia*.txt`.
2. **Ler de volta o que o Photoshop grava**: aplicar a operação com um preset que funciona (ex.: warp Arco) e ler a propriedade (`smartObjectMore`, `layerEffects`, `blendRange`) com `executeActionGet` + `desc2json.jsx`. Foi assim que o formato da malha saiu: `warpCustom` + `bounds` (classFloatRect) + `customEnvelopeWarp.meshPoints` (rationalPoint em px). O nome na terminologia (`points`) NÃO era o nome usado.
3. `batchplay_exemplos_adobe.json` (extraído dos plugins UXP da própria Adobe) tem a forma dos eventos de filtro (displace, dust, etc.).

## Técnicas
| Técnica | Como | Status |
|---|---|---|
| **Mesclar se (Blend If)** | `Y.mesclarSe(l, esta, baixo)`; ex. texto some nas luzes da foto: `Y.mesclarSe(t, null, [0,0,60,140])` (valores separados = transição suave) | ✅ |
| **Glitch RGB** | `Y.glitch(l, dx)`: duas cópias com restrição de canal (R / G+B) deslocadas; `Y.canais(l, ["red"])` avulso | ✅ |
| **LUT de cor** | `Y.lut("Fuji F125 Kodak 2393 (by Adobe).cube", "LUT FILME", g, op)` (evento `makerColorLookupLayerFromFile`; LUTs do Photoshop em `Y.LUTS`) | ✅ |
| **Deslocamento (texto acompanha tecido/parede)** | `Y.criarMapa(foto, "mapa.psd", 4)` + `Y.deslocar(l, "mapa.psd", 20)` (vira objeto inteligente com filtro editável) | ✅ |
| **Texto em arco** | `Y.arco(textLayer, 40)` (deformação de texto, continua editável) | ✅ |
| **Mockup em perspectiva** | `scripts/perspectiva.py arte.png saida.png --doc W H --cantos ... --raio 30` (homografia exata, cantos arredondados) e `Y.colocar(saida, nome, g)` SEM caixa; guardar a arte original oculta | ✅ |
| Perspectiva nativa por malha | `Y.perspectiva(l, cantos)`: a malha gravada sai certa, mas o pixel depende de onde a camada nasceu (forma em 300,300 bateu; em 0,0 não) | ⚠️ não usar em entrega |
| **Cantos de tela de celular** | `medir_objeto.py --ps "the phone" --retangulo` (ângulo/largura/topo por regressão das bordas) e geometria do aparelho para os cantos escondidos pela mão | ✅ |
| **Dedos por cima da tela** | cópia da foto no topo com `Y.mascara(copia, ["the fingers","the thumb"], {estrito:true})` | ✅ |

## Exemplo completo
`_laboratorio/mockup_celular.jsx` (pasta privada): foto de mão com celular + arte da marca na tela + reflexo + dedos por cima.
