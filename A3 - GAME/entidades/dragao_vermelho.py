"""Dragão Vermelho: chefe da Fase 4 (guardião do castelo).

Regras:
  - 5 vidas. Cada tiro que acerta tira 25% da barra da vida atual (4 tiros = 1 vida, 20 no total).
    Os 5 chumbinhos da calibre 12 contam como UM tiro (o dragão fica ~0,3 s sem aceitar outro golpe).
  - Cospe bolas de fogo pela BOCA. A direção é calculada na hora do disparo (aponta para onde o herói
    está) e depois a bola segue em linha reta: não persegue o herói.
  - De tempos em tempos levanta voo: fica exatamente 10 s no ar atirando e depois pousa.
  - Ao perder a última vida, ruge, fica atordoado e foge voando para longe (some da tela).

A Fase usa o dragão como qualquer inimigo (lista self.inimigos). As bolas de fogo vão para
self.ondas_sombrias, a mesma lista de ataques inimigos que a Fase já trata (dano ao herói, colisão e desenho).
"""
import math
import os
import random

import pygame

import config

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- ajustes fáceis (mude aqui) ----------
VIDAS = 5                      # quantidade de barras de vida
TIROS_POR_VIDA = 4             # cada tiro tira 25% de uma barra
DURACAO_VOO = 10.0             # segundos no ar atirando
VELOCIDADE_FOGO = 330.0        # px/s da bola de fogo (aumenta nas últimas vidas)
ALTURA_VOO = 110               # px acima do chão
ESCALA = 0.55                  # o sprite (520x473) vira ~286x260
INTERVALO_TIRO_SOLO = {5: 2.6, 4: 2.3, 3: 2.0, 2: 1.7, 1: 1.4}   # pausa entre ataques (por vidas restantes)
TIROS_POR_RAJADA = {5: 1, 4: 1, 3: 2, 2: 2, 1: 3}

SPRITE_W, SPRITE_H = 520, 473
PES = 468                      # linha dos pés no sprite original
CORPO_SRC = (125, 70, 505, 468)  # caixa que recebe/causa dano (corpo, sem as pontas das asas) (x0, y0, x1, y1)
BOCA_SRC = (138, 100)          # boca no sprite original (o sprite original olha para a ESQUERDA)

_cache = {}


QUADROS = {"chao": 12, "voo": 8}       # quantidade de quadros de cada animação (assets/dragao_vermelho/)


def _sprite(prefixo, indice, espelhar):
    chave = (prefixo, indice, espelhar)
    if chave not in _cache:
        caminho = os.path.join(RAIZ, "assets", "dragao_vermelho", f"{prefixo}_{indice:02d}.png")
        img = pygame.image.load(caminho).convert_alpha()
        img = pygame.transform.smoothscale(img, (int(SPRITE_W * ESCALA), int(SPRITE_H * ESCALA)))
        if espelhar:
            img = pygame.transform.flip(img, True, False)
        _cache[chave] = img
    return _cache[chave]


class BolaFogo:
    """Tiro reto: a direção é escolhida ao nascer e nunca muda."""

    def __init__(self, x, y, alvo_x, alvo_y, velocidade):
        dx, dy = alvo_x - x, alvo_y - y
        dist = math.hypot(dx, dy) or 1.0
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(dx / dist, dy / dist) * velocidade
        self.rect = pygame.Rect(0, 0, 26, 26)
        self.rect.center = (round(x), round(y))
        self.ativo = True
        self.t = 0.0
        self.rastro = []

    def atualizar(self, dt, plataformas):
        self.t += dt
        self.rastro.append((self.pos.x, self.pos.y))
        if len(self.rastro) > 7:
            self.rastro.pop(0)
        self.pos += self.vel * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if (self.pos.x < -60 or self.pos.x > config.LARGURA + 60
                or self.pos.y < -200 or self.pos.y > 900):
            self.ativo = False
            return
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                self.ativo = False
                return

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -40 or r.left > config.LARGURA + 40:
            return
        n = len(self.rastro)
        for i, (px, py) in enumerate(self.rastro):
            f = (i + 1) / (n + 1)
            raio = max(2, int(11 * f))
            p = camera.aplicar(pygame.Rect(round(px), round(py), 0, 0)).topleft
            halo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (255, 110, 30, int(150 * f)), (raio, raio), raio)
            tela.blit(halo, (p[0] - raio, p[1] - raio))
        pulso = int(math.sin(self.t * 30) * 2)
        pygame.draw.circle(tela, (200, 40, 20), r.center, 14 + pulso)
        pygame.draw.circle(tela, (255, 140, 30), r.center, 10 + pulso)
        pygame.draw.circle(tela, (255, 235, 140), r.center, 5)


