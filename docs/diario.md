# Diário de aprendizado do Yoshi

Cada entrada: técnica, como faz no motor, o que deu errado e como ficou. Mais novo em cima.

## 2026-10-16 madrugada

- **Alinhamento idêntico ao original (pedido do Gabriel: "colocar uma foto em cima da outra e bater").**
  1. `medir_texto.py ref.png --cor "#FFF9ED" --regiao ...` acha cada LINHA de texto pela cor e devolve a caixa justa (x,y,w,h) já em 1080 px. Usar `--regiao` para separar título/apoio e cores diferentes.
  2. `Y.texto({..., alvo: {x,y,w,h}})` ajusta o tamanho da fonte até a largura bater (sem distorcer) e põe a caixa dos pixels no ponto exato. `alvo.por: "altura"` quando a largura está escondida.
  3. `sobrepor.py ref.png remake.png saida.png` gera 50/50, bordas (ref vermelho x remake ciano) e diferença; nota por bordas a 2 px. O 50/50 mostra na hora o que está fora.
  - Uma linha por camada de texto quando o alvo vem medido (cada linha tem tamanho próprio no original).
- **Máscara limpa.** `Y.mascara` agora passa pelo Selecionar e Mascarar (`Y.refinarSelecao`: raio inteligente 3 px, suavizar 2, difusão 0,6, contraste 15, borda -20% para dentro, deep matte) antes de criar a máscara: some a franja do fundo.
  - Seleção por descrição em INGLÊS e em LISTA para objeto composto: `["the phone", "the hand", "the arm"]`.
  - Selecionar numa camada e mascarar outra: `{fonte: foto}` (ex.: tela do celular acesa = degradê mascarado pela seleção "the phone screen" feita na foto).
  - Camada de preenchimento já nasce com máscara: `Y.tirarMascara` apaga a vazia antes (senão "Criar não disponível").
- **Linha branca atravessando o celular** era o contorno das letras grosso (2 px) e branco sobre tela preta. No original: 1 px, ~75% de opacidade, sobre a tela ACESA. `Y.contornoSobre(texto, tela, cor, 1)`.
- **Recorte automático (máscara de corte):** camada inserida logo acima da base de um recorte já entra recortada; `Y.recorte` não repete (senão erro).

## 2026-10-16 03h: corpo da letra (cy/ch) e texto em duas cores
- `medir_texto.py` aceita várias cores (`--cor "#FFFFFF,#3ED6A6"`) para linhas com palavra destacada, e devolve `cy/ch`: o CORPO da linha (faixa densa = altura da maiúscula), que ignora acento, cedilha, vírgula e cauda do Q.
- `Y.encaixarTexto` com `alvo.ch` em texto CAIXA ALTA mede numa cópia com só "H": o tamanho sai pela altura real da maiúscula e o topo do H vai para `cy`. Antes, "COMEÇAR" (cedilha) e "É" (acento) aumentavam a caixa e a fonte saía menor.
- `comparar_fonte.py --cor` também aceita várias cores.
- Texto fino antisserrilhado (Poppins Light 31 px) fica cinza ~186 na referência: medir com `--cor "#FFFFFF,#B4B4B4" --tol 60`, senão a primeira letra some da caixa.
- Bora Imigrar "médico medo": título é FranklinGothicATF-Heavy (mesmo do "QUANTO GANHA"), apoio Poppins-Light. Título quebrado em 3 camadas, uma por linha, cada uma com alvo próprio: sobreposição bate com 1-2 px de diferença.

## 2026-10-16 03h (b): prova de fogo da fonte, logo aparado, documentos fechados
- `comparar_fonte.py`: tracking livre (espaça as letras até a proporção da referência, já que tracking se ajusta depois), nota = desenho (IoU ou correlação desfocada no traço fino) + espessura do traço + um pouco de largura natural. Owners-Bold confirmado no "CRESCEU.".
- Linhas finas continuaram ambíguas (Helvetica Neue x Owners x Montserrat) na referência de 673 px. Solução: `provar_fontes.py`, que monta a arte no Photoshop com cada candidata (texto com alvo medido) e ranqueia pela sobreposição. Resultado: OwnersWide-XLight nas linhas finas e OwnersWide-Regular no "Arraste para o lado".
- Logo da Bora Comunicação entrava menor: o PNG tem halo de alfa 1-5% até a borda e o Photoshop conta isso no tamanho. `aparar.py` limpa e recorta; com o aparado, o logo bate em 1 px (449,1206,180,53 x ref 449,1205,180,53).
- `montar.py` agora fecha os documentos que abriu. Havia 21 abertos e o Photoshop parou com "discos de trabalho cheios" (disco do Mac com 6 GB livres).
- Caixa marca-texto: medida direto da referência (cor laranja) e desenhada como retângulo, em vez de calcular pelo texto + padding.

