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
