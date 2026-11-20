"""O dragão da batalha final.

Estados: entrada -> ocioso -> (mirando -> cuspindo) | onda | (decolando -> voando -> pousando)
         atordoado (ao perder uma barra) | morrendo -> fugindo (cutscene)

O dragão não mexe em nada fora dele: avisa a cena por self.eventos (lista de tuplas):
  ("rugido",) ("projetil", objeto) ("tremor", forca, tempo) ("dano",) ("barra",) ("morreu",)
  ("asas", volume) ("pouso",) ("fogo",)
"""
import math
import random

import pygame

import config
from entidades.projeteis import BolaDeFogo, OndaDeFogo
from sistemas.recursos import imagem

ESC = 0.87            # sprite 520x372 -> ~452x324: o dobro da altura do herói
PES = 351             # linha dos pés no sprite original
CORPO = (150, 124, 394, 352)    # caixa do corpo no sprite original (x0, y0, x1, y1)
CABECA = (22, 40, 182, 142)
BOCA = (30, 112)

PAUSA = {3: 2.2, 2: 1.7, 1: 1.2}              # tempo entre ataques conforme as barras restantes
TIROS = {3: 1, 2: 2, 1: 3}                    # bolas de fogo por rajada
VEL_FOGO = {3: 430.0, 2: 480.0, 1: 540.0}
INTERVALO_VOO = {3: 1.3, 2: 1.0, 1: 0.8}      # tempo entre tiros no ar
ALTURA_VOO = 210


