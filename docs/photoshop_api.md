<!-- Engenharia reversa do Adobe Photoshop 2026 (27.11.0, ExtendScript 4.5.12), Mac, 16/10/2026.
     Ler antes de prometer qualquer coisa "pela API" ou de automatizar uma etapa nova no Photoshop. -->

# O que dá para fazer no Photoshop por API, por MCP e pela tela

## As camadas de controle (da mais confiável para a menos)

| Camada | O que é | Quando usar |
|---|---|---|
| **Agente nativo do Photoshop** (`PS.ferramenta(nome, params)`) | Descoberta de 16/10/2026: o PS 2026 tem um "MCP interno" (o motor do "Assistente de IA"). AM `listTools` / `executeTool` com alvo `[agent, application]` devolvem **137 ferramentas com JSON Schema** de entrada e saída (`docs/catalogo/local/agente_ferramentas.json`) + **18 escondidas** (`agente_ferramentas_escondidas.txt`). Valida os parâmetros e devolve `{status, data}` em JSON. IDs de documento/camada são UUID. | **Primeira escolha** para o que existir lá: texto com fonte e bloco que se ajusta, formas, camadas de ajuste com parâmetros, efeitos, pranchetas, seleção por prompt, presets, estrutura do documento. |
| **ExtendScript via AppleScript** (`scripts/ps_lib.py`) | `tell application id "com.adobe.Photoshop" to do javascript "$.evalFile('x.jsx')"`. Sem plugin, porta ou senha. DOM com 33 classes (`docs/catalogo/dom_extendscript.tsv`): Application 44 métodos, ArtLayer 70, Document 26, Selection 25, TextItem 60 propriedades. | **Caminho padrão do Yoshi.** Tudo que o DOM tem. |
| **Action Manager** (`executeAction` / `executeActionGet` dentro do mesmo ExtendScript) | O "batchPlay" do ExtendScript: qualquer evento que o Photoshop grava (smart object, estilos de camada, formas, ajustes, IA). IDs por `stringIDToTypeID`. | Tudo que o DOM não alcança. Descobrir descritor novo: ver o código do photoshop-mcp ou gravar uma Ação e inspecionar. |
| **Menu pela tela** (`app_menu` do computer use) | 759 comandos de menu catalogados com o ID (`docs/catalogo/menus_photoshop.tsv`). | Só quando não houver Action Manager. **`app.runMenuItem` NÃO funciona** quando o script vem do AppleScript (ver armadilhas). |
| **UXP + batchPlay** (plugin dentro do Photoshop) | API moderna da Adobe (JavaScript, `executeAsModal`, Imaging API). Exige instalar um plugin (.ccx ou UXP Developer Tool). | Só para o que o ExtendScript não faz: **Neural Filters** e leitura de pixels rápida. Não necessário para começar. |
| **Generator / Conexões remotas** (porta 49494, senha) | Plugin `Generator` já vem instalado; é o canal do `kyamagu/photoshop-connection` (arquivado). | Não usar: mesmo poder do ExtendScript, com mais configuração. |

**Conclusão:** um único caminho (ExtendScript + Action Manager pelo AppleScript) cobre praticamente todo trabalho de design. É o mesmo caminho que o `alisaitteke/photoshop-mcp` usa no Mac (ele confirma: "AppleScript → do javascript"; UXP só para Neural Filters).

## Agente nativo: como usar

```python
import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/oyoshi/scripts")); import ps_lib as PS
d = PS.doc_frente()                                   # UUID do documento da frente
PS.ferramenta("document_create_text_layer", {"doc_id": d, "text": "TÍTULO", "font_postscript_name": "Montserrat-Bold",
    "font_size": {"value": 96, "unit": "pixels"}, "font_color": {"r":255,"g":212,"b":0},
    "position_x": 50, "position_y": 20, "position": "top", "text_alignment": "center"})
PS.ferramenta("document_get_structure", {"doc_id": d})   # árvore com id, tipo, bounds, máscara, bloqueio, opacidade
```

Por baixo: `executeAction(s("executeTool"))` com `null` = referência `agent` dentro de `application`, `name` e `params` (objeto). `listTools` com `expanded: true` lista tudo. Para rever o schema de uma ferramenta: abrir `agente_ferramentas.json` (as chaves `$schema`/`$id` aparecem como `sche`/`id  `, efeito da conversão; ignorar).

**Testadas e funcionando:** `application_new_document`, `application_list_open_documents` (escondida), `document_get_structure` (escondida), `document_get_layer_selection`, `document_create_text_layer`, `text_layer_get_character_attributes`, `shape_layer_create_shape_layer`, `document_create_solid_color_layer`, `layer_effect_add_stroke`, `layer_get_extended_properties`, `history_get_list`, `adjustment_get_presets` (36 presets de cor: Retratos, Paisagem...), `adjustment_apply_preset`, `application_get_artboard_presets`, `layer_cleanup_rename_layers` (renomeia camadas com IA em ~3 s; não pediu crédito).