## 2026-10-16 03h (c): Calverstone fechada no texto
- Re-medida com corpo (cy/ch): as 4 linhas do remake batem em até 1 px com a referência (medir_texto nos dois lados).
- Prova de fogo: apoio = Montserrat-Regular/Bold (0,90; Gotham Book 0,86), título = GoodPro-XCondBlack (0,609 x XCondUltra 0,592; no olho, menos fantasma nas letras).
- Lição: dentro de uma família com muitas larguras/pesos (Good Pro, Owners), o comparador acha a família e a prova de fogo escolhe a variante.
- Diferença que sobra é a FOTO (outra pessoa). Para ficar idêntico de verdade precisaria da mesma foto de banco ou gerar por IA (perguntar ao Gabriel).

## 2026-10-16 03h (d): nota justa com referência borrada, cor medida
- `sobrepor.py`: a captura do Instagram (536-980 px) ampliada para 1080 fica borrada e quase sem bordas; a nota da AGM dava 0,14 com o texto no lugar. Agora o remake passa pela mesma resolução da referência + desfoque leve antes de comparar (AGM 0,69, Calverstone 0,76).
- `medir_texto.py` devolve `cor` de cada linha (mediana do miolo das letras, sem a borda antisserrilhada). AGM: creme #F1EEE6 e ouro #B18B38 (eu chutava #EEE6D6/#E3A93C).
- AGM "não é a câmera": BebasNeuePro-Bold confirmada na prova de fogo (0,713 x Bebas Neue Bold 0,696); título em 2 camadas medidas.

## 2026-10-16 03h (e): objeto no lugar certo
- `medir_objeto.py --ps "the camera"`: abre a referência no Photoshop, seleção por IA e devolve a caixa (258,258,561x579 na AGM; o limiar de cor errava porque a câmera tem partes escuras e um brilho em volta).
- `Y.caixaVisivel` / `Y.encaixarVisivel`: layer.bounds ignora a máscara, então o objeto recortado "media" a foto inteira. Agora mede pela máscara carregada como seleção. Câmera do remake: x 260 / largura 557 / centro 548 contra 258 / 561 / 547 na referência.
- SKILL.md ganhou o "Ciclo idêntico" (medir > encaixar > sobrepor) como passo obrigatório.

## 2026-10-16 03h (f): ciclo fechado, objeto girado, altura-x
- `Y.alinharObjeto(l, prompt, ref, anguloFoto)`: gira a foto pela diferença de ângulo (PCA da máscara de IA, `medir_objeto.py --ps` agora devolve `angulo` e `centro`), escala pela caixa e centraliza. Celular do "quanto ganha": foto a -22,3°, referência a 10,1°; depois de alinhar, 10,3° e centro a 9 px.
- Minúsculas encaixam pela altura do "x" (`xy/xh` no medir_texto): "Os números chamam atenção." saía com tracking aberto porque acentos/cedilha mudavam a caixa total.
- `medir_texto.py --tol auto` (padrão): borda a 50% de cobertura (metade da distância texto x fundo). Com tolerância fixa a altura-x variava 17-19 px (10% no tamanho).
- `ciclo.py`: mede ref > grava alvos.json > monta > mede remake (só em volta da caixa, só os campos que o motor usa) > corrige. Bora "quanto ganha": subtítulos e apoio bateram com <= 1 px na 1ª volta.

## 2026-10-16 03h (g): cor de objeto e objeto retangular
- `casar_cor.py`: casar a cor de um objeto com a referência. Curvas por canal com diferença grande POSTERIZAM (manchas ciano/vermelhas na pele); `--modo luz` = curva suave no composto + sólido no modo Cor com o tom mediano. Mão clara virou a mão em contraluz do original sem artefato.
- Máscaras por prompt agora têm nome próprio (`*.the-hand.mascara.png`) e o casar_cor aceita `--menos-ref/--menos-rem` (mão MENOS celular).
- Tela do celular: degradê com cores AMOSTRADAS ao longo do eixo da tela do original.
- `medir_objeto.py --retangulo`: em objeto de borda reta segurado, o PCA erra (10,1° x 7,9° reais) porque a mão entra na seleção. Ajuste das bordas esquerda/direita por regressão nas faixas sem dedo + centro da borda de cima. `Y.alinharRetangulo` e `Y.retanguloGirado` usam isso (celular desenhado em vetor, mão da foto por cima).
- Erro de leitura meu: conferi o topo numa prévia reduzida e achei que estava 40 px fora; no tamanho real o ponto caía certo. Conferir sempre na resolução nativa.

