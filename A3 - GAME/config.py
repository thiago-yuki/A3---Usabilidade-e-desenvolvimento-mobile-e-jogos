# Configurações globais do jogo

LARGURA = 960
ALTURA = 540
FPS = 60
TITULO = "A Última Chama de Esparta"

# Cores (R, G, B)
PRETO = (10, 10, 15)
BRANCO = (240, 240, 240)
DOURADO = (230, 170, 40)
VERMELHO = (200, 50, 40)
CINZA = (120, 120, 130)

# Física e jogador (pixels e segundos)
GRAVIDADE = 1800          # px/s²
VELOCIDADE_JOGADOR = 300  # px/s
FORCA_PULO = 650          # px/s (impulso inicial para cima)
VELOCIDADE_QUEDA_MAX = 900

# Mapa
TAMANHO_TILE = 48         # cada caractere do arquivo de mapa vira um quadrado de 48x48 px

# Combate
VIDA_JOGADOR = 5
DANO_ATAQUE = 1
ATAQUE_DURACAO = 0.18      # s que o golpe fica ativo
ATAQUE_RECARGA = 0.35      # s até poder atacar de novo
ATAQUE_ALCANCE = 56        # px à frente do Dáron
TEMPO_INVENCIVEL = 1.0     # s sem levar dano depois de ser atingido
RECUO_X = 260              # empurrão ao levar dano
RECUO_Y = 300
RECUO_INIMIGO = 200

# Habilidades
AVANCO_VELOCIDADE = 720    # px/s durante o avanço
AVANCO_DURACAO = 0.25      # s (≈ 180 px de distância)
AVANCO_RECARGA = 0.7       # s até poder avançar de novo
