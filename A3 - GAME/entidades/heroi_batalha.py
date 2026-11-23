"""O herói na batalha final, usando o visual da personagem das fases."""
import math

import pygame

import config
from entidades.jogador import Jogador

ALCANCE_ESPADA = 170
ALTURA_ESPADA = 130
DURACAO_ESPADA = 0.24


class HeroiBatalha(Jogador):
    LARGURA = 53
    ALTURA = 75

    def __init__(self, x, y):
        super().__init__(x, y)
        self.velocidade = 340
        self.forca_pulo = 860
        self.alcance_ataque = ALCANCE_ESPADA   # quanto a espada alcança à frente do herói (px)
        self.altura_ataque = ALTURA_ESPADA     # altura da área do golpe (px)
        self.vida_max = config.BATALHA_VIDA_HEROI
        self.vida = config.BATALHA_VIDA_HEROI
        self.recarga_gosma = 0.0

    # ---------- gosma ----------
    def pode_atirar(self):
        return self.recarga_gosma <= 0 and self.recuo <= 0

    def atirar(self):
        self.recarga_gosma = config.BATALHA_RECARGA_GOSMA

    def atacar(self):
        if self.tempo_recarga > 0:
            return False
        self.escalando = False
        self.tempo_ataque = DURACAO_ESPADA
        self.tempo_recarga = 0.42
        self.alvos_acertados.clear()
        return True

    @property
    def hitbox_ataque(self):
        if not self.atacando:
            return None
        topo = self.rect.centery - self.altura_ataque // 2
        if self.direcao > 0:
            return pygame.Rect(
                self.rect.right, topo, self.alcance_ataque, self.altura_ataque
            )
        return pygame.Rect(
            self.rect.left - self.alcance_ataque,
            topo,
            self.alcance_ataque,
            self.altura_ataque,
        )

    @property
    def boca_gosma(self):
        return (self.rect.centerx + self.direcao * 48, self.rect.top + 56)

    # ---------- atualização ----------
    def atualizar(self, dt, plataformas, largura_mundo):
        self.recarga_gosma = max(0.0, self.recarga_gosma - dt)
        super().atualizar(dt, plataformas, largura_mundo)

    # ---------- desenho ----------
    def imagem_personagem(self, tamanho, espelhar=None, ocultar_braco_arma=False):
        base = pygame.Surface((40, 56), pygame.SRCALPHA)
        self._desenhar_guerreira(
            base, base.get_rect(), desenhar_arma=False,
            ocultar_braco_arma=ocultar_braco_arma,
        )
        if espelhar is not None and espelhar != (self.direcao == -1):
            base = pygame.transform.flip(base, True, False)
        return pygame.transform.smoothscale(base, tamanho)

    def desenhar(self, tela, alfa=255):
        if self.invencivel > 0 and not self.avancando and int(self.invencivel * 20) % 2 == 0:
            return

        img = self.imagem_personagem(
            (self.LARGURA, self.ALTURA), ocultar_braco_arma=True
        )
        x = self.rect.centerx - img.get_width() // 2
        y = self.rect.bottom - img.get_height()
        if alfa < 255:
            img = img.copy()
            img.set_alpha(alfa)
        tela.blit(img, (x, y))
        if alfa >= 255:
            self._desenhar_espada(tela)

    def _desenhar_espada(self, tela):
        d = self.direcao
        if self.atacando:
            progresso = max(0.0, min(1.0, 1.0 - self.tempo_ataque / DURACAO_ESPADA))
            suave = progresso * progresso * (3 - 2 * progresso)
            angulo = math.radians(-150 + 185 * suave)
            angulo_braco = math.radians(-105 + 125 * suave)
        else:
            progresso = 1.0
            angulo = math.radians(-55)
            angulo_braco = math.radians(-48)

        ombro = (self.rect.centerx + d * 9, self.rect.bottom - 47)
        punho = (
            round(ombro[0] + math.cos(angulo_braco) * 18 * d),
            round(ombro[1] + math.sin(angulo_braco) * 18),
        )
        cotovelo = (
            round((ombro[0] + punho[0]) / 2 + d * 2),
            round((ombro[1] + punho[1]) / 2 + 3),
        )
        pygame.draw.lines(tela, (42, 46, 58), False, (ombro, cotovelo, punho), 7)
        pygame.draw.lines(tela, (206, 158, 130), False, (ombro, cotovelo, punho), 4)
        pygame.draw.circle(tela, (238, 194, 165), punho, 4)

        def ponto(distancia, deslocamento=0):
            angulo_ponto = angulo + deslocamento
            return (
                round(punho[0] + d * math.cos(angulo_ponto) * distancia),
                round(punho[1] + math.sin(angulo_ponto) * distancia),
            )

        if self.atacando and progresso > 0.04:
            inicio_rastro = max(0.0, progresso - 0.2)
            angulo_inicio = math.radians(-150 + 185 * inicio_rastro)
            pontos_rastro = []
            for i in range(10):
                t = i / 9
                a = angulo_inicio + (angulo - angulo_inicio) * t
                pontos_rastro.append((
                    round(punho[0] + d * math.cos(a) * 45),
                    round(punho[1] + math.sin(a) * 45),
                ))
            alfa = int(150 * (1.0 - progresso))
            rastro = pygame.Surface((120, 120), pygame.SRCALPHA)
            local = [(x - punho[0] + 60, y - punho[1] + 60) for x, y in pontos_rastro]
            pygame.draw.lines(rastro, (213, 226, 249, alfa), False, local, 7)
            pygame.draw.lines(rastro, (255, 255, 255, alfa), False, local, 2)
            tela.blit(rastro, (punho[0] - 60, punho[1] - 60))

        guarda = ponto(8)
        ponta = ponto(48)
        base_esquerda = ponto(8, math.pi / 2)
        base_direita = ponto(8, -math.pi / 2)
        ponta_esquerda = ponto(48, math.pi / 2)
        ponta_direita = ponto(48, -math.pi / 2)
        pygame.draw.line(tela, (91, 61, 43), ponto(-5), guarda, 4)
        pygame.draw.line(
            tela, (204, 174, 123),
            ponto(6, math.pi / 2), ponto(6, -math.pi / 2), 3,
        )
        pygame.draw.polygon(
            tela, (55, 62, 78),
            (base_esquerda, ponta_esquerda, ponta_direita, base_direita),
        )
        pygame.draw.polygon(
            tela, (226, 232, 244),
            (ponto(10, math.pi / 2), ponto(46, math.pi / 2),
             ponto(46, -math.pi / 2), ponto(10, -math.pi / 2)),
        )
        pygame.draw.line(tela, (255, 255, 255), ponto(10), ponta, 2)