## 2026-10-16 04h: laboratório de técnicas (pedido do Gabriel: "aprenda coisa de verdade")
- Descoberta grande: o binário do Photoshop traz o dicionário de terminologia inteiro (eventos, classes, chaves, tipos). Extraído para `docs/catalogo/local/terminologia*.txt`.
- Testadas e incorporadas ao Y: Mesclar se, glitch por restrição de canal, LUT por arquivo, mapa de deslocamento, texto em arco.
- Warp personalizado: descobri o formato lendo de volta um warp Arco (`meshPoints`, não `points` como diz a terminologia), mas o resultado na tela depende da origem da camada. Mockup ficou com `perspectiva.py` (homografia exata em Python) e saiu perfeito: arte da Bora na tela do celular, dedos por cima.
- Ver `docs/tecnicas.md`.

## 2026-10-16 04h (b): lotes 2 e 3 de técnicas
- Lote 2 (efeitos de design): sombra longa, extrusão 3D, neon, cromado, texto vazado, retícula, sombra de contato, luz de recorte. `Y.efeitos` ganhou chanfro, brilho interno, sombra interna, degradê, cetim (chaves tiradas do dicionário do binário). Painel em `_laboratorio/painel-tecnicas-2.png`.
- Lote 3 (produção): trocar conteúdo de objeto inteligente + `lote.py` (série de posts a partir de um JSON), expandir fundo com sensível ao conteúdo (4:5 -> 9:16 sem crédito), separação de frequência + esquivar/queimar, dupla exposição.
- Lição da dupla exposição: Tela só funciona com sujeito escuro; com jaleco claro tudo estoura. Receita certa = Multiplicação + rosto preservado por máscara esfumada.

## 2026-10-16 04h (c): story automático, QA automático, carrossel em pranchetas
- `jsx/para_story.jsx`: feed -> story 9:16 (fundo expandido com sensível ao conteúdo, granulação esticada, rodapé fora da caixa de mensagem). Calverstone saiu pronta para publicar.
- `conferir_arte.py`: contraste WCAG do texto contra o fundo REAL, zona segura, tamanho mínimo, margens, centro (só em texto centralizado). Já pegou o "01/05" da Bora com 3,2:1.
- Pranchetas: o DOM não cria texto dentro de prancheta e o evento AM de converter grupo fica indisponível; as ferramentas nativas do agente resolvem. Bug achado no caminho: variável global `lista` num script sobrescrevia a função `lista()` do desc2json e quebrava toda resposta com lista ("Object não é uma função"); funções internas agora têm prefixo `_d2j`.

## 2026-10-16 04h (d): ler o sistema de design da referência; foto não comprada
- `analisar_ref.py`: paleta k-médias em Lab com área e papel 60/30/10, grade de texto agrupada por alinhamento (Bora: título à esquerda em 64 + apoio centralizado; Calverstone: tudo centralizado em 542), ritmo vertical e escala tipográfica; `--comparar` dá o ΔE do remake (Bora: preto ok 1,7; cinzas da foto 9-14 = foto diferente).
- Radiologia (Calverstone): procurei no banco (Freepik) uma foto equivalente; nenhuma prévia bate (a do post é de costas, cabelo escuro, raio-X erguido). NÃO comprei (40 créditos por uma foto diferente). Fica para perguntar ao Gabriel se ele tem a foto original ou se quer gerar por IA.
- Tentei busca por similaridade de imagem (imageBase64): rejeitada, a string longa se corrompe; usar busca por texto + conferência das prévias públicas.

## 2026-10-16 04h (e): imagem chapada -> PSD editável, automático
- `scripts/swift/ocr.swift`: OCR nativo do macOS (Vision), texto + caixa por linha E por palavra, acentos certos.
- `reconstruir.py`: OCR > cor da tinta > medir_texto > fonte (comparador com recorte justo; texto pequeno usa a fonte da marca) > negrito/cor por palavra (salto de densidade de tinta >= 22%; cor da maioria das palavras como base) > `Y.apagarAreas` (fundo limpo por sensível ao conteúdo) > arte.jsx + medidas.json > ciclo.py. Radiologia da Calverstone saiu igual ao post, editável, QA 10/10.
- Erros no caminho: (1) tracking livre no comparador premiava fonte condensada com espaçamento enorme: largura natural voltou a pesar; (2) folga de 35% em volta da caixa do OCR pegava a linha de baixo e estragava a escolha da fonte; (3) a linha com palavras vermelhas era medida só pela cor branca (largura errada em 37 px): medir com todas as cores da linha; (4) logo detectado como texto: lista `--logos`.

