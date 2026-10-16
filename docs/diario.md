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