**Grupos (137):** `application_*` (novo, abrir, salvar, fechar, duplicar), `document_*` (criar camadas de texto/pixel/grupo/cor/ajuste de 14 tipos, pranchetas, girar, espelhar, redimensionar imagem e tela, preencher sensível ao conteúdo, apagar seleção), `layer_*` (mover, girar, redimensionar, opacidade, modo de mesclagem, visibilidade, bloqueio, recorte, máscara da seleção, smart object, remover fundo, rasterizar, reordenar, agrupar, parâmetros de todo ajuste), `text_layer_*` (texto, caractere, parágrafo, moldura, orientação, "magic layout" = texto que se ajusta ao bloco), `shape_layer_*`, `layer_effect_*` (traço), `selection_*` (tudo, assunto, por **prompt**, faixa de cores, retângulo, elipse, expandir, contrair, suavizar, difusão, inverter), `filter_*` (9 filtros), `history_*`, `adjustment_*`, `gen_tech_*`.

**Pegadinhas do schema:** `position_x/position_y` do texto são **% do documento** (0-100), não pixels. `font_size` e `resolution` são objetos `{value, unit}`. `position` da camada (`top|bottom|above|below|inside`) é obrigatório no texto. `magic_layout_type` só aceita `"block_fit"` (precisa de `area_frame`). Prancheta exige `anchor {x,y}`. O UUID do documento NÃO é o `id` do DOM: passar o número dá "Document not found".

**Gastam crédito generativo** (têm `model_id`; pedir autorização antes): `gen_tech_gen_fill` (Firefly Image 5), `gen_tech_text_to_image` (padrão **Nano Banana 3** via Firefly), `gen_tech_gen_expand_firefly_image_4`, `gen_tech_generative_upscale` (Topaz), `gen_tech_topaz_sharpen`, `gen_tech_topaz_denoise`, `gen_tech_harmonize`. `document_remove_selection` pode usar remoção generativa (`use_generative_ai`). Escondidas, não testadas: `gen_tech_generate_background_firefly_image_3`, `gen_tech_generative_recompose`.

## Gravador de ações (aprender com o usuário)

`PS.gravar(True)` registra um notifier `"All "`: cada ação feita **pela interface** (menu, painel, atalho) vira uma linha em `$TMPDIR/oyoshi_gravacao.jsonl` com o evento e o descritor completo, referências incluídas. Testado: "Selecionar > Tudo" gravou `invokeCommand {commandID: 1017}` + `set {null: [{_ref: channel, _property: selection}], to: allEnum}`. Ações feitas por script NÃO aparecem. É o ScriptingListener sem instalar nada: o usuário faz uma vez, o Yoshi copia o descritor e repete por script. **Sempre `PS.gravar(False)` no fim.**

## Ouro escondido no app (engenharia reversa dos painéis da Adobe)

O Photoshop traz 23 plugins UXP próprios em `Contents/Required/UXP/` (461 MB de JavaScript legível). `scripts/sondar/extrai_bp.py` tira deles **257 eventos/classes do batchPlay com exemplo real** (`docs/catalogo/local/batchplay_exemplos_adobe.json`, gerado pelo `catalogar.py`), entre eles: `neuralGalleryFilters` (Neural Filters), `skyReplacement` com todos os parâmetros, `selectSky`, `generativeUpscale`, `exportDocumentAsFileTypePressed` (Exportar como PNG sem diálogo), `makerColorLookupLayerFromFile` (LUT a partir de arquivo), `findFontByName`, `owlAction` (abrir/fechar/listar painéis), `getLayersPanelInfo`. O vocabulário completo do Action Manager (4352 IDs) está em `am_vocabulario.tsv` (`scripts/sondar/ids.jsx`).

## Recursos instalados (`docs/catalogo/local/descritores/app.json`, `acoes_instaladas.txt`)

- **7 conjuntos de Ações** prontos (rodar com `app.doAction("nome", "conjunto")`): Redimensionar (Instagram paisagem/retrato/quadrado, Facebook, X, **miniatura do YouTube**), Objeto e fundo (selecionar objeto, remover fundo, desfocar fundo, gerar fundo, harmonizar), Ajustes básicos, Efeitos criativos (granulação, vinheta, P&B), Guias (terços, grades 4x4 e 12x12), Exportar (PSD/PNG/JPG/TIFF/GIF/PDF).
- Presets: 28 pincéis, 122 amostras de cor, 183 degradês, 21 estilos de camada, 10 padrões, 21 predefinições de ferramenta; 112 ferramentas; 47 painéis; 1763 fontes.
- Descritor do documento (60 chaves) e de camada: `docs/catalogo/local/descritores/`.

