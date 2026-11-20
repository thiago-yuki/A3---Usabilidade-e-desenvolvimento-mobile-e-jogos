"""O herói na batalha final: o Jogador do jogo base, com vida em meios-corações,
tiro de gosma e o sprite de armadura prateada no lugar do retângulo."""
import pygame

import config
from entidades.jogador import Jogador
from sistemas.recursos import imagem

ESCALA = 0.64                 # o sprite (240x244) é reduzido para ~150 px de altura
ANCORA_X, ANCORA_Y = 88, 234  # ponto do sprite que fica sob os pés (centro do corpo, sola da bota)
LARGURA_SPRITE = 240

# ---- Espada: mude aqui para deixar mais curta ou mais longa ----
ALCANCE_ESPADA = 170          # antes era 84
ALTURA_ESPADA = 130           # antes era 100
PONTA_LAMINA_X = 95           # onde a lâmina do sprite termina (px à frente do centro do herói)
PONTA_LAMINA_Y = 82           # altura da lâmina em relação aos pés (px)


class HeroiBatalha(Jogador):
    LARGURA = 56
    ALTURA = 124

    def __init__(self, x, y):
        super().__init__(x, y)
        self.velocidade = 340
        self.forca_pulo = 860
        self.alcance_ataque = ALCANCE_ESPADA   # quanto a espada alcança à frente do herói (px)
        self.altura_ataque = ALTURA_ESPADA     # altura da área do golpe (px)
        self.vida = config.BATALHA_VIDA_HEROI
        self.recarga_gosma = 0.0
        self.tempo_anim = 0.0

    # ---------- gosma ----------
    def pode_atirar(self):
        return self.recarga_gosma <= 0 and self.recuo <= 0

    def atirar(self):
        self.recarga_gosma = config.BATALHA_RECARGA_GOSMA

    @property
    def boca_gosma(self):
        return (self.rect.centerx + self.direcao * 48, self.rect.top + 56)

    # ---------- atualização ----------
    def atualizar(self, dt, plataformas, largura_mundo):
        self.recarga_gosma = max(0.0, self.recarga_gosma - dt)
        self.tempo_anim += dt
        super().atualizar(dt, plataformas, largura_mundo)

    # ---------- desenho ----------
    def _sprite(self):
        if self.atacando:
            return "heroi_ataque.png"
        if self.no_chao and abs(self.vel.x) > 20:
            return ("heroi_andando1.png", "heroi_parado.png", "heroi_andando2.png", "heroi_parado.png")[
                int(self.tempo_anim * 9) % 4]
        return "heroi_parado.png"

    def desenhar(self, tela, nome=None, escala=ESCALA, alfa=255):
        """Desenha o herói com os pés em rect.bottom. (nome/escala/alfa servem para as cutscenes)"""
        if nome is None:
            if self.invencivel > 0 and not self.avancando and int(self.invencivel * 20) % 2 == 0:
                return  # pisca enquanto está invencível
            nome = self._sprite()
        espelhar = self.direcao == -1
        img = imagem(nome, escala, espelhar)
        ax = (LARGURA_SPRITE - ANCORA_X) if espelhar else ANCORA_X
        x = self.rect.centerx - round(ax * escala)
        y = self.rect.bottom - round(ANCORA_Y * escala)
        if self.avancando:  # rastro do avanço
            rastro = imagem(nome, escala, espelhar)
            rastro.set_alpha(80)
            tela.blit(rastro, (x - self.direcao * 34, y))
            rastro.set_alpha(255)
        if alfa < 255:
            img = img.copy()
            img.set_alpha(alfa)
        tela.blit(img, (x, y))
        if nome == "heroi_ataque.png" and alfa >= 255:
            self._desenhar_lamina_longa(tela)

    def _desenhar_lamina_longa(self, tela):
        """Prolonga a lâmina do sprite até o fim da área do golpe, para o alcance ficar visível."""
        d = self.direcao
        x0 = self.rect.centerx + d * PONTA_LAMINA_X
        x1 = self.rect.right + self.alcance_ataque if d == 1 else self.rect.left - self.alcance_ataque
        y = self.rect.bottom - PONTA_LAMINA_Y
        if (x1 - x0) * d <= 0:
            return
        lamina = [(x0, y - 7), (x1, y - 1), (x1, y + 1), (x0, y + 7)]
        pygame.draw.polygon(tela, (226, 232, 244), lamina)
        pygame.draw.line(tela, (255, 255, 255), (x0, y - 3), (x1, y), 2)
        brilho = pygame.Surface((abs(x1 - x0) + 20, 44), pygame.SRCALPHA)
        pygame.draw.ellipse(brilho, (255, 255, 255, 60), brilho.get_rect())
        tela.blit(brilho, (min(x0, x1) - 10, y - 22))
