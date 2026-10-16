# Método: árvore de camadas e como estudar o PSD de um designer

Aprendido em 16/10/2026 dissecando PSDs reais de redes sociais (carrosséis, double cards, story, pôster de evento, tarjas de nome). Os detalhes de cada marca ficam na pasta da marca (`<pasta_saida>/<Marca>/design/design-<marca>.md`), nunca neste repositório.

## Estudar um PSD (sem abrir o Photoshop)

```bash
python3 -m venv ~/.claude/skills/oyoshi/.venv && ~/.claude/skills/oyoshi/.venv/bin/pip install -q psd-tools
~/.claude/skills/oyoshi/.venv/bin/python ~/.claude/skills/oyoshi/scripts/dissecar_psd.py arquivo.psd <Marca>/design/referencias/
```

Gera `<nome>.arvore.md` (árvore igual ao painel Camadas, com fonte, tamanho real em px, cor, tracking e alinhamento de cada trecho de texto, efeitos, smart objects, máscaras, recortes, modos de mesclagem e opacidade), `.arvore.json` e `.preview.jpg`. Leva segundos até em PSD de 700 MB e não trava o Photoshop do usuário. Guardar uma cópia do PSD em `<Marca>/design/referencias/psd/` e escrever/atualizar `design-<marca>.md` com: formato, tipografia, cores, árvore padrão, truques e regras de conteúdo.

## A árvore padrão do Yoshi

Toda peça sai nesta ordem (de cima para baixo), com grupos nomeados em MAIÚSCULAS por função:

```
PRANCHETA (uma por formato: FEED 1080x1440 / STORY 1080x1920 / CARROSSEL 1080*n x 1440)
├── ACABAMENTO        grão, LUT, mapas de degradê fracos (5-30%), ruído, textura em Tela/Luz suave
├── MARCA             logos (smart object), selos, bandeira, "Te explicamos na legenda" + seta
├── TEXTOS            uma camada por nível de leitura (APOIO_1, TITULO, DESTAQUE, APOIO_2, CTA)
├── RECORTES          cópia da foto com máscara só na pessoa/objeto, ACIMA do título ("sai da frente")
├── FOTOS             smart objects (original fica oculto como backup quando há recorte)
├── GRAFICOS          formas, palavra gigante de fundo, molduras
└── FUNDO             cor/degradê (smart object vetorial com Sobreposição de degradê ou camada de cor)
```

Regras que se repetiram em todos os designers:
- **Tudo que é imagem entra como smart object** (foto, logo, vetor do Illustrator). Ajuste de cor em vetor é **Sobreposição de cor/degradê** (efeito), não pintura.
- **Texto em escada:** uma frase quebrada em 2-4 camadas de tamanhos muito diferentes (pequeno > enorme > pequeno). Destaque de UMA palavra ou linha por slide, na cor de destaque da marca, às vezes em itálico.
- **Pessoa na frente do título:** duplicar o smart object da foto, máscara só na pessoa, cópia acima do texto. Original oculto embaixo.
- **Carrossel panorâmico:** todos os slides numa prancheta só, com um elemento atravessando a divisa entre slides (palavra gigante, foto). Exportar fatiando.
- **Acabamento em pilha:** a cor final vem de várias camadas de ajuste fracas (LUT 5-38%, mapa de degradê 8-27% em Sobrepor/Luz suave, ruído 3%), agrupadas e nomeadas. Nunca um ajuste forte só.
- **Grão por cima de tudo** (camada "Granulação" com máscara) para tirar cara de digital.
- **Duas pranchetas, mesma árvore** quando a peça tem feed e story: muda posição e escala, não a estrutura.
- Elemento de rodapé recorrente: "Te explicamos na legenda" + seta dentro de elipse, canto inferior direito.
- Texto legal (disclaimer) sempre como **camada de texto editável**, mesmo quando o resto da arte vem achatado de IA.

Os designers estudados quase não renomeiam camadas (`Objeto Inteligente de Vetor`, `Agrupar 1`). O Yoshi nomeia tudo pela função; o pôster mais organizado (grupos EFEITOS/AJUSTES/FILTROS/FINALIZAÇÃO/PHOTOS/BG) é o modelo.

## Fontes

Antes de montar, conferir se as fontes da marca existem: `PS.js("app.fonts.getByName('IvyPrestoDisplay-Regular').name")` ou listar `app.fonts`. Se faltar:
1. **Adobe Fonts** (incluído no Creative Cloud): a ferramenta nativa `document_create_text_layer` aceita `font_name` legível e **procura e baixa do Adobe Fonts sozinha**; ou ativar em fonts.adobe.com.
2. **Google Fonts** / site oficial da fundição quando a fonte é gratuita (baixar, instalar em `~/Library/Fonts/`, `app.refreshFonts()`).
3. Fonte paga fora do Adobe Fonts: **não baixar de site pirata**; avisar o usuário e propor a mais parecida disponível.
