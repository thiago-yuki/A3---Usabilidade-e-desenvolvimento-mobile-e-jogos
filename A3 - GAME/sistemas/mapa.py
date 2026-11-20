import os
import config
from entidades.plataforma import Plataforma
from entidades.obstaculos import (
    TroncoCaido,
    GalhosEspinhos,
    VinhaEspinhosa,
    CipoEscalada,
    ArmadilhaCacador,
    LapideAntiga,
)
from entidades.escada import Escada

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELIQUIAS = {"J": "salto_duplo", "A": "avanco"}


class DadosMapa:
    def __init__(self):
        self.plataformas = []    # blocos '#'
        self.barreiras = []      # (x, y, largura, altura) de cada parede 'B'
        self.escadas = []       # objetos Escada de cada coluna 'L' na Fase 2
        self.troncos = []        # TroncoCaido 'L' (sólidos)
        self.espinhos = []       # GalhosEspinhos 'G' (causam dano no chão)
        self.vinhas = []         # VinhaEspinhosa 'V' (causam dano suspensas)
        self.cipos = []          # CipoEscalada 'H' (escaláveis)
        self.armadilhas = []     # ArmadilhaCacador 'M' na Fase 3
        self.lapides = []        # LapideAntiga 'R' (decoração sombria)
        self.inimigos = []       # (x_centro, y_base)
        self.chefe = None        # (x_centro, y_base) para 'M' na Fase 2
        self.zumbis = []         # (x_centro, y_base) dos zumbis caçadores 'Z'
        self.zumbis_brutos = []  # (x_centro, y_base) dos zumbis anciãos 'W'
        self.chefes = []         # (x_centro, y_base) do Guardião da Floresta 'C'
        self.tochas = []         # (x_centro, y_centro) das tochas 'T'
        self.reliquias = []      # (tipo, x_centro, y_centro)
        self.curas = []         # (x_centro, y_centro) para 'H'
        self.powerups = []      # (x_centro, y_centro) para 'T' (tiro triplo)
        self.inicio = None       # (x_centro, y_base)
        self.saida = None        # (x, y, largura, altura) ou None
        self.largura = 0
        self.altura = 0


def _caminho(numero):
    return os.path.join(RAIZ, "mapas", f"fase{numero}.txt")


def existe_fase(numero):
    return os.path.exists(_caminho(numero))


def carregar_mapa(numero):
    """Lê mapas/faseN.txt.

    Legenda:
      #  bloco sólido            P  início                  E  inimigo comum
      Z  zumbi caçador           W  zumbi ancião (bruto)    C  chefe guardião
      T  tocha (iluminação)      L  tronco caído / toco     G  galhos secos/espinhos
      V  vinha espinhosa aérea   H  cipó/raiz de escalada   M  chefe (Fase 2) / armadilha (Fase 3)
      R  lápide antiga / cruz    B  barreira rachada        S  saída (portal)
      J  relíquia salto duplo    A  relíquia avanço         .  vazio
    """
    with open(_caminho(numero), encoding="utf-8") as arquivo:
        linhas = [l.rstrip("\n") for l in arquivo if not l.startswith(";")]

    t = config.TAMANHO_TILE
    colunas = max(len(l) for l in linhas)
    linhas = [l.ljust(colunas, ".") for l in linhas]

    dados = DadosMapa()
    dados.inicio = (t, t * 2)
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
            if ch == "L":
                if numero == 2:
                    c += 1
                else:
                    ini = c
                    while c < colunas and linha[c] == "L":
                        c += 1
                    dados.troncos.append(TroncoCaido(ini * t, r * t, (c - ini) * t, t))
                continue
            if ch == "G":
                ini = c
                while c < colunas and linha[c] == "G":
                    c += 1
                dados.espinhos.append(GalhosEspinhos(ini * t, (r + 1) * t, (c - ini) * t))
                continue
            if ch == "M":
                posicao = (c * t + t // 2, (r + 1) * t)
                if numero == 2:
                    dados.chefe = posicao
                else:
                    dados.armadilhas.append(ArmadilhaCacador(*posicao))
            elif ch == "P":
                dados.inicio = (c * t + t // 2, (r + 1) * t)
            elif ch == "E":
                dados.inimigos.append((c * t + t // 2, (r + 1) * t))
            elif ch == "Z":
                dados.zumbis.append((c * t + t // 2, (r + 1) * t))
            elif ch == "W":
                dados.zumbis_brutos.append((c * t + t // 2, (r + 1) * t))
            elif ch == "C":
                dados.chefes.append((c * t + t // 2, (r + 1) * t))
            elif ch == "T":
                dados.tochas.append((c * t + t // 2, r * t + t // 2))
            elif ch == "R":
                dados.lapides.append(LapideAntiga(c * t + t // 2, (r + 1) * t, variante=c + r))
            elif ch == "H":
                dados.curas.append((c * t + t // 2, r * t + t // 2))
            elif ch == "T":
                dados.powerups.append((c * t + t // 2, r * t + t // 2))
            elif ch in RELIQUIAS:
                dados.reliquias.append((RELIQUIAS[ch], c * t + t // 2, r * t + t // 2))
            elif ch == "S":
                dados.saida = (c * t, (r + 1) * t - 2 * t, t, 2 * t)
            c += 1

    # barreiras ('B'), vinhas espinhosas ('V') e cipós de escalada ('H') empilhados na coluna
    # Barreiras ('B') e Escadas ('L') empilhadas na mesma coluna
    for c in range(colunas):
        r = 0
        while r < len(linhas):
            ch = linhas[r][c]
            if ch == "B":
                ini = r
                while r < len(linhas) and linhas[r][c] == "B":
                    r += 1
                dados.barreiras.append((c * t, ini * t, t, (r - ini) * t))
            elif ch == "V":
                ini = r
                while r < len(linhas) and linhas[r][c] == "V":
                    r += 1
                dados.vinhas.append(VinhaEspinhosa(c * t, ini * t, t, (r - ini) * t))
            elif ch == "H":
                ini = r
                while r < len(linhas) and linhas[r][c] == "H":
                    r += 1
                dados.cipos.append(CipoEscalada(c * t + t // 2, ini * t, (r - ini) * t))
            elif numero == 2 and linhas[r][c] == "L":
                ini = r
                while r < len(linhas) and linhas[r][c] == "L":
                    r += 1
                dados.escadas.append(Escada(c * t, ini * t, t, (r - ini) * t))
            else:
                r += 1

    return dados