## Testado e funcionando (27.11, 16/10/2026; `docs/catalogo/testes_27.11.tsv`)

| O quê | Como | Tempo |
|---|---|---|
| Criar documento 1080x1350 | `app.documents.add(...)` | |
| Colocar imagem como **smart object** | AM `placeEvent` | 1,4 s |
| Ler qual arquivo está no smart object | AM `executeActionGet` > `smartObject.fileReference` | 0 ms |
| **Trocar conteúdo do smart object** (base de template/mockup) | AM `placedLayerReplaceContents` | 0,3-0,5 s |
| Redimensionar/mover camada | `layer.resize()` / `translate()` | |
| **Selecionar assunto** (IA local, sem crédito) | AM `autoCutout` | 10,5 s (1ª vez carrega modelo) |
| Máscara a partir da seleção | AM `make` channel `mask` `revealSelection` | |
| **Remover fundo** (sem crédito) | AM `removeBackground` | 2,6 s |
| Texto com fonte por PostScript, cor HEX, tamanho, alinhamento | `textItem.font = "Montserrat-Bold"` etc. 1763 fontes em `app.fonts` | 0,35 s |
| Texto de parágrafo (caixa que quebra linha) | `textItem.kind = PARAGRAPHTEXT`, `width/height` | |
| **Estilo de camada** (sombra + traço) | AM `set` `layerEffects` (`dropShadow`, `frameFX`) | 11 ms |
| **Forma vetorial** (retângulo com canto arredondado) | AM `make` `contentLayer` + `rectangle` com `topLeft...` | |
| Camada de ajuste (matiz/saturação; vale para curvas, níveis, LUT...) | AM `make` `adjustmentLayer` | |
| Camada de degradê | AM `make` `contentLayer` `gradientLayer` (precisa do objeto `gradient` com `colors` e `transparency`; vazio dá erro) | |
| Máscara de corte (clipping) | AM `groupEvent` | |
| Grupo e mover camada para dentro | `layerSets.add()`, `layer.move(g, INSIDE)` | |
| **Prancheta** (artboard; carrossel com vários slides num PSD) | AM `make` `artboardSection` | |
| **Retrato da árvore de camadas** | AM `numberOfLayers` + `layer` por índice | 2 ms p/ 11 camadas |
| Filtros clássicos (desfoque, nitidez, ruído...) | `layer.applyGaussianBlur()` etc. (40 filtros no DOM) | |
| Exportar PNG / JPG / PSD | `saveAs(..., asCopy=true)`, `exportDocument(SAVEFORWEB)` | 0,5-1,4 s |
| Um desfazer para o lote inteiro | `doc.suspendHistory("nome", "codigo")` | |
| **Conferir o resultado com os olhos** | exportar PNG e abrir com Read | |

## Disponível, ainda não testado aqui

| O quê | Como | Observação |
|---|---|---|
| **Generative Fill / Remove / Expand / texto para imagem** (Firefly) | AM `syntheticFill` com `prompt`, `serviceID: "clio"`, `workflowType: in_painting \| text_to_image` (descritor no `photoshop-mcp`, `src/api/extendscript.ts`, MIT) | **Gasta crédito generativo da Adobe.** Precisa de seleção. `app.featureEnabled("generativeFill")` devolveu `false` (o nome da flag provavelmente não é esse; testar a chamada real só com autorização). |
| Generative Upscale (27+) | AM `generativeUpscale` | Crédito. |
| Sky Replacement | AM `skyReplacement` | Sem crédito. |
| Preenchimento sensível ao conteúdo | AM `fill` com `contentAware` | Sem crédito. |
| **Variáveis / Conjuntos de dados** | Menu Image > Variables / File > Export > Data Sets as Files | Template em lote a partir de CSV (o "autofill" do Photoshop). |
| Layer comps, guias, amostras de cor, ações (`app.doAction`) | DOM | Ação gravada pelo usuário vira atalho do Yoshi. |
| Scripts que já vêm no app | `Presets/Scripts/`: Export Layers To Files, ArtBoards To Files/PDF, Layer Comps To Files, Image Processor, Fit Image | Exportar carrossel por prancheta de graça. |
| Neural Filters (pele, harmonizar, colorir, super zoom) | Só via UXP batchPlay | Precisa do plugin UXP. |

## O que NÃO funciona (confirmado)

