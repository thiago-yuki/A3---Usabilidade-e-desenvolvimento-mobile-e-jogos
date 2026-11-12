import pygame
import config


class Barreira:
    """Parede rachada: bloqueia o caminho até o Dáron atravessá-la com o avanço."""

    def __init__(self, x, y, largura, altura):
        self.rect = pygame.Rect(x, y, largura, altura)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < 0 or r.left > config.LARGURA:
            return
        pygame.draw.rect(tela, (150, 100, 60), r)
        for y in range(r.y + 18, r.bottom - 8, 48):   # rachaduras
            pygame.draw.line(tela, (60, 35, 20), (r.x + 6, y), (r.right - 6, y + 14), 3)
