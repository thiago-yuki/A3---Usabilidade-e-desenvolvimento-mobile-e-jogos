# Configurações globais do jogo

LARGURA = 960
ALTURA = 540
FPS = 60
TITULO = "Falling in Fears"

# Cores (R, G, B)
PRETO = (10, 10, 15)
BRANCO = (240, 240, 240)
DOURADO = (230, 170, 40)
VERMELHO = (200, 50, 40)
CINZA = (120, 120, 130)
VERDE_ZUMBI = (95, 205, 65)

# Física e jogador (pixels e segundos)
GRAVIDADE = 1800          # px/s²
VELOCIDADE_JOGADOR = 300  # px/s
FORCA_PULO = 650          # px/s (impulso inicial para cima)
VELOCIDADE_QUEDA_MAX = 900

# Mapa
TAMANHO_TILE = 48         # cada caractere do arquivo de mapa vira um quadrado de 48x48 px

# Combate e Arma (Calibre 12)
VIDA_JOGADOR = 3          # 3 pontos de vida por fase
DANO_ATAQUE = 1           # dano por chumbinho da 12
ATAQUE_DURACAO = 0.14     # s do clarão do disparo
ATAQUE_RECARGA = 0.55     # s até poder atirar com a 12 de novo
TIRO_VELOCIDADE = 820     # px/s dos chumbinhos da 12
TIRO_ALCANCE = 230        # px de alcance máximo da 12
TIRO_PROJETEIS = 4        # quantidade de chumbinhos por disparo
TEMPO_INVENCIVEL = 1.0    # s sem levar dano depois de ser atingido
RECUO_X = 260             # empurrão ao levar dano
RECUO_Y = 300
RECUO_INIMIGO = 180

# Habilidades
AVANCO_VELOCIDADE = 720   # px/s durante o avanço
AVANCO_DURACAO = 0.25     # s (≈ 180 px de distância)
AVANCO_RECARGA = 0.7      # s até poder avançar de novo