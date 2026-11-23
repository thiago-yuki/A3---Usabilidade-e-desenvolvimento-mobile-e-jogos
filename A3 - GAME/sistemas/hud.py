import os

import pygame

import config


class Hud:
    def __init__(self):
        raiz_projeto = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        caminho_fonte = os.path.join(
            raiz_projeto, "assets", "fontes", "Cinzel-SemiBold.ttf"
        )

        try:
            self.fonte_titulo = pygame.font.Font(caminho_fonte, 23)
        except (pygame.error, OSError):
            self.fonte_titulo = pygame.font.Font(None, 30)

        self.fonte_habilidade = pygame.font.Font(None, 19)
        self.fonte_comandos = pygame.font.Font(None, 20)
        self.coracao_cheio = self._criar_coracao(True)
        self.coracao_vazio = self._criar_coracao(False)

    def _criar_coracao(self, ativo):
        escala = 3
        imagem = pygame.Surface((36 * escala, 34 * escala), pygame.SRCALPHA)
        contorno = [
            (18, 32), (5, 21), (2, 17), (2, 11),
            (5, 6), (10, 4), (14, 5), (18, 10),
            (22, 5), (27, 4), (32, 6), (34, 11),
            (34, 17), (31, 21),
        ]
        interior = [
            (18, 28), (8, 19), (5, 16), (5, 11),
            (8, 8), (12, 7), (15, 9), (18, 13),
            (21, 9), (24, 7), (29, 8), (31, 11),
            (31, 16), (28, 19),
        ]
        contorno = [(x * escala, y * escala) for x, y in contorno]
        interior = [(x * escala, y * escala) for x, y in interior]

        if ativo:
            cor_borda = (220, 171, 105)
            cor_preenchimento = (185, 61, 94)
            cor_detalhe = (249, 151, 171)
        else:
            cor_borda = (104, 88, 112)
            cor_preenchimento = (65, 49, 75)
            cor_detalhe = (91, 76, 99)

        pygame.draw.polygon(imagem, cor_borda, contorno)
        pygame.draw.polygon(imagem, cor_preenchimento, interior)
        pygame.draw.ellipse(
            imagem, cor_detalhe, (10 * escala, 9 * escala, 7 * escala, 3 * escala)
        )
        return pygame.transform.smoothscale(imagem, (30, 28))

    def _desenhar_painel_vidas(self, tela, jogador):
        x, y = 16, 15
        total_vidas = max(1, int(jogador.vida_max))
        espacamento = 46 if total_vidas <= 3 else 37
        largura = max(174, 59 + (total_vidas - 1) * espacamento)
        altura = 59
        painel = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(
            painel, (27, 20, 42, 235), (0, 0, largura, altura), border_radius=11
        )
        pygame.draw.rect(
            painel,
            (174, 133, 78, 235),
            (0, 0, largura, altura),
            2,
            border_radius=11,
        )
        pygame.draw.rect(
            painel,
            (91, 69, 105, 180),
            (5, 5, largura - 10, altura - 10),
            1,
            border_radius=8,
        )
        tela.blit(painel, (x, y))

        vidas_atuais = max(0, min(total_vidas, int(jogador.vida)))
        for i in range(total_vidas):
            centro_x = x + 28 + i * espacamento
            centro_y = y + 29
            pygame.draw.circle(tela, (40, 29, 51), (centro_x, centro_y), 17)
            cor_aro = (
                (190, 150, 94) if i < vidas_atuais else (83, 71, 91)
            )
            pygame.draw.circle(tela, cor_aro, (centro_x, centro_y), 17, 1)
            coracao = self.coracao_cheio if i < vidas_atuais else self.coracao_vazio
            tela.blit(coracao, (centro_x - 15, centro_y - 14))

    def desenhar_vidas(self, tela, jogador):
        self._desenhar_painel_vidas(tela, jogador)

    def _desenhar_titulo_fase(self, tela, numero):
        largura, altura = 184, 54
        x = config.LARGURA - largura - 16
        y = 17
        painel = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(
            painel, (27, 20, 42, 235), (0, 0, largura, altura), border_radius=10
        )
        pygame.draw.rect(
            painel,
            (190, 150, 91, 240),
            (0, 0, largura, altura),
            2,
            border_radius=10,
        )
        pygame.draw.rect(
            painel,
            (100, 76, 112, 190),
            (5, 5, largura - 10, altura - 10),
            1,
            border_radius=7,
        )
        tela.blit(painel, (x, y))

        texto = self.fonte_titulo.render(f"FASE {numero}", True, (244, 215, 164))
        tela.blit(texto, texto.get_rect(center=(x + largura // 2, y + altura // 2)))
        centro_y = y + altura // 2
        for lado in (x + 13, x + largura - 13):
            pygame.draw.polygon(
                tela,
                (218, 177, 112),
                [
                    (lado, centro_y - 5),
                    (lado + 4, centro_y),
                    (lado, centro_y + 5),
                    (lado - 4, centro_y),
                ],
            )

    def _desenhar_habilidade(self, tela, x, y, texto, pronta=True):
        cor_texto = (239, 214, 170) if pronta else (154, 143, 160)
        fonte = self.fonte_habilidade.render(texto, True, cor_texto)
        largura, altura = fonte.get_width() + 34, 27
        etiqueta = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(
            etiqueta, (31, 23, 46, 220), (0, 0, largura, altura), border_radius=7
        )
        cor_borda = (169, 132, 83, 220) if pronta else (95, 83, 106, 200)
        pygame.draw.rect(
            etiqueta, cor_borda, (0, 0, largura, altura), 1, border_radius=7
        )
        tela.blit(etiqueta, (x, y))
        cor_simbolo = (216, 174, 104) if pronta else (112, 99, 120)
        pygame.draw.circle(tela, cor_simbolo, (x + 12, y + 13), 3)
        tela.blit(fonte, (x + 23, y + 5))

    def _desenhar_habilidades(self, tela, jogador):
        y = 82
        if jogador.tem_salto_duplo:
            self._desenhar_habilidade(tela, 17, y, "Salto duplo")
            y += 33
        if jogador.tem_avanco:
            pronta = jogador.recarga_avanco <= 0
            if jogador.modo_guerreira:
                texto = "Esquiva Sombria (SHIFT)" if pronta else "Esquiva Sombria..."
            else:
                texto = "Avanço (K / SHIFT)"
            self._desenhar_habilidade(tela, 17, y, texto, pronta)

    def desenhar_comandos(self, tela, texto):
        x, y = 12, config.ALTURA - 42
        largura, altura = config.LARGURA - 24, 30
        painel = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(
            painel, (27, 20, 42, 220), (0, 0, largura, altura), border_radius=8
        )
        pygame.draw.rect(
            painel,
            (169, 132, 83, 210),
            (0, 0, largura, altura),
            1,
            border_radius=8,
        )
        tela.blit(painel, (x, y))
        imagem = self.fonte_comandos.render(texto, True, (225, 220, 210))
        tela.blit(imagem, imagem.get_rect(center=(config.LARGURA // 2, y + altura // 2)))

    def desenhar(self, tela, jogador, numero=1):
        self.desenhar_vidas(tela, jogador)
        self._desenhar_titulo_fase(tela, numero)
        self._desenhar_habilidades(tela, jogador)
