import os
import config
from entidades.plataforma import Plataforma

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELIQUIAS = {"J": "salto_duplo", "A": "avanco"}


class DadosMapa:
    def __init__(self):
        self.plataformas = []   # blocos '#'
        self.barreiras = []     # (x, y, largura, altura) de cada parede 'B'
        self.inimigos = []      # (x_centro, y_base)
        self.reliquias = []     # (tipo, x_centro, y_centro)
        self.inicio = None      # (x_centro, y_base)
        self.saida = None       # (x, y, largura, altura) ou None
        self.largura = 0
        self.altura = 0


def _caminho(numero):
    return os.path.join(RAIZ, "mapas", f"fase{numero}.txt")


def existe_fase(numero):
    return os.path.exists(_caminho(numero))


def carregar_mapa(numero):
    """Lê mapas/faseN.txt.

    Legenda:
      #  bloco sólido            P  início do Dáron        E  inimigo comum
      B  barreira rachada        S  saída (portal)         .  vazio
      J  relíquia do salto duplo A  relíquia do avanço     ;  comentário
    Barreiras ocupam 1 coluna; colunas seguidas de 'B' formam uma só parede.
    O portal 'S' ocupa o tile marcado e o de cima.
    """
    with open(_caminho(numero), encoding="utf-8") as arquivo:
        linhas = [l.rstrip("\n") for l in arquivo if not l.startswith(";")]

    t = config.TAMANHO_TILE
    colunas = max(len(l) for l in linhas)
    linhas = [l.ljust(colunas, ".") for l in linhas]

    dados = DadosMapa()
    dados.inicio = (t, t * 2)  # padrão, caso o mapa não tenha 'P'
    dados.largura = colunas * t
    dados.altura = len(linhas) * t

    for r, linha in enumerate(linhas):
        c = 0
        while c < colunas:
            ch = linha[c]
            if ch == "#":
                ini = c
                while c < colunas and linha[c] == "#":
                    c += 1
                dados.plataformas.append(Plataforma(ini * t, r * t, (c - ini) * t, t))
                continue
            if ch == "P":
                dados.inicio = (c * t + t // 2, (r + 1) * t)
            elif ch == "E":
                dados.inimigos.append((c * t + t // 2, (r + 1) * t))
            elif ch in RELIQUIAS:
                dados.reliquias.append((RELIQUIAS[ch], c * t + t // 2, r * t + t // 2))
            elif ch == "S":
                dados.saida = (c * t, (r + 1) * t - 2 * t, t, 2 * t)
            c += 1

    # barreiras: junta 'B' empilhados na mesma coluna
    for c in range(colunas):
        r = 0
        while r < len(linhas):
            if linhas[r][c] == "B":
                ini = r
                while r < len(linhas) and linhas[r][c] == "B":
                    r += 1
                dados.barreiras.append((c * t, ini * t, t, (r - ini) * t))
            else:
                r += 1

    return dados
