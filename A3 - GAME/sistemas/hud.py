import pygame
import config


class Hud:
    def __init__(self):
        self.fonte = pygame.font.Font(None, 24)

    def desenhar(self, tela, jogador):
        for i in range(jogador.vida_max):
            cor = config.VERMELHO if i < jogador.vida else (60, 40, 40)
            pygame.draw.rect(tela, cor, (16 + i * 34, 40, 26, 26), border_radius=6)

        y = 74
        if jogador.tem_salto_duplo:
            tela.blit(self.fonte.render("Salto duplo", True, config.DOURADO), (16, y))
            y += 22
        if jogador.tem_avanco:
            pronto = jogador.recarga_avanco <= 0
            if jogador.modo_guerreira:
                rotulo = "Esquiva Sombria (SHIFT)" if pronto else "Esquiva Sombria..."
            else:
                rotulo = "Avanço (K / SHIFT)"
            cor = config.DOURADO if pronto else config.CINZA
            tela.blit(self.fonte.render(rotulo, True, cor), (16, y))