class Dragao:
    def __init__(self, x_esquerda, chao_y):
        self.x = float(x_esquerda)
        self.x_inicial = float(x_esquerda)
        self.x_base = float(x_esquerda)
        self.chao_y = chao_y
        self.vida_barra = config.BATALHA_VIDA_BARRA_DRAGAO
        self.vida_max = self.vida_barra * 3
        self.vida = self.vida_max
        self.eventos = []
        self.reiniciar_comportamento()

    def reiniciar_comportamento(self):
        self.estado = "entrada"
        self.t_estado = 0.0
        self.tempo = 0.0
        self.altura = 0.0
        self.alvo_altura = 0.0
        self.flash = 0.0
        self.x = self.x_inicial
        self.x_base = self.x_inicial
        self.proximo_ataque = 1.5
        self.proximo_voo = random.uniform(12.0, 18.0)
        self.rajadas = []
        self.tiros_feitos = 0
        self.duracao_voo = 7.0
        self.prox_tiro_ar = 1.0
        self.brilho_boca = 0.0
        self.rugiu = False
        self.onda_lancada = False
        self.fase_asas = -1
        self.eventos = []

    # ---------- propriedades ----------
    @property
    def barras(self):
        """Barras de vida restantes (3, 2, 1 ou 0)."""
        return max(0, math.ceil(self.vida / self.vida_barra))

    @property
    def topo(self):
        bob = math.sin(self.tempo * 2.2) * 3
        return self.chao_y - PES * ESC - self.altura + bob

    @property
    def fora_da_tela(self):
        return self.estado == "fugindo" and self.topo < -400

    @property
    def vulneravel(self):
        return self.estado not in ("entrada", "morrendo", "fugindo")

    def caixas(self):
        """(corpo, cabeça): áreas que a espada e a gosma acertam."""
        t, x = self.topo, self.x
        corpo = pygame.Rect(x + CORPO[0] * ESC, t + CORPO[1] * ESC,
                            (CORPO[2] - CORPO[0]) * ESC, (CORPO[3] - CORPO[1]) * ESC)
        cabeca = pygame.Rect(x + CABECA[0] * ESC, t + CABECA[1] * ESC,
                             (CABECA[2] - CABECA[0]) * ESC, (CABECA[3] - CABECA[1]) * ESC)
        return corpo, cabeca

    def caixa_contato(self):
        """Encostar nesta área machuca o herói (um pouco menor que o corpo, para ser justo)."""
        return self.caixas()[0].inflate(-40, -40)

    def centro(self):
        corpo, _ = self.caixas()
        return corpo.center

    def boca(self):
        return (self.x + BOCA[0] * ESC, self.topo + BOCA[1] * ESC)

    # ---------- dano ----------
    def receber_dano(self, dano):
        if not self.vulneravel or self.vida <= 0:
            return False
        barras_antes = self.barras
        self.vida = max(0, self.vida - dano)
        self.flash = 0.12
        self.eventos.append(("dano",))
        if self.vida <= 0:
            self._ir("morrendo")
            self.alvo_altura = 0.0
            self.eventos.append(("morreu",))
        elif self.barras < barras_antes:
            self._ir("atordoado")
            self.alvo_altura = 0.0
            self.rajadas = []
            self.eventos.append(("barra",))
            self.eventos.append(("rugido",))
            self.eventos.append(("tremor", 10, 0.6))
        return True

    def fugir(self):
        """Cutscene final: o dragão derrotado sai voando pela parte de cima da tela."""
        self._ir("fugindo")

    # ---------- lógica ----------
    def _ir(self, estado):
        self.estado = estado
        self.t_estado = 0.0

    def _pausa(self):
        return PAUSA.get(self.barras, 1.2) + random.uniform(0.0, 0.6)

    def atualizar(self, dt, alvo):
        """alvo: posição (x, y) do herói, para mirar o fogo."""
        self.tempo += dt
        self.t_estado += dt
        self.flash = max(0.0, self.flash - dt)
        self.altura += (self.alvo_altura - self.altura) * min(1.0, 4.0 * dt)
        e = self.estado

        if e == "entrada":
            if not self.rugiu and self.t_estado > 0.2:
                self.rugiu = True
                self.eventos += [("rugido",), ("tremor", 8, 0.8)]
            if self.t_estado >= 2.4:
                self._ir("ocioso")

        elif e == "ocioso":
            self.brilho_boca = 0.0
            self.proximo_ataque -= dt
            self.proximo_voo -= dt
            if self.proximo_voo <= 0:
                self._ir("decolando")
                self.alvo_altura = ALTURA_VOO
                self.duracao_voo = random.uniform(6.0, 8.5)
                self.x_base = self.x
                self.eventos.append(("rugido",))   # o bater de asas toca sozinho enquanto ele voa
            elif self.proximo_ataque <= 0:
                if random.random() < 0.4:
                    self._ir("onda")
                    self.onda_lancada = False
                else:
                    self._ir("mirando")

        elif e == "mirando":
            self.brilho_boca = min(1.0, self.t_estado / 0.7)
            if self.t_estado >= 0.7:
                self._ir("cuspindo")
                self.tiros_feitos = 0
                self.rajadas = [0.0, 0.32, 0.64][:TIROS.get(self.barras, 1)]

        elif e == "cuspindo":
            while self.rajadas and self.t_estado >= self.rajadas[0]:
                self.rajadas.pop(0)
                self._atirar(alvo)
            if not self.rajadas and self.t_estado >= 0.9:
                self.brilho_boca = 0.0
                self.proximo_ataque = self._pausa()
                self._ir("ocioso")

        elif e == "onda":
            self.brilho_boca = min(1.0, self.t_estado / 0.6)
            if self.t_estado >= 0.6 and not self.onda_lancada:
                self.onda_lancada = True
                bx, _ = self.boca()
                self.eventos += [("fogo",), ("projetil", OndaDeFogo(bx, self.chao_y))]
            if self.t_estado >= 1.2:
                self.brilho_boca = 0.0
                self.proximo_ataque = self._pausa()
                self._ir("ocioso")

        elif e == "decolando":
            if self.t_estado >= 1.0:
                self._ir("voando")
                self.prox_tiro_ar = 0.6

        elif e == "voando":
            self.x = self.x_base + 70.0 * math.sin(self.t_estado * 0.9)
            self.prox_tiro_ar -= dt
            self.brilho_boca = 0.6 if self.prox_tiro_ar < 0.35 else 0.0
            if self.prox_tiro_ar <= 0:
                self._atirar(alvo)
                self.prox_tiro_ar = INTERVALO_VOO.get(self.barras, 1.0)
            if self.t_estado >= self.duracao_voo:
                self._ir("pousando")
                self.alvo_altura = 0.0
                self.brilho_boca = 0.0

        elif e == "pousando":
            self.x += (self.x_base - self.x) * min(1.0, 3.0 * dt)
            if self.altura < 4.0 and self.t_estado > 0.5:
                self.altura = 0.0
                self.eventos += [("pouso",), ("tremor", 9, 0.5)]
                self.proximo_ataque = 1.4
                self.proximo_voo = random.uniform(14.0, 22.0)
                self._ir("ocioso")

        elif e == "atordoado":
            self.brilho_boca = 0.0
            if self.t_estado >= 1.5:
                self.proximo_ataque = 1.2
                self._ir("ocioso")

        elif e == "fugindo":
            self.x -= 150.0 * dt
            self.alvo_altura = 900.0
            self.altura += 240.0 * dt * (1.0 + self.t_estado)

        # bater de asas: um som a cada 2 trocas de quadro do sprite (~0,44 s) enquanto está no ar
        # e visível. Ao fugir, o volume cai com a distância e para de vez quando sai da tela.
        if e in ("decolando", "voando", "pousando", "fugindo") and self.altura > 12 and self.topo > -260:
            fase = int(self.tempo * 4.5) // 2
            if fase != self.fase_asas:
                self.fase_asas = fase
                volume = 1.0 if e != "fugindo" else max(0.0, min(1.0, (self.topo + 260) / 420.0))
                if volume > 0.05:
                    self.eventos.append(("asas", volume))

    def _atirar(self, alvo):
        bx, by = self.boca()
        velocidade = VEL_FOGO.get(self.barras, 470.0)
        self.eventos += [("fogo",), ("projetil", BolaDeFogo(bx, by, alvo, velocidade))]

    # ---------- desenho ----------
    def _nome_sprite(self):
        voando = self.estado in ("decolando", "voando", "pousando", "fugindo") and self.altura > 12
        if voando:
            return "dragao_voando.png" if int(self.tempo * 4.5) % 2 == 0 else "dragao_chao.png"
        return "dragao_chao.png"

    def desenhar_sombra(self, tela):
        if self.estado == "fugindo" and self.altura > 300:
            return
        fator = max(0.35, 1.0 - self.altura / 380.0)
        w, h = int(430 * fator), int(26 * fator)
        sombra = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (10, 6, 16, int(120 * fator)), (0, 0, w, h))
        tela.blit(sombra, (round(self.x + 235 * ESC - w / 2 + 60), self.chao_y - h // 2 + 4))

    def desenhar(self, tela):
        img = imagem(self._nome_sprite(), ESC)
        pos = (round(self.x), round(self.topo))
        tremer = 3 if self.estado in ("mirando", "onda") else 0
        if tremer:
            pos = (pos[0] + random.randint(-tremer, tremer), pos[1])
        tela.blit(img, pos)
        if self.flash > 0:                       # pisca branco ao levar dano
            brilho = img.copy()
            brilho.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_ADD)
            tela.blit(brilho, pos)
        if self.brilho_boca > 0:                 # luz de fogo na boca antes de cuspir
            bx, by = self.boca()
            for raio, alfa in ((34, 40), (22, 80), (11, 160)):
                r = int(raio * (0.5 + 0.7 * self.brilho_boca))
                halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(halo, (255, 170, 50, alfa), (r, r), r)
                tela.blit(halo, (round(bx) - r, round(by) - r))
