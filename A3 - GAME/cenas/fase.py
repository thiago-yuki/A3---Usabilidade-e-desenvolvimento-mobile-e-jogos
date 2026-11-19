import pygame
import os
import math
import random
import config

from nucleo.cena import Cena
from nucleo.camera import Camera
from entidades.jogador import Jogador
from entidades.inimigos_comuns import GuerreiroCorrompido
from entidades.reliquia import Reliquia
from entidades.barreira import Barreira
from entidades.saida import Saida
from sistemas.mapa import carregar_mapa, existe_fase
from sistemas.hud import Hud


FUNDOS = {
    1: (25, 20, 30),
    2: (17, 25, 42),
    3: (12, 27, 19),
    4: (28, 13, 18)
}


class Fase(Cena):

    def __init__(self, jogo, numero=1):
        super().__init__(jogo)

        self.numero = numero
        self.fonte_msg = pygame.font.Font(None, 40)
        self.fonte_msg2 = pygame.font.Font(None, 28)

        # ==========================================
        # CARREGAMENTO DOS FUNDOS
        # ==========================================

        raiz_projeto = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        nomes_fundos = {
            1: ["fundo_fase1.png"],
            2: ["fundo_fase2.jpeg"],
            3: [
                "fundo_fase3.png",
                "fundo_fase3.jpeg",
                "fundo_fase3.jpg",
                "fundo_fase3.jfif"
            ],
            4: ["fundofase4.jpeg"]
        }

        self.imagem_base = None

        for nome in nomes_fundos.get(numero, []):

            caminho = os.path.join(
                raiz_projeto,
                "assets",
                nome
            )

            if os.path.exists(caminho):
                self.imagem_base = pygame.image.load(
                    caminho
                ).convert()

                self.imagem_base = pygame.transform.smoothscale(
                    self.imagem_base,
                    (config.LARGURA, config.ALTURA)
                )

                break

        # ==========================================
        # CARREGAMENTO DO MAPA
        # ==========================================

        dados = carregar_mapa(numero)

        self.largura = dados.largura
        self.altura = dados.altura

        self.plataformas = dados.plataformas

        self.barreiras = [
            Barreira(*b) for b in dados.barreiras
        ]

        self.solidos = self.plataformas + self.barreiras

        self.saida = (
            Saida(*dados.saida)
            if dados.saida else None
        )

        self.inimigos = [
            GuerreiroCorrompido(x, y)
            for x, y in dados.inimigos
        ]

        self.reliquias = [
            Reliquia(t, x, y)
            for t, x, y in dados.reliquias
            if t not in jogo.habilidades
        ]

        # ==========================================
        # JOGADOR
        # ==========================================

        x, y = dados.inicio

        self.jogador = Jogador(
            x - Jogador.LARGURA // 2,
            y - Jogador.ALTURA
        )

        for habilidade in jogo.habilidades:
            self.jogador.desbloquear(habilidade)

        # ==========================================
        # CÂMERA E HUD
        # ==========================================

        self.camera = Camera(
            self.largura,
            self.altura
        )

        self.camera.centralizar(self.jogador.rect)

        self.hud = Hud()

        self.mensagem = None
        self.tempo_mensagem = 0.0
        self.dicas = set()

        # ==========================================
        # ELEMENTOS VISUAIS
        # ==========================================

        self.fundo_panorama = None
        self.largura_panorama = 0
        self.fator_fundo = 0

        # Fase 1
        self.vegetacao = []
        self.lanternas = []
        self.particulas = []

        # Fase 2
        self.decoracoes_cemiterio = []
        self.almas = []
        self.luzes_cemiterio = []

        # Fase 3
        self.decoracoes_floresta = []
        self.sapos_floresta = []
        self.macas_flutuantes = []
        self.fantasmas_floresta = []
        self.esporos_verdes = []
        self.caveiras_floresta = []

        # Fase 4
        self.nevoas_fase4 = []
        self.brasas_fase4 = []
        self.esporos_fase4 = []

        # Prepara somente o cenário correspondente
        if self.numero == 1:
            self._preparar_cenario()

        elif self.numero == 2:
            self._preparar_cenario_fase2()

        elif self.numero == 3:
            self._preparar_cenario_fase3()

        elif self.numero == 4:
            self._preparar_cenario_fase4()

    # ==============================================
    # CRIAÇÃO DO PANORAMA
    # ==============================================

    def _montar_panorama(self, tonalidades):

        largura_tela = config.LARGURA
        altura_tela = config.ALTURA

        self.largura_panorama = largura_tela * 3

        self.fundo_panorama = pygame.Surface(
            (self.largura_panorama, altura_tela)
        )

        for regiao in range(3):

            inicio = regiao * largura_tela

            if self.imagem_base:

                imagem = self.imagem_base

                if regiao == 1:
                    imagem = pygame.transform.flip(
                        imagem,
                        True,
                        False
                    )

                self.fundo_panorama.blit(
                    imagem,
                    (inicio, 0)
                )

            else:

                self.fundo_panorama.fill(
                    FUNDOS.get(self.numero, (12, 27, 19)),
                    (inicio, 0, largura_tela, altura_tela)
                )

            filtro = pygame.Surface(
                (largura_tela, altura_tela),
                pygame.SRCALPHA
            )

            filtro.fill(tonalidades[regiao])

            self.fundo_panorama.blit(
                filtro,
                (inicio, 0)
            )

        distancia_camera = max(
            1,
            self.largura - config.LARGURA
        )

        self.fator_fundo = (
            self.largura_panorama - config.LARGURA
        ) / distancia_camera

    # ==============================================
    # PREPARAÇÃO DA FASE 1
    # ==============================================

    def _preparar_cenario(self):

        self._montar_panorama([
            (48, 18, 69, 30),
            (20, 39, 75, 48),
            (20, 47, 35, 62)
        ])

        self._desenhar_arvores_fundo(
            self.fundo_panorama,
            0,
            quantidade=4,
            altura_min=105,
            altura_max=165
        )

        self._desenhar_ruinas(
            self.fundo_panorama,
            config.LARGURA
        )

        self._desenhar_arvores_fundo(
            self.fundo_panorama,
            config.LARGURA * 2,
            quantidade=8,
            altura_min=150,
            altura_max=230
        )

        gerador = random.Random(37)
        tamanho_tile = config.TAMANHO_TILE

        for plataforma in self.plataformas:

            if plataforma.rect.top < self.altura - 2 * tamanho_tile:
                continue

            if plataforma.rect.width < 130:
                continue

            posicao = plataforma.rect.left + 40

            while posicao < plataforma.rect.right - 25:

                tipo = gerador.choice([
                    "arbusto",
                    "flor",
                    "cogumelo",
                    "pedra"
                ])

                escala = gerador.uniform(0.75, 1.15)

                self.vegetacao.append((
                    posicao,
                    plataforma.rect.top,
                    tipo,
                    escala
                ))

                posicao += gerador.randint(145, 210)

        self.lanternas = [
            (x, y)
            for x, y in [
                (330, 330),
                (1050, 315),
                (1850, 305),
                (2650, 325),
                (3450, 300),
                (4050, 320)
            ]
            if x < self.largura
        ]

        gerador_particulas = random.Random(92)

        for _ in range(34):

            self.particulas.append((
                gerador_particulas.uniform(0, self.largura),
                gerador_particulas.uniform(210, 435),
                gerador_particulas.uniform(0, math.pi * 2),
                gerador_particulas.uniform(0.7, 1.8)
            ))

    # ==============================================
    # ÁRVORES DA FASE 1
    # ==============================================

    def _desenhar_arvores_fundo(
        self,
        tela,
        inicio,
        quantidade=5,
        altura_min=120,
        altura_max=190
    ):

        gerador = random.Random(
            int(inicio) + quantidade
        )

        for _ in range(quantidade):

            x = inicio + gerador.randint(
                45,
                config.LARGURA - 45
            )

            base = gerador.randint(410, 470)

            altura = gerador.randint(
                altura_min,
                altura_max
            )

            cor_tronco = (29, 24, 43)
            cor_copa = (35, 27, 51)

            pygame.draw.polygon(
                tela,
                cor_tronco,
                [
                    (x - 7, base),
                    (x + 8, base),
                    (x + 3, base - altura),
                    (x - 3, base - altura + 15)
                ]
            )

            pygame.draw.lines(
                tela,
                cor_tronco,
                False,
                [
                    (x, base - altura // 2),
                    (x - 25, base - altura + 35),
                    (x - 40, base - altura + 20)
                ],
                7
            )

            pygame.draw.lines(
                tela,
                cor_tronco,
                False,
                [
                    (x, base - altura // 2 + 15),
                    (x + 25, base - altura + 45),
                    (x + 43, base - altura + 24)
                ],
                7
            )

            pygame.draw.circle(
                tela,
                cor_copa,
                (x - 19, base - altura + 30),
                30
            )

            pygame.draw.circle(
                tela,
                cor_copa,
                (x + 19, base - altura + 25),
                32
            )

            pygame.draw.circle(
                tela,
                cor_copa,
                (x, base - altura + 5),
                34
            )

    # ==============================================
    # RUÍNAS DA FASE 1
    # ==============================================

    def _desenhar_ruinas(self, tela, inicio):

        cor_pedra = (53, 49, 70)
        cor_clara = (76, 69, 91)
        cor_agua = (110, 147, 177)

        for x, altura in [
            (inicio + 150, 145),
            (inicio + 690, 165)
        ]:

            base = 440

            pygame.draw.rect(
                tela,
                cor_pedra,
                (x, base - altura, 27, altura)
            )

            pygame.draw.rect(
                tela,
                cor_clara,
                (x - 7, base - altura - 9, 41, 13)
            )

            pygame.draw.rect(
                tela,
                cor_clara,
                (x - 4, base - 6, 35, 8)
            )

            pygame.draw.line(
                tela,
                (97, 88, 111),
                (x + 5, base - altura + 15),
                (x + 5, base - 15),
                2
            )

        pygame.draw.arc(
            tela,
            cor_pedra,
            (inicio + 160, 205, 560, 350),
            math.pi,
            math.pi * 2,
            12
        )

        x_cachoeira = inicio + 480

        for i in range(9):

            x = x_cachoeira + i * 13

            pygame.draw.line(
                tela,
                cor_agua,
                (x, 245),
                (x + 2, 425),
                2 if i % 3 else 4
            )

        for i in range(5):

            x = x_cachoeira + 20 + i * 22

            pygame.draw.line(
                tela,
                (147, 168, 190),
                (x, 290),
                (x + 1, 400),
                1
            )

    # ==============================================
    # PREPARAÇÃO DA FASE 2
    # ==============================================

    def _preparar_cenario_fase2(self):

        self._montar_panorama([
            (12, 26, 48, 48),
            (19, 28, 48, 75),
            (9, 17, 36, 100)
        ])

        for regiao in range(3):

            self._desenhar_cemiterio_distante(
                self.fundo_panorama,
                regiao * config.LARGURA,
                regiao
            )

        gerador = random.Random(202)
        altura_chao = self.altura - 2 * config.TAMANHO_TILE

        for plataforma in self.plataformas:

            if plataforma.rect.top != altura_chao:
                continue

            if plataforma.rect.width < 150:
                continue

            posicao = plataforma.rect.left + 105

            while posicao < plataforma.rect.right - 25:

                tipo = gerador.choice([
                    "lapide",
                    "lapide",
                    "galho"
                ])

                self.decoracoes_cemiterio.append((
                    posicao,
                    plataforma.rect.top,
                    tipo,
                    gerador.uniform(0.85, 1.15)
                ))

                posicao += gerador.randint(220, 290)

        gerador_almas = random.Random(73)

        for _ in range(26):

            self.almas.append((
                gerador_almas.uniform(0, self.largura),
                gerador_almas.uniform(175, 480),
                gerador_almas.uniform(0, math.pi * 2),
                gerador_almas.uniform(0.6, 1.5),
                gerador_almas.randint(8, 15)
            ))

        self.luzes_cemiterio = [
            (x, y)
            for x, y in [
                (420, 445),
                (1080, 400),
                (1740, 450),
                (2360, 410),
                (3100, 445),
                (3650, 400)
            ]
            if x < self.largura
        ]

    # ==============================================
    # CEMITÉRIO AO FUNDO
    # ==============================================

    def _desenhar_cemiterio_distante(
        self,
        tela,
        inicio,
        regiao
    ):

        gerador = random.Random(400 + regiao)

        cor_arvore = (14, 20, 34)
        cor_pedra = (28, 37, 56)
        cor_detalhe = (46, 61, 79)

        if regiao == 0:

            pygame.draw.circle(
                tela,
                (142, 159, 180),
                (inicio + 760, 105),
                36
            )

            pygame.draw.circle(
                tela,
                (169, 184, 199),
                (inicio + 750, 96),
                27
            )

        for _ in range(5 if regiao != 2 else 7):

            x = inicio + gerador.randint(45, 900)
            base = gerador.randint(415, 490)
            altura = gerador.randint(125, 230)

            pygame.draw.lines(
                tela,
                cor_arvore,
                False,
                [
                    (x, base),
                    (x - 5, base - altura // 2),
                    (x + 1, base - altura)
                ],
                8
            )

            pygame.draw.lines(
                tela,
                cor_arvore,
                False,
                [
                    (x - 2, base - altura // 2),
                    (x - 32, base - altura + 34),
                    (x - 55, base - altura + 18)
                ],
                5
            )

            pygame.draw.lines(
                tela,
                cor_arvore,
                False,
                [
                    (x, base - altura + 44),
                    (x + 28, base - altura + 70),
                    (x + 49, base - altura + 54)
                ],
                5
            )

        for _ in range(8):

            x = inicio + gerador.randint(20, 920)
            base = gerador.randint(455, 490)

            largura = gerador.randint(13, 24)
            altura = gerador.randint(25, 48)

            lapide = pygame.Rect(
                x,
                base - altura,
                largura,
                altura
            )

            pygame.draw.rect(
                tela,
                cor_pedra,
                lapide,
                border_radius=6
            )

            pygame.draw.ellipse(
                tela,
                cor_pedra,
                (x, base - altura - 5, largura, 14)
            )

        if regiao == 1:

            base = 455

            for x in [inicio + 290, inicio + 630]:

                pygame.draw.rect(
                    tela,
                    cor_pedra,
                    (x, base - 190, 46, 190)
                )

                pygame.draw.rect(
                    tela,
                    cor_detalhe,
                    (x - 9, base - 200, 64, 17)
                )

            pygame.draw.arc(
                tela,
                cor_detalhe,
                (inicio + 270, 140, 440, 270),
                math.pi,
                math.pi * 2,
                15
            )

            pygame.draw.rect(
                tela,
                cor_pedra,
                (inicio + 320, 265, 360, 190)
            )

            pygame.draw.rect(
                tela,
                (14, 20, 34),
                (inicio + 430, 322, 135, 133)
            )

        if regiao == 2:

            x = inicio + 360
            base = 465

            pygame.draw.rect(
                tela,
                cor_pedra,
                (x, base - 120, 240, 120)
            )

            pygame.draw.polygon(
                tela,
                cor_detalhe,
                [
                    (x - 25, base - 120),
                    (x + 120, base - 185),
                    (x + 265, base - 120)
                ]
            )

            pygame.draw.rect(
                tela,
                (12, 18, 31),
                (x + 87, base - 85, 65, 85)
            )

    # ==============================================
    # PREPARAÇÃO DA FASE 3
    # ==============================================

    def _preparar_cenario_fase3(self):

        self._montar_panorama([
            (18, 51, 28, 38),
            (14, 43, 24, 62),
            (7, 26, 15, 90)
        ])

        for regiao in range(3):

            self._desenhar_floresta_distante(
                self.fundo_panorama,
                regiao * config.LARGURA,
                regiao
            )

        gerador = random.Random(303)

        altura_chao = (
            self.altura
            - 2 * config.TAMANHO_TILE
        )

        for plataforma in self.plataformas:

            if plataforma.rect.top != altura_chao:
                continue

            if plataforma.rect.width < 110:
                continue

            posicao = plataforma.rect.left + 45

            while posicao < plataforma.rect.right - 20:

                tipo = gerador.choice([
                    "raiz",
                    "cogumelo",
                    "pedra",
                    "caveira",
                    "flor"
                ])

                escala = gerador.uniform(0.8, 1.2)

                self.decoracoes_floresta.append((
                    posicao,
                    plataforma.rect.top,
                    tipo,
                    escala
                ))

                posicao += gerador.randint(130, 205)

        self.sapos_floresta = [
            (420, 390, 0.2),
            (1150, 350, 1.3),
            (1960, 400, 2.1),
            (2750, 350, 3.0),
            (3540, 385, 4.2)
        ]

        gerador_macas = random.Random(404)

        for _ in range(19):

            self.macas_flutuantes.append((
                gerador_macas.randint(120, self.largura - 100),
                gerador_macas.randint(210, 470),
                gerador_macas.uniform(0, math.pi * 2),
                gerador_macas.randint(8, 13),
                gerador_macas.choice(["vermelha", "verde"])
            ))

        gerador_fantasmas = random.Random(505)

        for _ in range(17):

            self.fantasmas_floresta.append((
                gerador_fantasmas.randint(50, self.largura - 50),
                gerador_fantasmas.randint(175, 465),
                gerador_fantasmas.uniform(0, math.pi * 2),
                gerador_fantasmas.uniform(0.6, 1.7),
                gerador_fantasmas.randint(9, 15)
            ))

        self.caveiras_floresta = [
            (700, 420, 1.15),
            (1550, 390, 0.9),
            (2380, 420, 1.2),
            (3260, 390, 1.05)
        ]

        gerador_esporos = random.Random(606)

        for _ in range(55):

            self.esporos_verdes.append((
                gerador_esporos.uniform(0, self.largura),
                gerador_esporos.uniform(130, 520),
                gerador_esporos.uniform(0, math.pi * 2),
                gerador_esporos.uniform(0.5, 1.8),
                gerador_esporos.randint(1, 3)
            ))

    # ==============================================
    # ÁRVORES E SILHUETAS DA FLORESTA
    # ==============================================

    def _desenhar_floresta_distante(
        self,
        tela,
        inicio,
        regiao
    ):

        gerador = random.Random(800 + regiao)

        cores_troncos = [
            (21, 39, 28),
            (16, 34, 26),
            (10, 25, 20)
        ]

        cor_tronco = cores_troncos[regiao]
        cor_raiz = (28, 50, 32)
        cor_copa = (13, 32, 20)

        quantidade = [5, 7, 9][regiao]

        for _ in range(quantidade):

            x = inicio + gerador.randint(35, 925)
            base = gerador.randint(430, 495)

            altura = gerador.randint(
                155 + regiao * 12,
                235 + regiao * 18
            )

            largura_tronco = gerador.randint(12, 23)

            pygame.draw.polygon(
                tela,
                cor_tronco,
                [
                    (x - largura_tronco // 2, base),
                    (x + largura_tronco // 2, base),
                    (x + 5, base - altura),
                    (x - 4, base - altura + 12)
                ]
            )

            pygame.draw.lines(
                tela,
                cor_tronco,
                False,
                [
                    (x, base - altura // 2),
                    (x - 25, base - altura + 60),
                    (x - 65, base - altura + 35),
                    (x - 80, base - altura + 15)
                ],
                7
            )

            pygame.draw.lines(
                tela,
                cor_tronco,
                False,
                [
                    (x, base - altura // 2 + 25),
                    (x + 28, base - altura + 80),
                    (x + 63, base - altura + 55),
                    (x + 78, base - altura + 30)
                ],
                7
            )

            pygame.draw.lines(
                tela,
                cor_raiz,
                False,
                [
                    (x, base - 4),
                    (x - 23, base - 18),
                    (x - 45, base - 14)
                ],
                6
            )

            pygame.draw.lines(
                tela,
                cor_raiz,
                False,
                [
                    (x, base - 4),
                    (x + 19, base - 18),
                    (x + 42, base - 13)
                ],
                6
            )

            if regiao == 2:

                pygame.draw.circle(
                    tela,
                    cor_copa,
                    (x - 28, base - altura + 32),
                    25
                )

                pygame.draw.circle(
                    tela,
                    cor_copa,
                    (x + 28, base - altura + 42),
                    27
                )

        if regiao >= 1:

            for _ in range(5):

                x = inicio + gerador.randint(40, 900)
                y = gerador.randint(465, 490)

                pygame.draw.ellipse(
                    tela,
                    (34, 49, 40),
                    (x - 9, y - 24, 18, 26)
                )

                pygame.draw.rect(
                    tela,
                    (34, 49, 40),
                    (x - 9, y - 12, 18, 12)
                )

        if regiao == 2:

            self._desenhar_caveira(
                tela,
                inicio + 470,
                335,
                1.8,
                (79, 95, 75),
                brilho=False
            )

        if regiao == 1:

            for x in [inicio + 180, inicio + 760]:

                pygame.draw.ellipse(
                    tela,
                    (44, 91, 54),
                    (x - 23, 405, 46, 16)
                )

                pygame.draw.rect(
                    tela,
                    (51, 77, 52),
                    (x - 5, 378, 10, 30)
                )

                pygame.draw.ellipse(
                    tela,
                    (85, 145, 64),
                    (x - 26, 366, 52, 23)
                )

    # ==============================================
    # NÉVOA DA FLORESTA
    # ==============================================

    def _desenhar_nevoa_floresta(self, tela):

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        deslocamento = int(
            tempo * 10 + self.camera.x * 0.15
        ) % (config.LARGURA + 300)

        for i in range(7):

            x = (
                i * 180 - deslocamento
            ) % (config.LARGURA + 380) - 190

            y = int(
                365 + math.sin(tempo * 0.4 + i) * 17
            )

            pygame.draw.ellipse(
                camada,
                (102, 153, 82, 31),
                (x, y, 240, 58)
            )

        deslocamento2 = int(
            tempo * 6 + self.camera.x * 0.08
        ) % (config.LARGURA + 350)

        for i in range(5):

            x = (
                i * 255 - deslocamento2
            ) % (config.LARGURA + 400) - 200

            y = int(
                290 + math.sin(tempo * 0.3 + i) * 20
            )

            pygame.draw.ellipse(
                camada,
                (91, 134, 93, 19),
                (x, y, 270, 62)
            )

        for i in range(8):

            x = int(
                (i * 123 + tempo * 9)
                % config.LARGURA
            )

            y = int(
                395 + math.sin(tempo * 0.8 + i) * 15
            )

            pygame.draw.circle(
                camada,
                (126, 191, 85, 28),
                (x, y),
                16
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # MAÇÃS ENVENENADAS FLUTUANTES
    # ==============================================

    def _desenhar_macas_envenenadas(self, tela):

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for mundo_x, mundo_y, fase, tamanho, tipo in self.macas_flutuantes:

            x = int(
                mundo_x - self.camera.x * 0.86
                + math.sin(tempo * 0.6 + fase) * 7
            )

            y = int(
                mundo_y - self.camera.y * 0.20
                + math.sin(tempo * 1.3 + fase) * 12
            )

            if x < -30 or x > config.LARGURA + 30:
                continue

            cor = (
                (174, 47, 48, 225)
                if tipo == "vermelha"
                else (101, 164, 54, 225)
            )

            pygame.draw.circle(
                camada,
                (113, 205, 63, 30),
                (x, y),
                tamanho + 13
            )

            pygame.draw.circle(
                camada,
                (110, 181, 68, 45),
                (x, y),
                tamanho + 8
            )

            pygame.draw.circle(
                camada,
                cor,
                (x - 4, y),
                tamanho
            )

            pygame.draw.circle(
                camada,
                cor,
                (x + 4, y),
                tamanho
            )

            pygame.draw.ellipse(
                camada,
                cor,
                (x - tamanho, y - 2, tamanho * 2, tamanho + 7)
            )

            pygame.draw.circle(
                camada,
                (220, 238, 122, 175),
                (x - 4, y - 5),
                max(2, tamanho // 3)
            )

            pygame.draw.line(
                camada,
                (71, 51, 31, 255),
                (x, y - tamanho + 2),
                (x + 2, y - tamanho - 5),
                2
            )

            pygame.draw.ellipse(
                camada,
                (91, 174, 60, 245),
                (x + 2, y - tamanho - 7, 9, 5)
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # SAPOS VERMELHOS DA PRIMEIRA FASE
    # ==============================================

    def _desenhar_sapos_floresta(self, tela):

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for mundo_x, mundo_y, fase in self.sapos_floresta:

            x = int(
                mundo_x - self.camera.x * 0.83
            )

            salto = abs(
                math.sin(tempo * 1.5 + fase)
            ) * 5

            y = int(
                mundo_y - self.camera.y * 0.20 - salto
            )

            if x < -45 or x > config.LARGURA + 45:
                continue

            vermelho = (145, 43, 49, 230)
            sombra = (68, 25, 36, 245)

            pygame.draw.ellipse(
                camada,
                sombra,
                (x - 17, y + 6, 17, 10)
            )

            pygame.draw.ellipse(
                camada,
                sombra,
                (x + 2, y + 6, 17, 10)
            )

            pygame.draw.ellipse(
                camada,
                vermelho,
                (x - 17, y - 5, 34, 20)
            )

            pygame.draw.ellipse(
                camada,
                vermelho,
                (x - 11, y - 14, 23, 17)
            )

            pygame.draw.circle(
                camada,
                (155, 48, 51, 255),
                (x - 7, y - 13),
                5
            )

            pygame.draw.circle(
                camada,
                (155, 48, 51, 255),
                (x + 8, y - 13),
                5
            )

            pygame.draw.circle(
                camada,
                (255, 157, 95, 255),
                (x - 7, y - 13),
                2
            )

            pygame.draw.circle(
                camada,
                (255, 157, 95, 255),
                (x + 8, y - 13),
                2
            )

            pygame.draw.ellipse(
                camada,
                (20, 31, 24, 140),
                (x - 16, y + 14, 32, 5)
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # FANTASMAS CINZENTOS DA SEGUNDA FASE
    # ==============================================

    def _desenhar_fantasmas_floresta(self, tela):

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for mundo_x, mundo_y, fase, velocidade, tamanho in self.fantasmas_floresta:

            x = int(
                mundo_x - self.camera.x * 0.88
                + math.sin(tempo * 0.45 + fase) * 10
            )

            y = int(
                mundo_y - self.camera.y * 0.25
                + math.sin(tempo * velocidade + fase) * 14
            )

            if x < -40 or x > config.LARGURA + 40:
                continue

            pulsacao = (
                math.sin(tempo * 2 + fase) + 1
            ) / 2

            alpha = int(90 + pulsacao * 65)

            pygame.draw.circle(
                camada,
                (159, 191, 194, 24),
                (x, y),
                tamanho + 11
            )

            pygame.draw.circle(
                camada,
                (166, 184, 190, alpha),
                (x, y - tamanho // 2),
                tamanho // 2
            )

            pygame.draw.ellipse(
                camada,
                (152, 174, 183, alpha),
                (
                    x - tamanho // 2,
                    y - tamanho // 2,
                    tamanho,
                    tamanho
                )
            )

            pygame.draw.polygon(
                camada,
                (137, 164, 175, alpha),
                [
                    (x - tamanho // 2, y),
                    (x - tamanho // 3, y + tamanho),
                    (x, y + tamanho // 2),
                    (x + tamanho // 3, y + tamanho),
                    (x + tamanho // 2, y)
                ]
            )

            pygame.draw.circle(
                camada,
                (36, 58, 75, 190),
                (x - 3, y - tamanho // 3),
                1
            )

            pygame.draw.circle(
                camada,
                (36, 58, 75, 190),
                (x + 3, y - tamanho // 3),
                1
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # CAVEIRAS
    # ==============================================

    def _desenhar_caveira(
        self,
        tela,
        x,
        y,
        escala=1.0,
        cor=(181, 190, 157),
        brilho=True
    ):

        largura = max(1, int(24 * escala))
        altura = max(1, int(21 * escala))

        if brilho:

            pygame.draw.circle(
                tela,
                (85, 191, 71, 55),
                (x, y - int(4 * escala)),
                int(21 * escala)
            )

        pygame.draw.ellipse(
            tela,
            cor,
            (
                x - largura // 2,
                y - altura,
                largura,
                altura
            )
        )

        pygame.draw.rect(
            tela,
            cor,
            (
                x - int(7 * escala),
                y - int(4 * escala),
                int(14 * escala),
                int(7 * escala)
            ),
            border_radius=max(1, int(2 * escala))
        )

        pygame.draw.circle(
            tela,
            (24, 38, 27),
            (x - int(5 * escala), y - int(5 * escala)),
            max(1, int(3 * escala))
        )

        pygame.draw.circle(
            tela,
            (24, 38, 27),
            (x + int(5 * escala), y - int(5 * escala)),
            max(1, int(3 * escala))
        )

        if brilho:

            pygame.draw.circle(
                tela,
                (125, 212, 78),
                (x - int(5 * escala), y - int(5 * escala)),
                max(1, int(1.5 * escala))
            )

            pygame.draw.circle(
                tela,
                (125, 212, 78),
                (x + int(5 * escala), y - int(5 * escala)),
                max(1, int(1.5 * escala))
            )

        for i in range(3):

            dx = x - int(4 * escala) + int(i * 4 * escala)

            pygame.draw.line(
                tela,
                (51, 61, 43),
                (dx, y),
                (dx, y + int(3 * escala)),
                1
            )

    # ==============================================
    # DECORAÇÃO DA FLORESTA NO PRIMEIRO PLANO
    # ==============================================

    def _desenhar_decoracoes_floresta(self, tela):

        tempo = pygame.time.get_ticks() / 1000

        for mundo_x, mundo_y, tipo, escala in self.decoracoes_floresta:

            x = int(mundo_x - self.camera.x)
            y = int(mundo_y - self.camera.y)

            if x < -70 or x > config.LARGURA + 70:
                continue

            if tipo == "raiz":

                pygame.draw.lines(
                    tela,
                    (43, 68, 39),
                    False,
                    [
                        (x - 25, y),
                        (x - 9, y - int(12 * escala)),
                        (x + 4, y - int(7 * escala)),
                        (x + 25, y - int(21 * escala))
                    ],
                    max(2, int(5 * escala))
                )

                pygame.draw.lines(
                    tela,
                    (74, 101, 54),
                    False,
                    [
                        (x - 7, y),
                        (x + 1, y - int(9 * escala)),
                        (x + 15, y - int(12 * escala))
                    ],
                    2
                )

            elif tipo == "cogumelo":

                pulso = (
                    math.sin(tempo * 2.5 + mundo_x) + 1
                ) / 2

                brilho = pygame.Surface(
                    (60, 55),
                    pygame.SRCALPHA
                )

                pygame.draw.circle(
                    brilho,
                    (111, 210, 75, int(25 + pulso * 20)),
                    (30, 28),
                    23
                )

                tela.blit(
                    brilho,
                    (x - 30, y - 43)
                )

                pygame.draw.rect(
                    tela,
                    (180, 185, 141),
                    (
                        x - int(3 * escala),
                        y - int(20 * escala),
                        int(7 * escala),
                        int(20 * escala)
                    )
                )

                pygame.draw.ellipse(
                    tela,
                    (98, 159, 57),
                    (
                        x - int(14 * escala),
                        y - int(25 * escala),
                        int(28 * escala),
                        int(14 * escala)
                    )
                )

                pygame.draw.circle(
                    tela,
                    (192, 234, 113),
                    (x, y - int(19 * escala)),
                    max(1, int(3 * escala))
                )

            elif tipo == "pedra":

                pygame.draw.ellipse(
                    tela,
                    (46, 65, 48),
                    (
                        x - int(15 * escala),
                        y - int(11 * escala),
                        int(30 * escala),
                        int(13 * escala)
                    )
                )

                pygame.draw.ellipse(
                    tela,
                    (95, 121, 82),
                    (
                        x - int(7 * escala),
                        y - int(10 * escala),
                        int(12 * escala),
                        int(4 * escala)
                    )
                )

            elif tipo == "caveira":

                self._desenhar_caveira(
                    tela,
                    x,
                    y,
                    escala * 0.8,
                    (185, 188, 150),
                    brilho=True
                )

            elif tipo == "flor":

                balanco = math.sin(tempo * 2 + mundo_x) * 2

                pygame.draw.line(
                    tela,
                    (63, 106, 50),
                    (x, y),
                    (int(x + balanco), y - int(18 * escala)),
                    2
                )

                pygame.draw.circle(
                    tela,
                    (135, 190, 77),
                    (int(x + balanco), y - int(19 * escala)),
                    max(2, int(4 * escala))
                )

                pygame.draw.circle(
                    tela,
                    (213, 221, 118),
                    (int(x + balanco), y - int(19 * escala)),
                    max(1, int(2 * escala))
                )

    # ==============================================
    # ESPOROS E PARTÍCULAS VERDES
    # ==============================================

    def _desenhar_esporos_verdes(self, tela):

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for mundo_x, mundo_y, fase, velocidade, tamanho in self.esporos_verdes:

            x = int(
                mundo_x - self.camera.x * 0.76
            )

            y = int(
                mundo_y - self.camera.y * 0.28
                + math.sin(tempo * velocidade + fase) * 13
            )

            x += int(
                math.sin(tempo * 0.5 + fase) * 5
            )

            if x < -10 or x > config.LARGURA + 10:
                continue

            pulsacao = (
                math.sin(tempo * 3 + fase) + 1
            ) / 2

            alpha = int(85 + pulsacao * 105)

            pygame.draw.circle(
                camada,
                (111, 211, 82, 30),
                (x, y),
                tamanho + 6
            )

            pygame.draw.circle(
                camada,
                (151, 219, 97, alpha),
                (x, y),
                tamanho
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # PREPARAÇÃO DA FASE 4 — CASTELO DO DRAGÃO
    # ==============================================

    def _preparar_cenario_fase4(self):

        gerador = random.Random(707)

        for _ in range(9):

            self.nevoas_fase4.append((
                gerador.randint(0, config.LARGURA),
                gerador.randint(280, 510),
                gerador.uniform(0.5, 1.5),
                gerador.randint(90, 180),
                gerador.randint(25, 50)
            ))

        for _ in range(45):

            self.brasas_fase4.append((
                gerador.uniform(0, self.largura),
                gerador.uniform(180, 540),
                gerador.uniform(0, math.pi * 2),
                gerador.uniform(0.5, 1.8),
                gerador.randint(2, 4)
            ))

        for _ in range(24):

            self.esporos_fase4.append((
                gerador.uniform(0, self.largura),
                gerador.uniform(130, 500),
                gerador.uniform(0, math.pi * 2),
                gerador.uniform(0.5, 1.4),
                gerador.randint(1, 3)
            ))

    # ==============================================
    # NÉVOA DA FASE 4
    # ==============================================

    def _desenhar_nevoa_fase4(self, tela):

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for mundo_x, mundo_y, velocidade, largura, altura in self.nevoas_fase4:

            x = int(
                mundo_x
                - self.camera.x * 0.25
                + math.sin(tempo * velocidade) * 25
            )

            y = int(
                mundo_y
                - self.camera.y * 0.15
                + math.sin(tempo * 0.5 + mundo_x) * 9
            )

            x %= config.LARGURA + largura
            x -= largura // 2

            pygame.draw.ellipse(
                camada,
                (112, 48, 47, 25),
                (x, y, largura, altura)
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # BRASAS DA FASE 4
    # ==============================================

    def _desenhar_brasas_fase4(self, tela):

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for mundo_x, mundo_y, fase, velocidade, tamanho in self.brasas_fase4:

            x = int(
                mundo_x - self.camera.x * 0.85
                + math.sin(tempo * velocidade + fase) * 8
            )

            y = int(
                mundo_y - self.camera.y * 0.25
                - (tempo * (12 + velocidade * 8)) % 550
            )

            if x < -10 or x > config.LARGURA + 10:
                continue

            pulsacao = (
                math.sin(tempo * 4 + fase) + 1
            ) / 2

            alpha = int(100 + pulsacao * 130)

            pygame.draw.circle(
                camada,
                (191, 47, 32, 35),
                (x, y),
                tamanho + 6
            )

            pygame.draw.circle(
                camada,
                (239, 75, 39, alpha),
                (x, y),
                tamanho
            )

            pygame.draw.circle(
                camada,
                (255, 174, 82, alpha),
                (x, y),
                max(1, tamanho // 2)
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # PARTÍCULAS DE ENERGIA DA FASE 4
    # ==============================================

    def _desenhar_esporos_fase4(self, tela):

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for mundo_x, mundo_y, fase, velocidade, tamanho in self.esporos_fase4:

            x = int(
                mundo_x - self.camera.x * 0.65
                + math.sin(tempo * velocidade + fase) * 9
            )

            y = int(
                mundo_y - self.camera.y * 0.20
                + math.sin(tempo * 1.2 + fase) * 12
            )

            if x < -10 or x > config.LARGURA + 10:
                continue

            pygame.draw.circle(
                camada,
                (220, 100, 65, 30),
                (x, y),
                tamanho + 5
            )

            pygame.draw.circle(
                camada,
                (255, 180, 111, 145),
                (x, y),
                tamanho
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # NÉVOA DA FASE 1
    # ==============================================

    def _desenhar_nevoa(self, tela):

        if self.numero != 1:
            return

        tempo = pygame.time.get_ticks() / 1000

        nevoa = pygame.Surface(
            (config.LARGURA, 175),
            pygame.SRCALPHA
        )

        deslocamento = int(
            tempo * 12 + self.camera.x * 0.16
        ) % (config.LARGURA + 250)

        for i in range(6):

            x = (
                i * 210 - deslocamento
            ) % (config.LARGURA + 300) - 150

            y = int(
                35 + math.sin(tempo * 0.5 + i) * 18
            )

            largura = 180 + (i % 3) * 45
            altura = 38 + (i % 2) * 14

            pygame.draw.ellipse(
                nevoa,
                (153, 126, 190, 17),
                (x, y, largura, altura)
            )

        tela.blit(nevoa, (0, 300))

    # ==============================================
    # ÁGUA DA FASE 1
    # ==============================================

    def _desenhar_agua(self, tela):

        if self.numero != 1:
            return

        tempo = pygame.time.get_ticks() / 1000

        altura_agua = 100

        agua = pygame.Surface(
            (config.LARGURA, altura_agua),
            pygame.SRCALPHA
        )

        agua.fill((18, 25, 63, 22))

        ondas = [
            ((165, 143, 220, 115), 22, 3, 1.4),
            ((111, 139, 206, 100), 45, 4, 1.8),
            ((196, 174, 231, 95), 67, 3, 1.2),
            ((111, 166, 190, 85), 86, 2, 2.0)
        ]

        for indice, (cor, base_y, amplitude, velocidade) in enumerate(ondas):

            pontos = []

            for x in range(-8, config.LARGURA + 16, 8):

                fase = (
                    x * 0.025
                    + tempo * velocidade
                    + indice
                    - self.camera.x * 0.003
                )

                y = int(
                    base_y
                    + math.sin(fase) * amplitude
                    + math.sin(fase * 0.55) * 1.5
                )

                pontos.append((x, y))

            pygame.draw.lines(
                agua,
                cor,
                False,
                pontos,
                2
            )

        for i in range(8):

            x = int(
                (i * 137 + tempo * (18 + i * 1.5))
                % (config.LARGURA + 40)
            ) - 20

            y = int(
                20 + (i * 17 % 65)
                + math.sin(tempo * 2 + i) * 3
            )

            pygame.draw.line(
                agua,
                (238, 213, 169, 125),
                (x, y),
                (x + 8 + (i % 3) * 6, y),
                2
            )

        tela.blit(
            agua,
            (0, config.ALTURA - altura_agua)
        )

    # ==============================================
    # VEGETAÇÃO DA FASE 1
    # ==============================================

    def _desenhar_vegetacao(self, tela):

        if self.numero != 1:
            return

        tempo = pygame.time.get_ticks() / 1000

        for x_mundo, y_mundo, tipo, escala in self.vegetacao:

            x = int(x_mundo - self.camera.x)
            y = int(y_mundo - self.camera.y)

            if x < -65 or x > config.LARGURA + 65:
                continue

            if tipo == "arbusto":

                pygame.draw.ellipse(
                    tela,
                    (37, 65, 47),
                    (x - 17 * escala, y - 16 * escala,
                     36 * escala, 18 * escala)
                )

                pygame.draw.ellipse(
                    tela,
                    (52, 88, 57),
                    (x - 10 * escala, y - 24 * escala,
                     26 * escala, 18 * escala)
                )

            elif tipo == "flor":

                balanco = math.sin(tempo * 2 + x_mundo) * 2

                pygame.draw.line(
                    tela,
                    (74, 112, 69),
                    (x, y),
                    (int(x + balanco), y - 22 * escala),
                    2
                )

                pygame.draw.circle(
                    tela,
                    (184, 143, 202),
                    (int(x + balanco), int(y - 23 * escala)),
                    max(2, int(4 * escala))
                )

            elif tipo == "cogumelo":

                pygame.draw.rect(
                    tela,
                    (203, 190, 164),
                    (x - 3 * escala, y - 13 * escala,
                     7 * escala, 13 * escala)
                )

                pygame.draw.ellipse(
                    tela,
                    (116, 62, 119),
                    (x - 12 * escala, y - 18 * escala,
                     24 * escala, 11 * escala)
                )

            elif tipo == "pedra":

                pygame.draw.ellipse(
                    tela,
                    (57, 54, 72),
                    (x - 14 * escala, y - 10 * escala,
                     27 * escala, 12 * escala)
                )

    # ==============================================
    # LANTERNAS DA FASE 1
    # ==============================================

    def _desenhar_lanternas(self, tela):

        if self.numero != 1:
            return

        tempo = pygame.time.get_ticks() / 1000

        for x_mundo, y_mundo in self.lanternas:

            x = int(x_mundo - self.camera.x)
            y = int(y_mundo - self.camera.y)

            if x < -70 or x > config.LARGURA + 70:
                continue

            pulsacao = (
                math.sin(tempo * 3 + x_mundo) + 1
            ) / 2

            brilho = pygame.Surface(
                (90, 90),
                pygame.SRCALPHA
            )

            alpha = int(22 + pulsacao * 20)

            pygame.draw.circle(
                brilho,
                (255, 176, 83, alpha),
                (45, 45),
                38
            )

            tela.blit(
                brilho,
                (x - 45, y - 38)
            )

            pygame.draw.rect(
                tela,
                (72, 48, 48),
                (x - 8, y - 9, 16, 22),
                border_radius=3
            )

            pygame.draw.rect(
                tela,
                (196, 145, 79),
                (x - 6, y - 7, 12, 17),
                2,
                border_radius=2
            )

            pygame.draw.circle(
                tela,
                (255, 210, 117),
                (x, y + 1),
                4
            )

    # ==============================================
    # VAGALUMES DA FASE 1
    # ==============================================

    def _desenhar_particulas(self, tela):

        if self.numero != 1:
            return

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for mundo_x, mundo_y, fase, velocidade in self.particulas:

            x = int(mundo_x - self.camera.x * 0.80)

            y = int(
                mundo_y - self.camera.y * 0.35
                + math.sin(tempo * velocidade + fase) * 9
            )

            if x < -15 or x > config.LARGURA + 15:
                continue

            pygame.draw.circle(
                camada,
                (177, 137, 226, 35),
                (x, y),
                8
            )

            pygame.draw.circle(
                camada,
                (218, 197, 250, 130),
                (x, y),
                2
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # NÉVOA DA FASE 2
    # ==============================================

    def _desenhar_nevoa_cemiterio(self, tela):

        if self.numero != 2:
            return

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        deslocamento = int(
            tempo * 13 + self.camera.x * 0.19
        ) % (config.LARGURA + 300)

        for i in range(7):

            x = (
                i * 185 - deslocamento
            ) % (config.LARGURA + 360) - 180

            y = int(
                345 + math.sin(tempo * 0.45 + i) * 20
            )

            pygame.draw.ellipse(
                camada,
                (143, 169, 197, 29),
                (x, y, 230, 55)
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # ALMAS DA FASE 2
    # ==============================================

    def _desenhar_almas(self, tela):

        if self.numero != 2:
            return

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for mundo_x, mundo_y, fase, velocidade, tamanho in self.almas:

            x = int(mundo_x - self.camera.x * 0.88)

            y = int(
                mundo_y - self.camera.y * 0.30
                + math.sin(tempo * velocidade + fase) * 13
            )

            if x < -35 or x > config.LARGURA + 35:
                continue

            alpha = 120

            pygame.draw.circle(
                camada,
                (183, 211, 228, alpha),
                (x, y - tamanho // 2),
                tamanho // 2
            )

            pygame.draw.ellipse(
                camada,
                (155, 190, 210, alpha),
                (x - tamanho // 2, y - tamanho // 2,
                 tamanho, tamanho)
            )

            pygame.draw.polygon(
                camada,
                (145, 183, 207, alpha),
                [
                    (x - tamanho // 2, y),
                    (x - tamanho // 3, y + tamanho),
                    (x, y + tamanho // 2),
                    (x + tamanho // 3, y + tamanho),
                    (x + tamanho // 2, y)
                ]
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # LUZES DA FASE 2
    # ==============================================

    def _desenhar_luzes_cemiterio(self, tela):

        if self.numero != 2:
            return

        tempo = pygame.time.get_ticks() / 1000

        camada = pygame.Surface(
            (config.LARGURA, config.ALTURA),
            pygame.SRCALPHA
        )

        for i, (mundo_x, mundo_y) in enumerate(self.luzes_cemiterio):

            x = int(mundo_x - self.camera.x)

            y = int(
                mundo_y - self.camera.y
                + math.sin(tempo * 1.7 + i) * 5
            )

            if x < -40 or x > config.LARGURA + 40:
                continue

            pygame.draw.circle(
                camada,
                (98, 177, 226, 45),
                (x, y),
                27
            )

            pygame.draw.circle(
                camada,
                (220, 238, 247, 215),
                (x, y),
                3
            )

        tela.blit(camada, (0, 0))

    # ==============================================
    # LÁPIDES DA FASE 2
    # ==============================================

    def _desenhar_decoracoes_cemiterio(self, tela):

        if self.numero != 2:
            return

        for mundo_x, mundo_y, tipo, escala in self.decoracoes_cemiterio:

            x = int(mundo_x - self.camera.x)
            y = int(mundo_y - self.camera.y)

            if x < -60 or x > config.LARGURA + 60:
                continue

            if tipo == "lapide":

                largura = max(12, int(22 * escala))
                altura = max(24, int(38 * escala))

                pontos = [
                    (x - largura // 2, y),
                    (x - largura // 2, y - altura + 9),
                    (x - largura // 3, y - altura),
                    (x + largura // 3, y - altura),
                    (x + largura // 2, y - altura + 9),
                    (x + largura // 2, y)
                ]

                pygame.draw.polygon(
                    tela,
                    (66, 79, 100),
                    pontos
                )

                pygame.draw.lines(
                    tela,
                    (111, 132, 153),
                    True,
                    pontos,
                    2
                )

                pygame.draw.line(
                    tela,
                    (130, 146, 163),
                    (x, y - altura + 10),
                    (x, y - altura + 24),
                    2
                )

                pygame.draw.line(
                    tela,
                    (130, 146, 163),
                    (x - 5, y - altura + 15),
                    (x + 5, y - altura + 15),
                    2
                )

            elif tipo == "galho":

                pygame.draw.lines(
                    tela,
                    (40, 49, 61),
                    False,
                    [
                        (x, y),
                        (x - 4, y - 18),
                        (x - 14, y - 29)
                    ],
                    3
                )

                pygame.draw.lines(
                    tela,
                    (40, 49, 61),
                    False,
                    [
                        (x - 5, y - 19),
                        (x + 7, y - 30),
                        (x + 12, y - 38)
                    ],
                    3
                )

    # ==============================================
    # EVENTOS
    # ==============================================

    def eventos(self, eventos):

        for e in eventos:

            if e.type == pygame.KEYDOWN:

                if e.key == pygame.K_ESCAPE:

                    from cenas.menu import Menu

                    self.jogo.trocar_cena(
                        Menu(self.jogo)
                    )

                elif e.key in (
                    pygame.K_SPACE,
                    pygame.K_w,
                    pygame.K_UP
                ):

                    self.jogador.pular()

                elif e.key in (pygame.K_j, pygame.K_x):

                    self.jogador.atacar()

                elif e.key in (
                    pygame.K_k,
                    pygame.K_LSHIFT,
                    pygame.K_RSHIFT
                ):

                    self.jogador.avancar()

    # ==============================================
    # ATUALIZAÇÃO
    # ==============================================

    def atualizar(self, dt):

        self.jogador.atualizar(
            dt,
            self.solidos,
            self.largura
        )

        for inimigo in self.inimigos:

            inimigo.atualizar(
                dt,
                self.solidos
            )

        for reliquia in self.reliquias:
            reliquia.atualizar(dt)

        self.tempo_mensagem = max(
            0.0,
            self.tempo_mensagem - dt
        )

        self._combate()
        self._interacoes()

        self.inimigos = [
            i for i in self.inimigos if i.vivo
        ]

        self.camera.seguir(
            self.jogador.rect,
            dt
        )

        if self.jogador.rect.top > self.altura + 200:

            self.jogador.vida -= 1

            if self.jogador.vida > 0:

                self.jogador.reiniciar()

                self.camera.centralizar(
                    self.jogador.rect
                )

        if self.jogador.vida <= 0:

            from cenas.game_over import GameOver

            self.jogo.trocar_cena(
                GameOver(self.jogo, self.numero)
            )

    # ==============================================
    # COMBATE
    # ==============================================

    def _combate(self):

        area = self.jogador.hitbox_ataque

        if area:

            for inimigo in self.inimigos:

                if (
                    id(inimigo) not in self.jogador.alvos_acertados
                    and area.colliderect(inimigo.rect)
                ):

                    inimigo.receber_dano(
                        config.DANO_ATAQUE,
                        self.jogador.rect.centerx
                    )

                    self.jogador.alvos_acertados.add(id(inimigo))

        for inimigo in self.inimigos:

            if (
                inimigo.vivo
                and self.jogador.rect.colliderect(inimigo.rect)
            ):

                self.jogador.receber_dano(
                    inimigo.dano,
                    inimigo.rect.centerx
                )

    # ==============================================
    # INTERAÇÕES
    # ==============================================

    def _interacoes(self):

        for reliquia in self.reliquias:

            if self.jogador.rect.colliderect(reliquia.rect):

                reliquia.coletada = True

                self.jogador.desbloquear(reliquia.tipo)

                self.jogo.habilidades.add(reliquia.tipo)

                self.mensagem = reliquia.textos
                self.tempo_mensagem = 5.0

        self.reliquias = [
            r for r in self.reliquias if not r.coletada
        ]

        if self.jogador.avancando:

            zona = self.jogador.rect.inflate(72, 0)

            for barreira in list(self.barreiras):

                if zona.colliderect(barreira.rect):

                    self.barreiras.remove(barreira)
                    self.solidos.remove(barreira)

        if self.barreiras and self.tempo_mensagem <= 0:

            perto = self.jogador.rect.inflate(300, 0)

            if any(
                perto.colliderect(b.rect)
                for b in self.barreiras
            ):

                chave = (
                    "barreira",
                    self.jogador.tem_avanco
                )

                if chave not in self.dicas:

                    self.dicas.add(chave)

                    if self.jogador.tem_avanco:

                        self.mensagem = (
                            "Parede rachada!",
                            "Chegue perto e avance contra ela (K ou SHIFT)"
                        )

                    else:

                        self.mensagem = (
                            "Parede rachada...",
                            "Falta uma relíquia para quebrá-la"
                        )

                    self.tempo_mensagem = 4.0

        if (
            self.saida
            and self.jogador.rect.colliderect(self.saida.rect)
        ):

            self._proxima_fase()

    def _proxima_fase(self):

        if existe_fase(self.numero + 1):

            self.jogo.trocar_cena(
                Fase(self.jogo, self.numero + 1)
            )

        else:

            from cenas.final import Final

            self.jogo.trocar_cena(
                Final(self.jogo)
            )

    # ==============================================
    # FUNDO PANORÂMICO
    # ==============================================

    def _desenhar_fundo(self, tela):

        if self.numero == 4 and self.imagem_base:

            tela.blit(
                self.imagem_base,
                (0, 0)
            )

            return

        if self.fundo_panorama:

            deslocamento_x = int(
                self.camera.x * self.fator_fundo
            )

            deslocamento_y = int(
                self.camera.y * 0.15
            )

            tela.blit(
                self.fundo_panorama,
                (-deslocamento_x, -deslocamento_y)
            )

        else:

            tela.fill(
                FUNDOS.get(
                    self.numero,
                    (25, 20, 30)
                )
            )

    # ==============================================
    # DESENHO FINAL
    # ==============================================

    def desenhar(self, tela):

        # Fundo
        self._desenhar_fundo(tela)

        # Efeitos da Fase 1
        if self.numero == 1:

            self._desenhar_agua(tela)
            self._desenhar_nevoa(tela)
            self._desenhar_vegetacao(tela)
            self._desenhar_lanternas(tela)
            self._desenhar_particulas(tela)

        # Efeitos da Fase 2
        elif self.numero == 2:

            self._desenhar_nevoa_cemiterio(tela)
            self._desenhar_almas(tela)
            self._desenhar_luzes_cemiterio(tela)

        # Efeitos da Fase 3
        elif self.numero == 3:

            self._desenhar_nevoa_floresta(tela)
            self._desenhar_fantasmas_floresta(tela)
            self._desenhar_sapos_floresta(tela)
            self._desenhar_macas_envenenadas(tela)
            self._desenhar_esporos_verdes(tela)

        # Efeitos da Fase 4
        elif self.numero == 4:

            self._desenhar_nevoa_fase4(tela)
            self._desenhar_brasas_fase4(tela)
            self._desenhar_esporos_fase4(tela)

        # Plataformas
        for p in self.plataformas:

            p.desenhar(
                tela,
                self.camera,
                tema=self.numero
            )

        # Decoração próxima ao chão da Fase 2
        if self.numero == 2:
            self._desenhar_decoracoes_cemiterio(tela)

        # Decoração próxima ao chão da Fase 3
        if self.numero == 3:

            self._desenhar_decoracoes_floresta(tela)

            for x_mundo, y_mundo, escala in self.caveiras_floresta:

                x = int(x_mundo - self.camera.x * 0.92)
                y = int(y_mundo - self.camera.y * 0.55)

                if -40 < x < config.LARGURA + 40:

                    self._desenhar_caveira(
                        tela,
                        x,
                        y,
                        escala,
                        (184, 193, 153),
                        brilho=True
                    )

        # Barreiras
        for b in self.barreiras:

            b.desenhar(
                tela,
                self.camera,
                tema=self.numero
            )

        # Saída
        if self.saida:
            self.saida.desenhar(tela, self.camera)

        # Relíquias
        for r in self.reliquias:
            r.desenhar(tela, self.camera)

        # Inimigos reais
        for inimigo in self.inimigos:
            inimigo.desenhar(tela, self.camera)

        # Guerreira
        self.jogador.desenhar(tela, self.camera)

        # HUD
        self.hud.desenhar(
            tela,
            self.jogador,
            self.numero
        )

        # Mensagens de interação
        if self.mensagem and self.tempo_mensagem > 0:

            titulo, descricao = self.mensagem

            for texto, fonte, cor, y in (
                (titulo, self.fonte_msg, config.DOURADO, 130),
                (descricao, self.fonte_msg2, config.BRANCO, 168)
            ):

                sombra = fonte.render(
                    texto,
                    True,
                    (0, 0, 0)
                )

                img = fonte.render(
                    texto,
                    True,
                    cor
                )

                pos = img.get_rect(
                    center=(
                        config.LARGURA // 2,
                        y
                    )
                )

                tela.blit(
                    sombra,
                    pos.move(2, 2)
                )

                tela.blit(
                    img,
                    pos
                )