## 2026-10-16 04h (f): reconstrutor generalizado em 3 marcas
- Bora Imigrar (médico medo): saiu igual ao post, editável. Precisou: `--zonas` (OCR lia placas da foto: EXIT, 208, ROOMS), fundo da palavra pela moldura 4 px maior (a caixa do Vision encosta na letra e o "fundo" virava verde), corte de tinta a 35% do contraste (verde sobre escuro tem metade do contraste do branco), negrito por espessura de traço (erosão de 1 px: Bold ~0,11-0,16, Regular <= 0,03; a densidade dava negrito falso em fonte fina), blocos de linhas pequenas empilhadas ("Arraste / para o / lado" numa camada com entrelinha medida), fonte por bloco (linhas do mesmo título votam juntas) e recorte justo para o comparador (pela medida, não pela caixa do Vision).
- Bora Comunicação: caixa marca-texto detectada nos pixels (faixas sólidas acima e abaixo das letras) e redesenhada como retângulo editável; cor da tinta escolhida pela FORMA (traço some em erosões de ~22% da altura, mancha da foto sobra). Limite: texto fino branco sobre camisa branca contamina a medida das duas linhas de baixo; ajustes manuais `--fonte-linha`/`--estilo`.
- Radiologia continua igual depois de todas as mudanças (sem regressão).

## 2026-10-16 04h (g): do post real ao template da marca
- `virar_template.py`: lê o PSD reconstruído (tamanho, tracking, posição) + `camadas.json` do reconstruir (fonte-base, negrito, destaque declarados) e gera `template.jsx`; `Y.marcacao` entende `**negrito**` e `{{destaque}}`. Radiologia -> Enfermagem e Fisioterapia, idênticas no estilo (painel em `Calverstone Advisors/design/artes/2026-10-16-reconstrucao-radiologia/painel-template.png`).
- Bug de verdade achado no motor: no `Y.faixas`, os vãos entre faixas não levavam fonte e o Photoshop caía na Myriad Pro ("nos" em Myriad no meio de Montserrat). Agora levam a fonte da camada.
- Negrito por erosão calibrado com caixa refinada: corte fixo 0,12 (Bold 0,15-0,30; Regular até 0,09 com maiúscula inicial).

## 2026-10-16 05h: fundo limpo por difusão (sem mancha) e caixa falsa
- Post azul (13 mil): o sensível ao conteúdo deixava retângulos escuros sobre o degradê. Agora `fundo_por_difusao` (Python) apaga o texto em fundo liso com difusão global (frente de onda, só vizinhos válidos, áreas com textura fora da média); o sensível ao conteúdo fica só para fundo com textura. Critério de "liso" = pouco detalhe fino no anel (imagem menos desfoque de 3 px), porque degradê largo tem variação grande mas detalhe ~0. Resultado: 10 de 11 áreas por difusão, fundo impecável.
- Caixa marca-texto falsa (o próprio fundo azul saturado): a caixa agora precisa ter cor diferente do fundo da linha.
- Área apagada = caixa medida justa + 5 px (a folga do OCR comia logo e emoji vizinhos). Logos com quebra de linha normalizados.
- Erros desta rodada: valor zero de pixel sem vizinho virou "válido" e espalhou preto (corrigido com frente de onda).

## 2026-10-16 05h (b): lote de 10 posts e o que ele ensinou
- Lote em `_laboratorio/lote_reconstrucao.sh` (10 posts de 4 marcas, ~1 min cada). Saíram bem: greencard, o-que-falta, tecnologia, carreira (Bora), AGM, currículo médico; com defeito: jornal, quanto-ganha (texto da foto do celular), visa-bulletin (texto do passaporte), 13 mil.
- Correções:
  - OCR devolve o ângulo da linha; linha torta (> 3°) é texto impresso na foto e fica na imagem.
  - Chave dos alvos só ASCII (L01, L02...): rótulo com acento/travessão não casava depois de passar pelo AppleScript e o texto nascia sem alvo (tamanho 40, no canto).
  - Folga vertical limitada à metade do vão até a linha vizinha; medição do remake com junção mínima e pela linha mais perto do centro esperado (linhas coladas eram medidas juntas e o ciclo divergia).
  - O ciclo guarda o melhor alvo de cada linha, trava correções absurdas e monta o PSD final com os melhores.
  - Negrito por erosão proporcional à altura (texto grande regular passava por negrito).
  - Voto de fonte só entre linhas em que a 1ª fonte de uma está entre as 4 da outra (Light não vota com Bold).
