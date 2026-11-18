import math
import random
import pygame
import config


class ProjetilPlasma:
    """Disparo de energia de plasma com núcleo brilhante, halo e rastro."""

    def __init__(self, x, y, direcao, vy=0):
        self.pos = pygame.Vector2(x, y)
        self.direcao = direcao
        self.velocidade = 780
        self.vy = vy
        self.dano = 2
        self.ativo = True
        self.tempo_vida = 1.4
        self.rect = pygame.Rect(x - 14, y - 8, 28, 16)
        self.rastro = []

    def atualizar(self, dt, solidos, largura_mundo):
        self.tempo_vida -= dt
        if self.tempo_vida <= 0:
            self.ativo = False
            return

        self.rastro.append((self.pos.x, self.pos.y))
        if len(self.rastro) > 8:
            self.rastro.pop(0)

        self.pos.x += self.direcao * self.velocidade * dt
        self.pos.y += self.vy * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.rect.left < 0 or self.rect.right > largura_mundo:
            self.ativo = False
            return

        for s in solidos:
            if self.rect.colliderect(s.rect):
                self.ativo = False
                return

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -60 or r.left > config.LARGURA + 60:
            return

        for idx, (rx, ry) in enumerate(self.rastro):
            ponto = camera.aplicar(pygame.Rect(rx, ry, 1, 1)).topleft
            progresso = (idx + 1) / max(1, len(self.rastro))
            raio = int(10 * progresso)
            surf = pygame.Surface((raio * 2 + 2, raio * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (0, 210, 255, int(110 * progresso)), (raio + 1, raio + 1), raio)
            tela.blit(surf, (ponto[0] - raio - 1, ponto[1] - raio - 1))

        halo = pygame.Surface((64, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (0, 180, 255, 90), (0, 2, 64, 36))
        pygame.draw.ellipse(halo, (80, 240, 255, 170), (10, 8, 44, 24))
        pygame.draw.ellipse(halo, (240, 255, 255, 255), (18, 13, 28, 14))
        tela.blit(halo, (r.centerx - 32, r.centery - 20))


class ParticulaPlasma:
    """Faíscas de impacto quando o plasma acerta um inimigo ou parede."""

    def __init__(self, x, y, cor=(80, 240, 255)):
        ang = random.uniform(0, math.tau)
        vel = random.uniform(90, 320)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(math.cos(ang) * vel, math.sin(ang) * vel)
        self.vida = random.uniform(0.18, 0.38)
        self.vida_max = self.vida
        self.cor = cor
        self.raio = random.randint(2, 5)

    def atualizar(self, dt):
        self.vida -= dt
        self.pos += self.vel * dt
        self.vel *= 0.92

    def desenhar(self, tela, camera):
        if self.vida <= 0:
            return
        p = camera.aplicar(pygame.Rect(round(self.pos.x), round(self.pos.y), 1, 1)).topleft
        alfa = int(255 * (self.vida / self.vida_max))
        surf = pygame.Surface((self.raio * 2 + 2, self.raio * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.cor, alfa), (self.raio + 1, self.raio + 1), self.raio)
        tela.blit(surf, (p[0] - self.raio, p[1] - self.raio))