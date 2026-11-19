
import os
import config
from entidades.plataforma import Plataforma

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELIQUIAS = {"J": "salto_duplo", "A": "avanco"}


class DadosMapa:
    def __init__(self):
        self.plataformas = []   # blocos '#'
        self.barreiras = []     # (x, y, largura, altura)
        self.inimigos = []      # (x_centro, y_base)
        self.reliquias = []     # (tipo, x_centro, y_centro)
        self.inicio = None      # (x_centro, y_base)
        self.saida = None       # (x, y, largura, altura)
        self.largura = 0
        self.altura = 0


def _caminho(numero):
    return os.path.join(RAIZ, "mapas", f"fase{numero}.txt")


def existe_fase(numero):
    caminho = _caminho(numero)
    return os.path.isfile(caminho)


def carregar_mapa(numero):
    """Lê mapas/faseN.txt.

    Legenda:
      #  bloco sólido
      P  início do jogador
      E  inimigo comum
      B  barreira
      S  saída
      .  vazio
      J  relíquia do salto duplo
      A  relíquia do avanço
      ;  comentário

    Barreiras ocupam 1 coluna; colunas seguidas de 'B' formam
    uma só parede.
    O portal 'S' ocupa o tile marcado e o de cima.
    """

    caminho = _caminho(numero)

    # Verifica se o arquivo existe
    if not os.path.isfile(caminho):
        raise FileNotFoundError(
            f"Não foi encontrado o mapa da fase {numero}:\n{caminho}"
        )

    # Lê o arquivo e ignora comentários e linhas vazias
    with open(caminho, "r", encoding="utf-8-sig") as arquivo:
        linhas = []

        for linha in arquivo:
            linha = linha.rstrip("\r\n")

            # Ignora linhas vazias
            if not linha.strip():
                continue

            # Ignora comentários
            if linha.lstrip().startswith(";"):
                continue

            linhas.append(linha)

    # Impede que max() seja executado com uma lista vazia
    if not linhas:
        raise ValueError(
            f"O mapa da fase {numero} está vazio ou contém apenas comentários.\n"
            f"Verifique o arquivo: {caminho}"
        )

    t = config.TAMANHO_TILE

    # Descobre a maior quantidade de colunas
    colunas = max(len(linha) for linha in linhas)

    # Completa as linhas menores com espaços vazios
    linhas = [linha.ljust(colunas, ".") for linha in linhas]

    dados = DadosMapa()

    # Posição padrão caso o mapa não tenha um P
    dados.inicio = (t, t * 2)

    dados.largura = colunas * t
    dados.altura = len(linhas) * t

    # Lê os elementos do mapa
    for r, linha in enumerate(linhas):
        c = 0

        while c < colunas:
            ch = linha[c]

            # Plataformas
            if ch == "#":
                ini = c

                while c < colunas and linha[c] == "#":
                    c += 1

                dados.plataformas.append(
                    Plataforma(
                        ini * t,
                        r * t,
                        (c - ini) * t,
                        t
                    )
                )

                continue

            # Posição inicial do jogador
            if ch == "P":
                dados.inicio = (
                    c * t + t // 2,
                    (r + 1) * t
                )

            # Inimigos
            elif ch == "E":
                dados.inimigos.append(
                    (
                        c * t + t // 2,
                        (r + 1) * t
                    )
                )

            # Relíquias
            elif ch in RELIQUIAS:
                dados.reliquias.append(
                    (
                        RELIQUIAS[ch],
                        c * t + t // 2,
                        r * t + t // 2
                    )
                )

            # Saída da fase
            elif ch == "S":
                dados.saida = (
                    c * t,
                    (r + 1) * t - 2 * t,
                    t,
                    2 * t
                )

            c += 1

    # Identifica e agrupa barreiras empilhadas
    for c in range(colunas):
        r = 0

        while r < len(linhas):

            if linhas[r][c] == "B":
                ini = r

                while r < len(linhas) and linhas[r][c] == "B":
                    r += 1

                dados.barreiras.append(
                    (
                        c * t,
                        ini * t,
                        t,
                        (r - ini) * t
                    )
                )

            else:
                r += 1

    return dados
