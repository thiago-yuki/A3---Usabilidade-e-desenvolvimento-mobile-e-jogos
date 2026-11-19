
import os
import pygame
import config


class Hud:
    def __init__(self):
        raiz_projeto = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        # Fonte medieval para o título da fase
        caminho_fonte = os.path.join(
            raiz_projeto,
            "assets",
            "fontes",
            "Cinzel-SemiBold.ttf"
        )

        try:
            self.fonte_titulo = pygame.font.Font(caminho_fonte, 23)
        except (pygame.error, OSError):
            self.fonte_titulo = pygame.font.Font(None, 30)

        self.fonte_habilidade = pygame.font.Font(None, 19)

        # Corações preparados para os estados cheio e vazio
        self.coracao_cheio = self._criar_coracao(True)
        self.coracao_vazio = self._criar_coracao(False)

    def _criar_coracao(self, ativo):
        escala = 3
        imagem = pygame.Surface(
            (36 * escala, 34 * escala),
            pygame.SRCALPHA
        )

        contorno = [
            (18, 32), (5, 21), (2, 17), (2, 11),
            (5, 6), (10, 4), (14, 5), (18, 10),
            (22, 5), (27, 4), (32, 6), (34, 11),
            (34, 17), (31, 21)
        ]

        interior = [
            (18, 28), (8, 19), (5, 16), (5, 11),
            (8, 8), (12, 7), (15, 9), (18, 13),
            (21, 9), (24, 7), (29, 8), (31, 11),
            (31, 16), (28, 19)
        ]

        contorno = [
            (x * escala, y * escala) for x, y in contorno
        ]

        interior = [
            (x * escala, y * escala) for x, y in interior
        ]

        if ativo:
            cor_borda = (220, 171, 105)
            cor_preenchimento = (185, 61, 94)
            cor_detalhe = (249, 151, 171)
        else:
            cor_borda = (104, 88, 112)
            cor_preenchimento = (65, 49, 75)
            cor_detalhe = (91, 76, 99)

        pygame.draw.polygon(
            imagem,
            cor_borda,
            contorno
        )

        pygame.draw.polygon(
            imagem,
            cor_preenchimento,
            interior
        )

        # Pequeno reflexo no coração
        pygame.draw.ellipse(
            imagem,
            cor_detalhe,
            (
                10 * escala,
                9 * escala,
                7 * escala,
                3 * escala
            )
        )

        return pygame.transform.smoothscale(
            imagem,
            (30, 28)
        )

    def _desenhar_painel_vidas(self, tela, jogador):
        x, y = 16, 15
        largura, altura = 174, 59

        painel = pygame.Surface(
            (largura, altura),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            painel,
            (27, 20, 42, 235),
            (0, 0, largura, altura),
            border_radius=11
        )

        pygame.draw.rect(
            painel,
            (174, 133, 78, 235),
            (0, 0, largura, altura),
            2,
            border_radius=11
        )

        pygame.draw.rect(
            painel,
            (91, 69, 105, 180),
            (5, 5, largura - 10, altura - 10),
            1,
            border_radius=8
        )

        tela.blit(painel, (x, y))

        total_vidas = max(1, int(config.VIDA_JOGADOR))
        vidas_atuais = max(
            0,
            min(total_vidas, int(jogador.vida))
        )

        for i in range(total_vidas):
            centro_x = x + 28 + i * 46
            centro_y = y + 29

            # Medalhão escuro atrás de cada coração
            pygame.draw.circle(
                tela,
                (40, 29, 51),
                (centro_x, centro_y),
                17
            )

            cor_aro = (
                (190, 150, 94)
                if i < vidas_atuais
                else (83, 71, 91)
            )

            pygame.draw.circle(
                tela,
                cor_aro,
                (centro_x, centro_y),
                17,
                1
            )

            coracao = (
                self.coracao_cheio
                if i < vidas_atuais
                else self.coracao_vazio
            )

            tela.blit(
                coracao,
                (centro_x - 15, centro_y - 14)
            )

    def _desenhar_titulo_fase(self, tela, numero):
        largura, altura = 184, 54
        x = config.LARGURA - largura - 16
        y = 17

        painel = pygame.Surface(
            (largura, altura),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            painel,
            (27, 20, 42, 235),
            (0, 0, largura, altura),
            border_radius=10
        )

        pygame.draw.rect(
            painel,
            (190, 150, 91, 240),
            (0, 0, largura, altura),
            2,
            border_radius=10
        )

        pygame.draw.rect(
            painel,
            (100, 76, 112, 190),
            (5, 5, largura - 10, altura - 10),
            1,
            border_radius=7
        )

        tela.blit(painel, (x, y))

        texto = self.fonte_titulo.render(
            f"FASE {numero}",
            True,
            (244, 215, 164)
        )

        posicao = texto.get_rect(
            center=(x + largura // 2, y + altura // 2)
        )

        tela.blit(texto, posicao)

        # Pequenos detalhes dourados nas laterais
        centro_y = y + altura // 2

        for lado in (x + 13, x + largura - 13):
            pygame.draw.polygon(
                tela,
                (218, 177, 112),
                [
                    (lado, centro_y - 5),
                    (lado + 4, centro_y),
                    (lado, centro_y + 5),
                    (lado - 4, centro_y)
                ]
            )

    def _desenhar_habilidade(self, tela, x, y, texto, pronta=True):
        fonte = self.fonte_habilidade.render(
            texto,
            True,
            (239, 214, 170) if pronta else (154, 143, 160)
        )

        largura = fonte.get_width() + 34
        altura = 27

        etiqueta = pygame.Surface(
            (largura, altura),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            etiqueta,
            (31, 23, 46, 220),
            (0, 0, largura, altura),
            border_radius=7
        )

        cor_borda = (
            (169, 132, 83, 220)
            if pronta
            else (95, 83, 106, 200)
        )

        pygame.draw.rect(
            etiqueta,
            cor_borda,
            (0, 0, largura, altura),
            1,
            border_radius=7
        )

        tela.blit(etiqueta, (x, y))

        # Pequeno símbolo decorativo
        pygame.draw.circle(
            tela,
            (216, 174, 104) if pronta else (112, 99, 120),
            (x + 12, y + 13),
            3
        )

        tela.blit(
            fonte,
            (x + 23, y + 5)
        )

    def _desenhar_habilidades(self, tela, jogador):
        y = 82

        if jogador.tem_salto_duplo:
            self._desenhar_habilidade(
                tela,
                17,
                y,
                "SALTO DUPLO"
            )
            y += 33

        if jogador.tem_avanco:
            pronta = jogador.recarga_avanco <= 0

            self._desenhar_habilidade(
                tela,
                17,
                y,
                "AVANÇO",
                pronta
            )

    def desenhar(self, tela, jogador, numero=1):
        self._desenhar_painel_vidas(tela, jogador)
        self._desenhar_titulo_fase(tela, numero)
        self._desenhar_habilidades(tela, jogador)
