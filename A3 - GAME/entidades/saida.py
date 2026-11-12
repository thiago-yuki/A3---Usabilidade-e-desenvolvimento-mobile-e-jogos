import pygame
import config


class Saida:
    """Portal que leva para a próxima fase."""

    def __init__(self, x, y, largura, altura):
        self.rect = pygame.Rect(x, y, largura, altura)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < 0 or r.left > config.LARGURA:
            return
        pygame.draw.ellipse(tela, config.DOURADO, r, 4)
        pygame.draw.ellipse(tela, (90, 60, 20), r.inflate(-16, -16))
