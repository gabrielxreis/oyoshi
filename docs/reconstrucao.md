# Reconstrução: imagem chapada para PSD editável

`scripts/reconstruir.py` transforma um print de post (ou qualquer arte achatada) num PSD em camadas: fundo limpo, textos vivos com a fonte e o estilo do original, caixas de destaque como forma. Depois, `ciclo.py` ajusta tudo até 1 px e `virar_template.py` transforma o resultado em molde da marca.

## Etapas

1. **OCR nativo do macOS** (`scripts/swift/ocr`, framework Vision): linha, palavra e caixa. Compilar uma vez: `swiftc -O scripts/swift/ocr.swift -o scripts/swift/ocr`. Acentos em pt-BR saem certos; texto minúsculo (< 10 px) às vezes erra ("para or"): use `--corrigir`.
2. **Filtros de linha**: fora de `--zonas` fica na imagem (placa, tela, embalagem da foto); nomes em `--logos` ficam como imagem; linhas pequenas empilhadas e alinhadas viram um bloco só (`juntar_blocos`).
3. **Caixas marca-texto** (`detectar_caixas`, passada prévia em todas as linhas): cor saturada, diferente do fundo da linha, com faixas sólidas acima e abaixo das letras (>= 80%). Viram `Y.retangulo` editável, e a cor delas passa a contar como fundo na leitura da tinta.
4. **Cor da tinta** (`tinta_por_forma`): k-médias com 3 grupos nos pixels de maior contraste; a letra é o grupo com forma de traço (some após erosões de ~22% da altura da linha; a mancha da foto sobra). Entre os traços, fica o de maior contraste: é o miolo da letra, não a borda cinza do antisserrilhado.
5. **Palavra a palavra** (`faixas_palavras`): as caixas do Vision são aproximadas em fontes largas, então `refinar_palavras` recorta pelos vãos reais de tinta quando a contagem bate. O fundo da palavra vem de uma moldura 4 px maior. Negrito = sobrevivência à erosão de 1 px > 0,12 (Bold 0,15-0,30; Regular até 0,09). Cor diferente da maioria = faixa de cor. A cor-base é a da maioria das palavras, pesada pela largura.
6. **Fonte**: recorte justo pela medida (a caixa do Vision é folgada e invade a linha vizinha) e `comparar_fonte.py` com as cores da linha. Linhas grandes de altura e espessura parecidas votam juntas, pela soma das notas, com penalidade de 3% para itálico. Texto pequeno usa `--fonte-texto` e `--fonte-negrito` da marca. Se o automático errar: `--fonte-linha` e `--estilo`.
7. **Fundo limpo** (`fundo_por_difusao`): onde o anel em volta do texto tem pouco detalhe fino (degradê, cor chapada), o texto some por difusão, numa frente de onda que só usa vizinhos válidos. Onde há textura (foto), entra o Preenchimento Sensível ao Conteúdo do Photoshop (`Y.apagarAreas`). A interface do Instagram (seta, bolinhas) sai com `--limpar-ui`.
8. **Texto atrás do objeto** (`ocultar.py`, roda sozinho no fim): compara a tinta da referência com a do remake em cada linha; cobertura < 0,88 = letra escondida por objeto -> máscara de camada pela tinta visível (com abertura morfológica para não sair pontilhada). Se a referência tem o contorno da letra desenhado sobre o objeto (efeito da tela do celular), cria uma cópia só-contorno visível onde o objeto cobre. O apagar do fundo segue a forma da tinta (dilatada), então o objeto na frente não é apagado.
9. **Ciclo**: grava `medidas.json` e `arte.jsx` (cada linha com `alvo`) e roda `ciclo.py`: mede a referência, monta, mede o resultado com a mesma régua e corrige até erro <= 1 px.

## Por que cada heurística existe (erros reais que ela resolveu)

| Sintoma | Causa | Correção |
|---|---|---|
| Fonte condensada com espaçamento enorme | tracking livre no comparador premiava largura errada | largura natural com peso de novo |
| Título lido como fonte errada | a caixa do OCR pegava a linha de baixo | recorte pela medida |
| Palavra verde saiu branca | a caixa da palavra encostava na letra, e o "fundo" virava verde | moldura 4 px maior |
| Negrito falso em "Está" e "Mas" | densidade de tinta varia com a forma das letras | espessura do traço por erosão |
| Linha marrom em vez de branca | foto clara atrás de texto fino | tinta escolhida pela forma |
| Fundo azul virou "caixa" | cor saturada do próprio fundo | a caixa tem que diferir do fundo da linha |
| Retângulos escuros no degradê | sensível ao conteúdo amostra áreas escuras | difusão em fundo liso |
| Myriad Pro no meio do texto | vão entre faixas sem fonte | `Y.faixas` grava a fonte da camada |

## Limites conhecidos
- Texto fino e claro sobre roupa ou parede clara contamina a medida: use `--fonte-linha`/`--estilo` e meça à mão (`medir_texto.py --regiao`).
- Emoji branco ao lado de texto branco é apagado junto (vai como texto Apple Color Emoji, se precisar).
- A foto continua a do print (resolução da captura). Para um remake com foto nova, use a reconstrução como template (`virar_template.py`) e troque o fundo.
