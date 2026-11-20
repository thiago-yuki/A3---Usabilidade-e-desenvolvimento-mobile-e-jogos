"""Coordenadas do cenário da batalha final (em pixels da tela lógica 1280x720).
Usado pela cena e pelo gerador do fundo (ferramentas/gerar_fundo.py)."""

LARGURA = 1280
ALTURA = 720
CHAO_Y = 640                      # topo do chão

# Vão da porta do castelo: x, y, largura, altura (arco no topo)
PORTA = (1072, 520, 80, 120)
PORTA_CENTRO_X = 1112

# Janelas da torre principal (cx, cy, largura, altura), de baixo para cima
JANELAS_TORRE = [(1215, 548, 26, 44), (1215, 452, 26, 44),
                 (1215, 356, 26, 44), (1215, 262, 26, 44)]
# Janela do alto, onde a princesa aparece
JANELA_PRINCESA = (1215, 168, 56, 84)

# Tochas ao lado da porta (x, y)
TOCHAS = [(1062, 556), (1162, 556)]