class DragaoVermelho:
    eh_chefe = True
    nome = "Dragão Vermelho"

    def __init__(self, x_centro, y_base):
        limite = config.LARGURA - SPRITE_W * ESCALA - 10     # não sai pela direita da tela
        self.x_esq = float(min(x_centro - 52, limite))      # canto esquerdo do sprite
        self.x_base = self.x_esq
        self.x = self.x_esq
        self.chao_y = y_base
        self.golpes_max = VIDAS * TIROS_POR_VIDA
        self.golpes = self.golpes_max          # golpes que ainda aguenta
        self.dano = 1                          # dano ao encostar no herói
        self.vivo = True
        self.direcao = -1                      # 1 = olha para a direita, -1 = para a esquerda (vira sozinho para o herói)
        self.estado = "entrada"
        self.t_estado = 0.0
        self.tempo = 0.0
        self.altura = 0.0
        self.alvo_altura = 0.0
        self.tempo_dano = 0.0
        self.cooldown_golpe = 0.0
        self.brilho_boca = 0.0
        self.proximo_ataque = 1.2
        self.proximo_voo = random.uniform(8.0, 12.0)
        self.rajadas = []
        self.prox_tiro_ar = 0.0
        self.ondas_pendentes = []              # a Fase move estas bolas para self.ondas_sombrias
        self.tremor_pendente = False
        self.eventos = []                      # "rugido", "fogo", "vida", "derrotado", "fugiu"

    # ---------- propriedades usadas pela Fase ----------
    @property
    def vida(self):
        return self.golpes

    @property
    def vida_max(self):
        return self.golpes_max

    @property
    def vidas_restantes(self):
        """Barras de vida que ainda têm algo (5..0)."""
        return max(0, math.ceil(self.golpes / TIROS_POR_VIDA))

    @property
    def derrotado(self):
        return self.estado in ("morrendo", "fugindo")

    @property
    def topo(self):
        bob = math.sin(self.tempo * 2.4) * 3
        return self.chao_y - PES * ESCALA - self.altura + bob

    def _faixa_x(self, x0, x1):
        """Converte um intervalo x do sprite original para a tela, conforme o lado que o dragão olha."""
        if self.direcao == 1:       # espelhado
            x0, x1 = SPRITE_W - x1, SPRITE_W - x0
        return self.x + x0 * ESCALA, self.x + x1 * ESCALA

    @property
    def rect(self):
        if self.derrotado:          # derrotado: não machuca nem leva tiro
            return pygame.Rect(-9999, -9999, 1, 1)
        a, b = self._faixa_x(CORPO_SRC[0], CORPO_SRC[2])
        t = self.topo
        return pygame.Rect(round(a), round(t + CORPO_SRC[1] * ESCALA),
                           round(b - a), round((CORPO_SRC[3] - CORPO_SRC[1]) * ESCALA))

    def boca(self):
        bx, by = BOCA_SRC
        if self.direcao == 1:
            bx = SPRITE_W - bx
        return self.x + bx * ESCALA, self.topo + by * ESCALA

    # ---------- dano ----------
    def receber_dano(self, dano, origem_x):
        if self.estado in ("entrada", "morrendo", "fugindo") or self.cooldown_golpe > 0 or self.golpes <= 0:
            return
        vidas_antes = self.vidas_restantes
        self.golpes -= 1
        self.cooldown_golpe = 0.3          # os 5 chumbinhos de um disparo contam como um tiro só
        self.tempo_dano = 0.15
        if self.golpes <= 0:
            self._ir("morrendo")
            self.alvo_altura = 0.0
            self.rajadas = []
            self.eventos += ["rugido", "derrotado"]
            self.tremor_pendente = True
        elif self.vidas_restantes < vidas_antes:      # perdeu uma barra inteira
            self._ir("atordoado")
            self.alvo_altura = 0.0
            self.rajadas = []
            self.eventos += ["rugido", "vida"]
            self.tremor_pendente = True

    # ---------- lógica ----------
    def _ir(self, estado):
        self.estado = estado
        self.t_estado = 0.0

    def _pausa(self):
        return INTERVALO_TIRO_SOLO.get(self.vidas_restantes, 1.6) + random.uniform(0.0, 0.5)

    def _atirar(self, alvo):
        bx, by = self.boca()
        vel = VELOCIDADE_FOGO + (5 - self.vidas_restantes) * 25
        self.ondas_pendentes.append(BolaFogo(bx, by, alvo.rect.centerx, alvo.rect.centery, vel))
        self.eventos.append("fogo")

    def atualizar(self, dt, plataformas, alvo=None):
        self.tempo += dt
        self.t_estado += dt
        self.tempo_dano = max(0.0, self.tempo_dano - dt)
        self.cooldown_golpe = max(0.0, self.cooldown_golpe - dt)
        self.altura += (self.alvo_altura - self.altura) * min(1.0, 4.0 * dt)
        e = self.estado

        if alvo is not None and e not in ("morrendo", "fugindo"):
            self.direcao = 1 if alvo.rect.centerx >= self.x + SPRITE_W * ESCALA / 2 else -1

        if e == "entrada":
            if self.t_estado < dt * 1.5:
                self.eventos.append("rugido")
                self.tremor_pendente = True
            if self.t_estado >= 2.0:
                self._ir("ocioso")

        elif e == "ocioso":
            self.brilho_boca = 0.0
            self.proximo_ataque -= dt
            self.proximo_voo -= dt
            if self.proximo_voo <= 0:
                self._ir("decolando")
                self.alvo_altura = ALTURA_VOO
                self.x_base = self.x
                self.eventos.append("rugido")
            elif self.proximo_ataque <= 0:
                self._ir("mirando")

        elif e == "mirando":
            self.brilho_boca = min(1.0, self.t_estado / 0.7)
            if self.t_estado >= 0.7:
                n = TIROS_POR_RAJADA.get(self.vidas_restantes, 1)
                self.rajadas = [0.35 * i for i in range(n)]
                self._ir("cuspindo")

        elif e == "cuspindo":
            while self.rajadas and self.t_estado >= self.rajadas[0]:
                self.rajadas.pop(0)
                if alvo is not None:
                    self._atirar(alvo)
            if not self.rajadas and self.t_estado >= 0.9:
                self.brilho_boca = 0.0
                self.proximo_ataque = self._pausa()
                self._ir("ocioso")

        elif e == "decolando":
            if self.t_estado >= 0.9:
                self._ir("voando")
                self.prox_tiro_ar = 0.7

        elif e == "voando":
            # exatamente DURACAO_VOO segundos no ar, balançando de um lado para o outro
            self.x = self.x_base + 110.0 * math.sin(self.t_estado * 0.9)
            self.x = max(10.0, min(self.x, config.LARGURA - SPRITE_W * ESCALA - 10))
            self.prox_tiro_ar -= dt
            self.brilho_boca = 0.7 if self.prox_tiro_ar < 0.35 else 0.0
            if self.prox_tiro_ar <= 0 and alvo is not None:
                self._atirar(alvo)
                self.prox_tiro_ar = 1.3 if self.vidas_restantes > 2 else 1.0
            if self.t_estado >= DURACAO_VOO:
                self._ir("pousando")
                self.alvo_altura = 0.0
                self.brilho_boca = 0.0

        elif e == "pousando":
            self.x += (self.x_base - self.x) * min(1.0, 3.0 * dt)
            if self.altura < 4.0 and self.t_estado > 0.5:
                self.altura = 0.0
                self.eventos.append("pouso")
                self.tremor_pendente = True
                self.proximo_ataque = 1.4
                self.proximo_voo = random.uniform(10.0, 16.0)
                self._ir("ocioso")

        elif e == "atordoado":
            self.brilho_boca = 0.0
            self.x += (self.x_base - self.x) * min(1.0, 3.0 * dt)
            if self.t_estado >= 1.5:
                self.proximo_ataque = 1.2
                self._ir("ocioso")

        elif e == "morrendo":
            self.brilho_boca = 0.0
            if self.t_estado >= 1.6:
                self._ir("fugindo")

        elif e == "fugindo":
            # derrotado, sai voando para longe pela parte de cima da tela
            self.x -= 90.0 * dt
            self.alvo_altura = 1200.0
            self.altura += 260.0 * dt * (1.0 + self.t_estado)
            if self.topo < -420:
                self.vivo = False
                self.eventos.append("fugiu")

    # ---------- desenho ----------
    def _quadro_atual(self):
        """Animação: no chão ele respira e balança asas e cauda; no ar bate as asas."""
        no_ar = self.estado in ("decolando", "voando", "pousando", "fugindo") and self.altura > 12
        if no_ar:
            return "voo", int(self.tempo * 14) % QUADROS["voo"]
        return "chao", int(self.tempo * 10) % QUADROS["chao"]

    def _desenhar_sombra(self, tela, camera):
        if self.estado == "fugindo" and self.altura > 300:
            return
        fator = max(0.35, 1.0 - self.altura / 380.0)
        w, h = int(270 * fator), int(20 * fator)
        sombra = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (10, 6, 16, int(120 * fator)), (0, 0, w, h))
        cx = self.x + SPRITE_W * ESCALA / 2
        pos = camera.aplicar(pygame.Rect(round(cx - w / 2), round(self.chao_y - h // 2 + 3), 0, 0)).topleft
        tela.blit(sombra, pos)

    def desenhar(self, tela, camera):
        self._desenhar_sombra(tela, camera)
        prefixo, indice = self._quadro_atual()
        img = _sprite(prefixo, indice, self.direcao == 1)
        pos = [round(self.x), round(self.topo)]
        if self.estado in ("mirando", "morrendo"):
            pos[0] += random.randint(-2, 2)
        pos = camera.aplicar(pygame.Rect(pos[0], pos[1], 0, 0)).topleft
        tela.blit(img, pos)
        if self.tempo_dano > 0:                    # pisca branco ao levar tiro
            brilho = img.copy()
            brilho.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_ADD)
            tela.blit(brilho, pos)
        if self.brilho_boca > 0 and not self.derrotado:     # luz de fogo na boca antes de cuspir
            bx, by = self.boca()
            c = camera.aplicar(pygame.Rect(round(bx), round(by), 0, 0)).topleft
            for raio, alfa in ((30, 40), (20, 80), (10, 170)):
                r = int(raio * (0.5 + 0.7 * self.brilho_boca))
                halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(halo, (255, 150, 40, alfa), (r, r), r)
                tela.blit(halo, (c[0] - r, c[1] - r))
