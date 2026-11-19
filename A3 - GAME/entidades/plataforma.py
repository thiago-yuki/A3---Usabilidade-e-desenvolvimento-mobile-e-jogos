
import pygame
import config


class Plataforma:
    def __init__(self, x, y, largura, altura):
        self.rect = pygame.Rect(x, y, largura, altura)

    def desenhar(self, tela, camera, tema=1):

        r = camera.aplicar(self.rect)

        if (
            r.right < 0
            or r.left > config.LARGURA
            or r.bottom < 0
            or r.top > config.ALTURA
        ):
            return

        tamanho = config.TAMANHO_TILE

        # =====================================
        # FASE 1: PEDRAS ARROXEADAS
        # =====================================

        if tema == 1:

            pedras = [
                (78, 70, 94),
                (87, 78, 103),
                (68, 66, 86),
                (94, 82, 105)
            ]

            contorno = (35, 30, 45)
            luz = (128, 111, 139)
            sombra = (43, 37, 54)
            musgo = (65, 91, 63)
            detalhe = (91, 108, 68)

        # =====================================
        # FASE 2: PEDRAS AZUL-ACINZENTADAS
        # =====================================

        elif tema == 2:

            pedras = [
                (59, 74, 91),
                (69, 84, 102),
                (52, 66, 83),
                (80, 91, 108)
            ]

            contorno = (27, 38, 53)
            luz = (128, 148, 169)
            sombra = (32, 45, 61)
            musgo = (65, 91, 111)
            detalhe = (106, 143, 163)

        # =====================================
        # FASE 3: FLORESTA AMALDIÇOADA
        # =====================================

        elif tema == 3:

            pedras = [
                (42, 65, 43),
                (53, 77, 48),
                (35, 56, 40),
                (65, 84, 52)
            ]

            contorno = (18, 35, 23)
            luz = (105, 139, 79)
            sombra = (22, 40, 26)
            musgo = (74, 123, 54)
            detalhe = (121, 160, 72)

        # =====================================
        # FASE 4: PEDRAS DE OBSIDIANA
        # CASTELO DAS TRÊS MALDIÇÕES
        # =====================================

        else:

            pedras = [
                (39, 34, 39),
                (49, 38, 41),
                (32, 31, 38),
                (57, 42, 43),
                (43, 39, 46)
            ]

            contorno = (17, 16, 23)
            luz = (112, 70, 68)
            sombra = (19, 17, 23)
            musgo = (55, 91, 49)
            detalhe = (102, 139, 68)

        # =====================================
        # BASE DA PLATAFORMA
        # =====================================

        pygame.draw.rect(
            tela,
            contorno,
            r
        )

        linha = 0

        for y in range(r.top, r.bottom, tamanho):

            coluna = 0

            for x in range(r.left, r.right, tamanho):

                largura = min(tamanho, r.right - x)
                altura = min(tamanho, r.bottom - y)

                pedra = pygame.Rect(
                    x + 1,
                    y + 1,
                    max(1, largura - 2),
                    max(1, altura - 2)
                )

                indice = (
                    self.rect.x // tamanho
                    + coluna * 3
                    + linha * 5
                    + self.rect.y // tamanho
                ) % len(pedras)

                pygame.draw.rect(
                    tela,
                    pedras[indice],
                    pedra
                )

                # =====================================
                # RELEVO SUPERIOR
                # =====================================

                if pedra.width > 5:

                    pygame.draw.line(
                        tela,
                        luz,
                        (pedra.left + 2, pedra.top + 2),
                        (pedra.right - 3, pedra.top + 2),
                        2
                    )

                # =====================================
                # SOMBRA INFERIOR
                # =====================================

                if pedra.height > 5:

                    pygame.draw.line(
                        tela,
                        sombra,
                        (pedra.left + 2, pedra.bottom - 2),
                        (pedra.right - 2, pedra.bottom - 2),
                        2
                    )

                # =====================================
                # DIVISÕES ENTRE PEDRAS
                # =====================================

                pygame.draw.rect(
                    tela,
                    contorno,
                    pedra,
                    1
                )

                # =====================================
                # RACHADURAS
                # =====================================

                detalhe_rachadura = (
                    self.rect.x // tamanho
                    + coluna * 7
                    + linha * 11
                ) % 4

                if (
                    detalhe_rachadura == 0
                    and largura >= 24
                    and altura >= 24
                ):

                    pontos = [
                        (x + largura // 3, y + altura // 4),
                        (x + largura // 2, y + altura // 2),
                        (x + largura // 3, y + altura * 3 // 4)
                    ]

                    pygame.draw.lines(
                        tela,
                        sombra,
                        False,
                        pontos,
                        2
                    )

                    # Rachaduras verdes da Fase 3
                    if tema == 3:

                        pygame.draw.lines(
                            tela,
                            (93, 153, 65),
                            False,
                            [
                                (px + 2, py)
                                for px, py in pontos
                            ],
                            1
                        )

                    # Rachaduras mágicas da Fase 4
                    elif tema == 4:

                        # Núcleo vermelho incandescente
                        pygame.draw.lines(
                            tela,
                            (115, 39, 35),
                            False,
                            pontos,
                            3
                        )

                        pygame.draw.lines(
                            tela,
                            (190, 65, 43),
                            False,
                            [
                                (px - 1, py)
                                for px, py in pontos
                            ],
                            1
                        )

                # =====================================
                # MUSGO E LÍQUEN
                # =====================================

                vegetacao = (
                    self.rect.x // tamanho
                    + coluna * 5
                    + linha
                ) % 3

                if (
                    linha == 0
                    and vegetacao != 1
                    and largura >= 20
                    and tema != 4
                ):

                    pygame.draw.ellipse(
                        tela,
                        musgo,
                        (x + 5, y + 3, 15, 6)
                    )

                    pygame.draw.ellipse(
                        tela,
                        detalhe,
                        (x + 11, y + 3, 7, 4)
                    )

                # =====================================
                # RAÍZES DA FLORESTA - FASE 3
                # =====================================

                if tema == 3 and linha == 0 and coluna % 3 == 0:

                    pygame.draw.lines(
                        tela,
                        (42, 75, 39),
                        False,
                        [
                            (x + 8, y + 2),
                            (x + 12, y + 7),
                            (x + 20, y + 9)
                        ],
                        2
                    )

                # =====================================
                # VEIOS MÁGICOS - FASE 4
                # =====================================

                if (
                    tema == 4
                    and largura >= 24
                    and altura >= 20
                ):

                    veio = (
                        self.rect.x // tamanho
                        + coluna * 3
                        + linha * 7
                    ) % 5

                    if veio == 0:

                        pygame.draw.lines(
                            tela,
                            (65, 105, 52),
                            False,
                            [
                                (x + 5, y + altura - 7),
                                (x + 11, y + altura // 2),
                                (x + 19, y + altura // 2 - 5)
                            ],
                            2
                        )

                    elif veio == 2:

                        pygame.draw.line(
                            tela,
                            (112, 43, 37),
                            (x + 7, y + altura - 6),
                            (x + 15, y + altura - 11),
                            2
                        )

                coluna += 1

            linha += 1

        # =====================================
        # ACABAMENTO SUPERIOR
        # =====================================

        cores_topo = {
            1: (132, 120, 141),
            2: (142, 163, 180),
            3: (111, 151, 84),
            4: (126, 65, 55)
        }

        pygame.draw.line(
            tela,
            cores_topo.get(tema, (111, 151, 84)),
            (r.left, r.top),
            (r.right, r.top),
            2
        )

        # =====================================
        # SOMBRA INFERIOR
        # =====================================

        pygame.draw.line(
            tela,
            contorno,
            (r.left, r.bottom - 1),
            (r.right, r.bottom - 1),
            2
        )
