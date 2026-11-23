"""Projéteis da batalha final: fogo do dragão (bola e onda no chão) e a gosma do herói."""
import math

import pygame

from sistemas.recursos import sprite

_rotacionadas = {}


def _girar(nome, escala, angulo):
    """Imagem do projétil girada (com cache a cada 6 graus)."""
    chave = (nome, escala, round(angulo / 6))
    if chave not in _rotacionadas:
        _rotacionadas[chave] = pygame.transform.rotate(sprite(nome, escala), round(angulo / 6) * 6)
    return _rotacionadas[chave]


class BolaDeFogo:
    """Bola de fogo mirada no herói."""
    RAIO = 17

    def __init__(self, x, y, alvo, velocidade=470.0, desvio_graus=0.0):
        ang = math.atan2(alvo[1] - y, alvo[0] - x) + math.radians(desvio_graus)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(math.cos(ang) * velocidade, math.sin(ang) * velocidade)
        self.angulo = math.degrees(math.atan2(-self.vel.y, self.vel.x))
        self.dano = 1
        self.vivo = True
        self.bateu_chao = False

    @property
    def rect(self):
        r = pygame.Rect(0, 0, self.RAIO * 2, self.RAIO * 2)
        r.center = (round(self.pos.x), round(self.pos.y))
        return r

    def atualizar(self, dt, chao_y, largura):
        self.pos += self.vel * dt
        if self.pos.y >= chao_y - 10:
            self.bateu_chao = True
            self.vivo = False
        elif self.pos.x < -120 or self.pos.x > largura + 120 or self.pos.y < -160:
            self.vivo = False

    def desenhar(self, tela):
        img = _girar("fogo", 0.62, self.angulo - 90)
        r = img.get_rect()
        r.center = (round(self.pos.x), round(self.pos.y))
        tela.blit(img, r)


class OndaDeFogo:
    """Chamas que correm pelo chão em direção ao herói: é preciso pular."""
    LARGURA = 96
    ALTURA = 52

    def __init__(self, x, chao_y, velocidade=-340.0):
        self.x = float(x)
        self.chao_y = chao_y
        self.vel = velocidade
        self.dano = 1
        self.vivo = True
        self.t = 0.0

    @property
    def rect(self):
        return pygame.Rect(round(self.x), self.chao_y - self.ALTURA, self.LARGURA, self.ALTURA)

    def atualizar(self, dt):
        self.t += dt
        self.x += self.vel * dt
        if self.x < -self.LARGURA - 40:
            self.vivo = False

    def desenhar(self, tela):
        for indice, (deslocamento, escala) in enumerate(((20, 0.62), (48, 0.82), (76, 0.62))):
            img = sprite("fogo", escala, espelhar=self.vel < 0)
            r = img.get_rect()
            ondulacao = round(3 * math.sin(self.t * 18 + indice * 1.7))
            r.midbottom = (
                round(self.x + deslocamento),
                self.chao_y + 6 - ondulacao,
            )
            tela.blit(img, r)


class Gosma:
    """Tiro do herói: sai em linha reta, na direção em que ele está olhando (1 = direita, -1 = esquerda)."""
    RAIO = 14

    def __init__(self, x, y, direcao, velocidade=680.0):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(direcao * velocidade, 0)
        self.dano = 2
        self.vivo = True
        self.t = 0.0

    @property
    def rect(self):
        r = pygame.Rect(0, 0, self.RAIO * 2, self.RAIO * 2)
        r.center = (round(self.pos.x), round(self.pos.y))
        return r

    def atualizar(self, dt, chao_y, largura):
        self.t += dt
        self.pos += self.vel * dt
        if self.pos.y >= chao_y or self.pos.x < -60 or self.pos.x > largura + 60 or self.pos.y < -100:
            self.vivo = False

    def desenhar(self, tela):
        img = sprite("gosma", 0.62)
        r = img.get_rect()
        r.center = (round(self.pos.x), round(self.pos.y))
        tela.blit(img, r)
