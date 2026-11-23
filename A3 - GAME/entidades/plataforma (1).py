import pygame
import config


class Plataforma:
    def __init__(self, x, y, largura, altura):
        self.rect = pygame.Rect(x, y, largura, altura)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < 0 or r.left > config.LARGURA:   # fora da tela: nem desenha
            return
        pygame.draw.rect(tela, config.CINZA, r)
        pygame.draw.rect(tela, config.BRANCO, (r.x, r.y, r.width, 3))  # faixa clara no topo
