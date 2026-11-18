import math
import random
import pygame
import config


class Tocha:
    """Tocha que ilumina a floresta sombria na Fase 3."""

    def __init__(self, x_centro, y_centro):
        self.rect = pygame.Rect(0, 0, 16, 36)
        self.rect.center = (x_centro, y_centro)
        self.t = random.uniform(0, 10)

    def atualizar(self, dt):
        self.t += dt

    def raio_luz(self):
        return int(190 + math.sin(self.t * 9) * 10 + math.cos(self.t * 15) * 6)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -40 or r.left > config.LARGURA + 40:
            return

        # Cabo de madeira e suporte de ferro
        pygame.draw.rect(tela, (110, 68, 35), (r.centerx - 3, r.centery - 4, 6, 22), border_radius=2)
        pygame.draw.rect(tela, (70, 75, 85), (r.centerx - 5, r.centery - 6, 10, 5))

        # Chama animada
        osc = math.sin(self.t * 14) * 3
        cx, cy = r.centerx, r.centery - 10
        pygame.draw.circle(tela, (255, 110, 20), (cx, cy), 9)
        pygame.draw.polygon(tela, (255, 180, 40), [
            (cx - 7, cy + 2),
            (cx + osc, cy - 15),
            (cx + 7, cy + 2),
        ])
        pygame.draw.circle(tela, (255, 245, 180), (cx, cy), 4)