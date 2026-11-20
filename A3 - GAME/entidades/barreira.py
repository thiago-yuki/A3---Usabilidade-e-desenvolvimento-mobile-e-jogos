
import pygame
import config


class Barreira:
    """Parede rachada que bloqueia o caminho."""

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
                (72, 65, 88),
                (83, 74, 99),
                (65, 61, 80),
                (91, 79, 103)
            ]

            contorno = (31, 27, 43)
            luz = (132, 116, 143)
            sombra = (39, 34, 52)
            rachadura = (35, 29, 44)
            brilho = (104, 88, 112)

        # =====================================
        # FASE 2: PEDRAS AZUL-ACINZENTADAS
        # =====================================

        elif tema == 2:

            pedras = [
                (57, 71, 88),
                (69, 82, 99),
                (48, 63, 80),
                (78, 90, 108)
            ]

            contorno = (25, 35, 49)
            luz = (125, 148, 169)
            sombra = (30, 42, 58)
            rachadura = (27, 42, 59)
            brilho = (101, 174, 207)

        # =====================================
        # FASE 3: FLORESTA AMALDIÇOADA
        # =====================================

        elif tema == 3:

            pedras = [
                (43, 64, 42),
                (53, 76, 48),
                (34, 54, 37),
                (64, 83, 50)
            ]

            contorno = (19, 34, 22)
            luz = (105, 145, 78)
            sombra = (24, 40, 25)
            rachadura = (22, 39, 24)
            brilho = (130, 213, 78)

        # =====================================
        # FASE 4: CASTELO DAS TRÊS MALDIÇÕES
        # =====================================

        else:

            pedras = [
                (37, 32, 38),
                (48, 37, 40),
                (30, 29, 36),
                (55, 40, 42),
                (42, 36, 43)
            ]

            contorno = (15, 14, 20)
            luz = (113, 69, 65)
            sombra = (19, 16, 22)
            rachadura = (65, 28, 30)
            brilho = (190, 65, 43)

        # =====================================
        # FUNDO DA PAREDE
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

                bloco = pygame.Rect(
                    x + 2,
                    y + 2,
                    max(1, largura - 4),
                    max(1, altura - 4)
                )

                indice = (
                    linha * 3
                    + coluna * 5
                    + self.rect.x // tamanho
                ) % len(pedras)

                pygame.draw.rect(
                    tela,
                    pedras[indice],
                    bloco
                )

                # =====================================
                # LUZ NA BORDA SUPERIOR
                # =====================================

                if bloco.width > 5:

                    pygame.draw.line(
                        tela,
                        luz,
                        (bloco.left + 2, bloco.top + 2),
                        (bloco.right - 3, bloco.top + 2),
                        2
                    )

                # =====================================
                # SOMBRA INFERIOR
                # =====================================

                if bloco.height > 5:

                    pygame.draw.line(
                        tela,
                        sombra,
                        (bloco.left + 2, bloco.bottom - 2),
                        (bloco.right - 2, bloco.bottom - 2),
                        2
                    )

                # =====================================
                # RACHADURAS
                # =====================================

                if largura >= 24 and altura >= 24:

                    detalhe = (
                        linha + coluna * 2
                    ) % 3

                    if detalhe == 0:

                        pontos = [
                            (x + largura // 3, y + altura // 5),
                            (x + largura // 2, y + altura // 2),
                            (x + largura // 3, y + altura * 3 // 4)
                        ]

                        pygame.draw.lines(
                            tela,
                            rachadura,
                            False,
                            pontos,
                            2
                        )

                        # Brilho da corrupção na Fase 3
                        if tema == 3:

                            pygame.draw.lines(
                                tela,
                                brilho,
                                False,
                                [
                                    (px + 2, py)
                                    for px, py in pontos
                                ],
                                2
                            )

                        # Brilho azul da Fase 2
                        elif tema == 2:

                            pygame.draw.lines(
                                tela,
                                brilho,
                                False,
                                [
                                    (px + 2, py)
                                    for px, py in pontos
                                ],
                                1
                            )

                        # Rachaduras incandescentes da Fase 4
                        elif tema == 4:

                            pygame.draw.lines(
                                tela,
                                (105, 34, 31),
                                False,
                                pontos,
                                4
                            )

                            pygame.draw.lines(
                                tela,
                                (210, 76, 43),
                                False,
                                [
                                    (px + 1, py)
                                    for px, py in pontos
                                ],
                                2
                            )

                # =====================================
                # MUSGO ROXO - FASE 1
                # =====================================

                if (
                    tema == 1
                    and (linha + coluna) % 2 == 0
                    and largura >= 20
                ):

                    pygame.draw.ellipse(
                        tela,
                        (66, 86, 60),
                        (x + 5, y + 5, 12, 5)
                    )

                # =====================================
                # LÍQUEN AZUL - FASE 2
                # =====================================

                elif (
                    tema == 2
                    and linha == 0
                    and coluna % 2 == 0
                    and largura >= 20
                ):

                    pygame.draw.ellipse(
                        tela,
                        (66, 102, 119),
                        (x + 5, y + 5, 13, 5)
                    )

                # =====================================
                # MUSGO VENENOSO - FASE 3
                # =====================================

                elif (
                    tema == 3
                    and linha == 0
                    and coluna % 2 == 0
                    and largura >= 20
                ):

                    pygame.draw.ellipse(
                        tela,
                        (73, 119, 48),
                        (x + 5, y + 5, 14, 5)
                    )

                # =====================================
                # VEIOS VERDES - FASE 4
                # =====================================

                elif (
                    tema == 4
                    and largura >= 24
                    and altura >= 20
                    and (linha + coluna) % 3 == 0
                ):

                    pygame.draw.lines(
                        tela,
                        (57, 94, 47),
                        False,
                        [
                            (x + 5, y + altura - 5),
                            (x + 11, y + altura // 2),
                            (x + 19, y + altura // 2 - 4)
                        ],
                        2
                    )

                coluna += 1

            linha += 1

        # =====================================
        # CONTORNO EXTERNO
        # =====================================

        pygame.draw.rect(
            tela,
            contorno,
            r,
            2
        )

        # Acabamento avermelhado da Fase 4
        if tema == 4:

            pygame.draw.line(
                tela,
                (105, 47, 42),
                (r.left + 2, r.top + 2),
                (r.right - 2, r.top + 2),
                2
            )