- Em texto de corpo grande (> 56 px no doc), passar `--pequeno 110` para usar a fonte de texto da marca em vez do comparador.

## 2026-10-16 05h (c): segundo lote, 7 de 10 bons
- Bons sem ajuste: 13 mil, greencard, o-que-falta, jornal, tecnologia, carreira, AGM. Com defeito: quanto-ganha (título ATRÁS do celular: o reconstrutor põe o texto por cima; precisa de máscara do objeto, próximo passo), visa-bulletin (fonte fora do padrão da marca), currículo médico (caixa laranja não detectada).
- Novo: nota baixa com o filtro da marca (< 0,6) = post fora do padrão; varre todas as fontes (Visa Bulletin é OwnersXXNarrow-XBlack, não Franklin). Largura natural < 0,93 penaliza (tracking absurdo grudava as palavras: "ASDATASMUDARAM").
- Novo: medida muito maior que a caixa do OCR = objeto da foto da mesma cor encostado (passaporte azul-escuro sob o texto verde-escuro) -> mede na região justa do OCR.
- Novo: glifo que a fonte da marca não tem (→) vai numa faixa com Helvetica Neue (antes virava □).
- Erro meu: `--zonas` do visa estava errado e escondeu o título; o filtro de linha torta (passaporte a -13°) resolve sozinho.

## 2026-10-16 06h: texto atrás de objeto, automático
- `ocultar.py` + `Y.mascaraDeImagem` + `Y.contornoOculto`: "QUANTO GANHA" atrás do celular saiu igual ao post (letras cobertas pelo celular, contorno fantasma sobre a tela), sem nada manual além da correção do OCR (G/INHA=GANHA).
- O fundo agora é apagado só onde há tinta (dilatada 3 px), não no retângulo inteiro: o celular na frente da palavra fica intacto.
- Cor da tinta: entre os grupos com forma de traço e contraste >= 60% do maior, o de maior área (antes o contorno preto do celular vencia o creme das letras).
- Bugs no caminho: ocultar medindo sobre o PNG já mascarado (agora remonta antes), máscara aplicada na cópia de contorno (busca ignora "CONTORNO").

## 2026-10-16 06h (b): caixas empilhadas e oclusão sem falso positivo
- `detectar_caixas` reescrita: fundo da linha pelas bordas esquerda/direita da FAIXA inteira da imagem (caixas empilhadas deixavam topo/base laranjas e a caixa era rejeitada como "fundo"); caixas empilhadas separadas pela mudança de largura linha a linha; bordas laterais retas obrigatórias e sem encostar no recorte (o fundo azul do 13 mil não é mais "caixa"). Currículo médico: duas caixas laranjas certas.
- `ocultar.py`: cobertura medida com tolerância proporcional (tinta do remake com tinta da referência perto) e oclusão só quando a falta está CONCENTRADA num trecho (>= 75% numa janela de 45% da linha). GANHA atrás do celular: 1,00; diferenças de fonte/peso espalhadas: ~0,70 (ignoradas).
- Negrito relativo dentro da linha (mais grossa > 2,2x a mais fina + 0,03).

## 2026-10-16 07h: bancada de fontes (medir em vez de achar)
- `avaliar_fontes.py`: PSDs com camadas de texto (templates de igreja) viram verdade conhecida; recorta cada linha no composto e confere a fonte reconhecida. Primeira medida honesta, sem filtro de marca, varrendo todas as ~4 mil fontes instaladas.
- Resultados (mesmas 29 linhas): comparador antigo 59% exato / 79% top 5 / 66% família; com a etapa fina (render no tamanho real em cinza + correlação com deslocamento) 59% / 79% / **72% família**; com termo de quantidade de tinta 52% (revertido).
- Lições da bancada: (1) caixa alta aplicada por estilo (FontCaps) muda tudo: comparar com o texto como aparece; (2) passar a cor do texto é decisivo (18% -> 49% só com isso e caps); (3) erro que sobra é quase todo PESO vizinho (Medium x Regular, ExtraBold x Black) e famílias gêmeas (Roboto x Metropolis, Montserrat x Brandon) -> na prática usar o filtro da marca + prova de fogo.