- **`app.runMenuItem(id)` chamado via AppleScript:** sempre "item de menu não está disponível", mesmo com o Photoshop na frente e documento limpo. Contorno: usar o evento do Action Manager equivalente (quase todo item de menu tem um) ou `app_menu` pela tela.
- **Menu pela tela com o Photoshop em segundo plano:** o `app_menu` do computer use acha os itens **desabilitados**. Antes: `osascript -e 'tell application id "com.adobe.Photoshop" to activate'`. Depois disso o menu funciona (testado com Selecionar > Tudo). Item que falha abre alerta modal no PS: fechar o alerta (janela "Adobe Photoshop", botão OK) antes de seguir.
- **Desfazer granular de IA**: `autoCutout` na primeira chamada demora ~10 s (carrega modelo); não é travamento.
- **Reflexão das coleções** (`Documents`, `ArtLayers`, `Layers`, `PathItems`, `LayerComps`) dá erro; as classes de item funcionam.

## Armadilhas

- **Unidades:** começar todo script com `app.preferences.rulerUnits = Units.PIXELS` e `app.displayDialogs = DialogModes.NO`.
- **Arquivo de saída do ExtendScript** usa quebra de linha CR no Mac: usar `f.lineFeed = "Unix"`.
- **AppleScript não aceita `POSIX file` em `do javascript`**: passar o caminho por `$.evalFile('...')`.
- `executeAction` em degradê/estilos com descritor incompleto devolve "parâmetros não são válidos": sempre mandar o objeto completo.
- Texto: a fonte vai pelo **PostScript name** (`Montserrat-Bold`), não pelo nome de exibição. Conferir em `app.fonts`.
- Sempre `saveAs(..., true)` (cópia) para exportar sem trocar o arquivo aberto.

## MCPs e repositórios avaliados

| Projeto | Como fala com o PS | Veredito |
|---|---|---|
| [alisaitteke/photoshop-mcp](https://github.com/alisaitteke/photoshop-mcp) (657★, MIT, atualizado 15/10/2026) | AppleScript `do javascript` (Mac) / COM (Win); UXP opcional na porta 38452 | **Melhor fonte de descritores prontos** (128 ferramentas, 17 receitas com 1 desfazer, Firefly). Usar como referência de código; instalar só se quiser as ferramentas MCP prontas. Tem telemetria anônima ligada por padrão. |
| [loonghao/photoshop-python-api-mcp-server](https://github.com/loonghao/photoshop-python-api-mcp-server) | COM | **Só Windows.** Ferramentas básicas. Não serve no Mac. |
| [kyamagu/photoshop-connection](https://github.com/kyamagu/photoshop-connection) | Socket criptografado na porta 49494 (Conexões remotas) | **Arquivado.** Mesmo ExtendScript com mais configuração. Não usar. |
| [sfkislev/flue](https://github.com/sfkislev/flue) (skill `photoshop`, 97★, MIT) | AppleScript `do javascript` (Mac) / COM (Win), por um `photoshop_bridge.py` | Mesmo caminho do Yoshi. Aproveitado: o **índice do DOM inteiro** (93 classes, 725 enums, 2157 propriedades, 67 métodos) em `docs/catalogo/flue_api-index.txt` (buscar com `rg`, nunca ler inteiro) e a ideia de um `APP.local.md` com armadilhas da máquina. Ele cobre também Illustrator, InDesign, AE, Premiere. |
| [photoshop-automator](https://www.skillsdirectory.com/skills/neversight-photoshop-automator) (abdul-karim-mia) | AppleScript (Mac) / VBScript+COM (Win) | Só 6 comandos (rodar JSX, trocar texto, criar camada, desfoque, ação, exportar). Nada novo. |
| [adobe/skills](https://github.com/adobe/skills) | n/a | **Sem Photoshop.** Tem Express (`adobe-design-from-template`), Firefly (`run-workflow`, exige plano enterprise) e "Adobe for Creativity" (só app desktop). Pode entrar depois para Adobe Express. |

## Canva (comparação)

O Canva não tem app local scriptável. O caminho é o **MCP oficial do Canva** (conector `plugin:marketing:canva`, ainda **não autorizado** nesta máquina): gerar design, buscar, exportar, subir asset e editar por transação (`start-editing-transaction` → `perform-editing-operations` → `commit-editing-transaction`), que hoje troca texto, mídia e título, sem controle fino de camada, estilo ou posição como no Photoshop. Disponível em todos os planos. Fontes: [Canva MCP](https://canva.dev/docs/mcp/), [verificação da integração](https://www.canva.dev/docs/mcp/verify-integration/).

## Como refazer a sondagem (versão nova do Photoshop)

```bash
osascript -e "tell application id \"com.adobe.Photoshop\" to do javascript \"\$.evalFile('$HOME/.claude/skills/oyoshi/scripts/sondar/reflect.jsx')\""
osascript -e "tell application id \"com.adobe.Photoshop\" to do javascript \"\$.evalFile('$HOME/.claude/skills/oyoshi/scripts/sondar/menus.jsx')\""
```

Saídas em `$TMPDIR/oyoshi_*.txt`. `testes.jsx` precisa de `pessoa.png` e `logo.png` na pasta de `OYOSHI_TESTE` (ou na pasta temporária).
