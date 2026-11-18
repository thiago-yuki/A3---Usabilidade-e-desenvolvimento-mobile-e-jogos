import pygame
import config


class Escada:
    """Escada vertical para subir e descer níveis do cemitério."""

    def __init__(self, x, y, largura, altura):
        self.rect = pygame.Rect(x, y, largura, altura)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < 0 or r.left > config.LARGURA:
            return

        cor_ferro = (75, 85, 100)
        cor_brilho = (115, 130, 150)

        # Trilhos laterais
        pygame.draw.rect(tela, cor_ferro, (r.x + 6, r.y, 5, r.height))
        pygame.draw.rect(tela, cor_ferro, (r.right - 11, r.y, 5, r.height))

        # Degraus a cada 18 pixels
        for dy in range(r.y + 8, r.bottom - 4, 18):
            pygame.draw.rect(tela, cor_ferro, (r.x + 6, dy, r.width - 12, 4))
            pygame.draw.line(tela, cor_brilho, (r.x + 7, dy), (r.right - 8, dy), 1)