import math
import pygame
import config

TEXTOS = {
    "salto_duplo": ("Relíquia do Salto Duplo", "Aperte pular de novo no ar para saltar mais alto!"),
    "avanco": ("Relíquia do Avanço", "Aperte K ou SHIFT para avançar. Barreiras rachadas se quebram!"),
}


class Reliquia:
    def __init__(self, tipo, x_centro, y_centro):
        self.tipo = tipo
        self.rect = pygame.Rect(0, 0, 30, 30)
        self.rect.center = (x_centro, y_centro)
        self.coletada = False
        self.t = 0.0

    @property
    def textos(self):
        return TEXTOS[self.tipo]

    def atualizar(self, dt):
        self.t += dt

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < 0 or r.left > config.LARGURA:
            return
        cx = r.centerx
        cy = int(r.centery + math.sin(self.t * 3) * 5)   # flutua
        pontos = [(cx, cy - 18), (cx + 14, cy), (cx, cy + 18), (cx - 14, cy)]
        pygame.draw.polygon(tela, config.DOURADO, pontos)
        pygame.draw.polygon(tela, config.BRANCO, pontos, 2)
