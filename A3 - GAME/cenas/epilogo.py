"""Tela 5 (epílogo): a heroína encontra a princesa no jardim do castelo. Cutscene + mensagem final.

Sequência: a heroína entra andando -> encontro com diálogo -> as duas vão embora juntas ->
mensagem final -> FIM (ENTER volta ao menu).

Tudo o que dá para mudar (textos, posições, velocidades) está nas constantes aqui embaixo.
"""
import math
import os
import random

import pygame

import config
from entidades.jogador import Jogador
from nucleo.camera import Camera
from nucleo.cena import Cena
from sistemas.sons import Sons

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------- textos (mude à vontade) ----------------
LEGENDA_INICIAL = "O dragão foi vencido. No jardim do castelo, alguém esperava..."
DIALOGO = [
    ("Princesa", "Eu sabia que você viria me buscar!"),
    ("Heroína", "Nada me impediria. Vamos para casa."),
    ("Princesa", "Juntas, para sempre."),
]
MENSAGEM_FINAL = [
    "O medo ficou para trás.",
    "E, juntas, as duas voltaram para casa",
    "e viveram felizes para sempre.",
]
TITULO_FIM = "FIM"
SUBTITULO = config.TITULO                      # "Falling in Fears"
AGRADECIMENTO = "Obrigado por jogar!"
CREDITOS = []                                  # ex.: ["Programação: Fulano", "Arte: Ciclano"]
DICA_FIM = "ENTER - voltar ao menu"

# ---------------- cenário (ajuste se a ponte ficar desalinhada) ----------------
CHAO_Y = 362                   # linha dos pés dos personagens (na ponte)
HEROI_X_INICIO = -40
PRINCESA_X = 690
DISTANCIA_ENCONTRO = 62        # distância entre os dois quando se encontram
VEL_ANDAR = 95.0               # px/s do herói
VEL_PARTIDA = 70.0             # px/s quando vão embora juntos
ALTURA_PRINCESA = 72           # px
VELOCIDADE_TEXTO = 38          # letras por segundo no diálogo
PAUSA_FALA = 1.6               # s de espera depois de uma fala terminar de aparecer


class Coracao:
    def __init__(self, x, y):
        self.x = x + random.uniform(-14, 14)
        self.y = y
        self.vx = random.uniform(-10, 10)
        self.vy = random.uniform(-48, -30)
        self.t = 0.0
        self.vida = random.uniform(1.6, 2.4)
        self.tam = random.uniform(5, 9)

    def atualizar(self, dt):
        self.t += dt
        self.x += (self.vx + math.sin(self.t * 4) * 12) * dt
        self.y += self.vy * dt

    def desenhar(self, tela):
        f = max(0.0, 1.0 - self.t / self.vida)
        s = int(self.tam * 2 + 4)
        surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        c = (255, 90, 140, int(240 * f))
        r = self.tam * 0.55
        cx, cy = s, s
        pygame.draw.circle(surf, c, (cx - r * 0.9, cy - r * 0.3), r)
        pygame.draw.circle(surf, c, (cx + r * 0.9, cy - r * 0.3), r)
        pygame.draw.polygon(surf, c, [(cx - r * 1.75, cy - r * 0.1), (cx + r * 1.75, cy - r * 0.1), (cx, cy + r * 1.9)])
        tela.blit(surf, (round(self.x) - s, round(self.y) - s))


class Epilogo(Cena):
    def __init__(self, jogo):
        super().__init__(jogo)
        self.jogo.iniciar_musica_final()
        self.sons = Sons()
        self.timer_passo = 0.0
        self.L, self.A = config.LARGURA, config.ALTURA
        caminho = os.path.join(RAIZ, "assets", "fundo_fase5.jpeg")
        self.fundo = pygame.transform.smoothscale(pygame.image.load(caminho).convert(), (self.L, self.A))

        img = pygame.image.load(os.path.join(RAIZ, "assets", "princesa.png")).convert_alpha()
        h = ALTURA_PRINCESA
        w = max(1, int(img.get_width() * h / img.get_height()))
        self.img_princesa = pygame.transform.smoothscale(img, (w, h))
        self.img_princesa_espelhada = pygame.transform.flip(self.img_princesa, True, False)

        # o herói é o mesmo personagem das fases (só desenhado, sem física)
        self.heroi = Jogador(0, 0)
        self.heroi.no_chao = True
        self.heroi.invencivel = 0.0
        self.heroi.direcao = 1
        self.camera = Camera(self.L, self.A)
        self.heroi_x = float(HEROI_X_INICIO)
        self.princesa_x = float(PRINCESA_X)
        self.princesa_olha_esquerda = True

        self.t = 0.0
        self.estado = "entrada"
        self.t_estado = 0.0
        self.fala = 0
        self.t_fala = 0.0
        self.coracoes = []
        self.prox_coracao = 0.0
        self.fade = 1.0                                   # 1 = preto
        self.vagalumes = [[random.uniform(0, self.L), random.uniform(120, 420), random.uniform(0, math.tau),
                           random.uniform(0.6, 1.6)] for _ in range(34)]
        self.fontes = {}

    # ---------------- utilidades ----------------
    def _fonte(self, tam, negrito=False):
        chave = (tam, negrito)
        if chave not in self.fontes:
            nome = "Cinzel-Bold.ttf" if negrito else "Cinzel-SemiBold.ttf"
            try:
                self.fontes[chave] = pygame.font.Font(os.path.join(RAIZ, "assets", "fontes", nome), tam)
            except (pygame.error, OSError):
                self.fontes[chave] = pygame.font.Font(None, int(tam * 1.3))
        return self.fontes[chave]

    def _ir(self, estado):
        self.estado = estado
        self.t_estado = 0.0

    def _texto(self, tela, txt, tam, cor, centro, negrito=False, alfa=255):
        f = self._fonte(tam, negrito)
        sombra = f.render(txt, True, (0, 0, 0))
        img = f.render(txt, True, cor)
        if alfa < 255:
            sombra.set_alpha(int(alfa * 0.7))
            img.set_alpha(alfa)
        r = img.get_rect(center=centro)
        tela.blit(sombra, r.move(2, 2))
        tela.blit(img, r)

    # ---------------- eventos ----------------
    def eventos(self, eventos):
        for e in eventos:
            if e.type != pygame.KEYDOWN:
                continue
            if self.estado == "fim":
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                    from cenas.game_over import GameOver
                    self.jogo.trocar_cena(GameOver(self.jogo, 4, vitoria=True))
            elif e.key == pygame.K_ESCAPE:
                self._ir("fim")                              # pula a cutscene
            elif self.estado == "encontro" and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self._proxima_fala()

    def _proxima_fala(self):
        self.fala += 1
        self.t_fala = 0.0
        if self.fala >= len(DIALOGO):
            self._ir("partida")

    # ---------------- lógica ----------------
    def atualizar(self, dt):
        self.t += dt
        self.t_estado += dt
        self.heroi.anim_t += dt
        for v in self.vagalumes:
            v[2] += dt * v[3]
        self.coracoes = [c for c in self.coracoes if c.t < c.vida]
        for c in self.coracoes:
            c.atualizar(dt)

        e = self.estado
        self.heroi.vel.x = 0
        if e == "entrada":
            self.fade = max(0.0, 1.0 - self.t_estado / 1.2)
            self._andar_heroi(dt, VEL_ANDAR)
            if self.t_estado >= 1.2:
                self._ir("andando")

        elif e == "andando":
            self._andar_heroi(dt, VEL_ANDAR)
            if self.heroi_x >= self.princesa_x - DISTANCIA_ENCONTRO:
                self.heroi_x = self.princesa_x - DISTANCIA_ENCONTRO
                self._ir("encontro")

        elif e == "encontro":
            self.t_fala += dt
            self._soltar_coracoes(dt, 0.45)
            fala = DIALOGO[min(self.fala, len(DIALOGO) - 1)][1]
            if self.t_fala >= len(fala) / VELOCIDADE_TEXTO + PAUSA_FALA:
                self._proxima_fala()

        elif e == "partida":
            self.princesa_olha_esquerda = False
            self._soltar_coracoes(dt, 0.3)
            self.heroi.direcao = 1
            if self.t_estado > 0.8:                           # os dois andam juntos para a direita
                self.heroi.vel.x = VEL_PARTIDA
                self.heroi_x += VEL_PARTIDA * dt
                self.princesa_x += VEL_PARTIDA * dt
                self._atualizar_passo(dt)
            if self.t_estado > 3.2:
                self.fade = min(1.0, (self.t_estado - 3.2) / 1.2)
            if self.t_estado >= 4.4:
                self._ir("fim")

        elif e == "fim":
            self.fade = 1.0
            if self.t_estado >= 8.0:
                from cenas.game_over import GameOver
                self.jogo.trocar_cena(GameOver(self.jogo, 4, vitoria=True))

    def _andar_heroi(self, dt, vel):
        self.heroi.direcao = 1
        self.heroi.vel.x = vel
        self.heroi_x += vel * dt
        self._atualizar_passo(dt)

    def _atualizar_passo(self, dt):
        self.timer_passo -= dt
        if self.timer_passo <= 0:
            self.timer_passo = 0.34
            self.sons.tocar("passo")

    def _soltar_coracoes(self, dt, intervalo):
        self.prox_coracao -= dt
        if self.prox_coracao <= 0:
            self.prox_coracao = intervalo
            meio = (self.heroi_x + self.princesa_x) / 2
            self.coracoes.append(Coracao(meio, CHAO_Y - 78))

    # ---------------- desenho ----------------
    def _desenhar_vagalumes(self, tela):
        for x, y, f, v in self.vagalumes:
            px = x + math.sin(f * 1.3) * 22
            py = y + math.sin(f) * 14
            brilho = 0.5 + 0.5 * math.sin(f * 3.1)
            r = 3
            halo = pygame.Surface((r * 8, r * 8), pygame.SRCALPHA)
            pygame.draw.circle(halo, (255, 230, 120, int(70 * brilho)), (r * 4, r * 4), r * 4)
            pygame.draw.circle(halo, (255, 245, 190, int(230 * brilho)), (r * 4, r * 4), r)
            tela.blit(halo, (round(px) - r * 4, round(py) - r * 4))

    def _desenhar_personagens(self, tela):
        # princesa (balança de leve, como se respirasse)
        img = self.img_princesa if self.princesa_olha_esquerda else self.img_princesa_espelhada
        bob = int(math.sin(self.t * 2.4) * 1.5)
        tela.blit(img, img.get_rect(midbottom=(round(self.princesa_x), CHAO_Y + 2 + bob)))
        # herói
        self.heroi.rect.midbottom = (round(self.heroi_x), CHAO_Y)
        self.heroi.pos.update(self.heroi.rect.topleft)
        self.heroi.desenhar(tela, self.camera)

    def _desenhar_dialogo(self, tela):
        if self.estado != "encontro" and not (self.estado == "entrada" or self.estado == "andando"):
            return
        largura, altura = 860, 84
        x, y = (self.L - largura) // 2, self.A - altura - 22
        painel = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.rect(painel, (27, 20, 42, 225), (0, 0, largura, altura), border_radius=12)
        pygame.draw.rect(painel, (190, 150, 91, 240), (0, 0, largura, altura), 2, border_radius=12)
        pygame.draw.rect(painel, (100, 76, 112, 190), (6, 6, largura - 12, altura - 12), 1, border_radius=8)
        tela.blit(painel, (x, y))
        if self.estado == "encontro":
            quem, fala = DIALOGO[min(self.fala, len(DIALOGO) - 1)]
            visiveis = int(self.t_fala * VELOCIDADE_TEXTO)
            fn = self._fonte(16, True)
            tela.blit(fn.render(quem.upper(), True, (244, 215, 164)), (x + 24, y + 12))
            tela.blit(self._fonte(22).render(fala[:visiveis], True, (240, 236, 245)), (x + 24, y + 38))
            if visiveis >= len(fala):
                tela.blit(self._fonte(13).render("ENTER ▶", True, (190, 150, 91)), (x + largura - 90, y + altura - 24))
        else:
            tela.blit(self._fonte(20).render(LEGENDA_INICIAL, True, (240, 236, 245)), (x + 24, y + 30))

    def _desenhar_fim(self, tela):
        tela.fill((6, 4, 12))
        t = self.t_estado
        linhas = MENSAGEM_FINAL
        y = self.A // 2 - 120
        for i, linha in enumerate(linhas):
            alfa = int(255 * max(0.0, min(1.0, (t - 0.8 - i * 1.4) / 1.0)))
            if alfa:
                self._texto(tela, linha, 28, (244, 215, 164), (self.L // 2, y + i * 42), alfa=alfa)
        inicio_fim = 0.8 + len(linhas) * 1.4 + 0.4
        a_fim = int(255 * max(0.0, min(1.0, (t - inicio_fim) / 1.2)))
        if a_fim:
            self._texto(tela, TITULO_FIM, 84, (230, 170, 64), (self.L // 2, self.A // 2 + 50), negrito=True, alfa=a_fim)
            self._texto(tela, SUBTITULO, 22, (200, 185, 215), (self.L // 2, self.A // 2 + 112), alfa=a_fim)
        a_fim2 = int(255 * max(0.0, min(1.0, (t - inicio_fim - 1.6) / 1.0)))
        if a_fim2:
            self._texto(tela, AGRADECIMENTO, 20, (240, 236, 245), (self.L // 2, self.A // 2 + 146), alfa=a_fim2)
            for i, c in enumerate(CREDITOS):
                self._texto(tela, c, 16, (200, 185, 215), (self.L // 2, self.A // 2 + 176 + i * 22), alfa=a_fim2)
            if int(self.t * 1.6) % 2 == 0:
                self._texto(tela, DICA_FIM, 15, (190, 150, 91), (self.L // 2, self.A - 28), alfa=a_fim2)

    def desenhar(self, tela):
        if self.estado == "fim":
            self._desenhar_fim(tela)
            return
        tela.blit(self.fundo, (0, 0))
        self._desenhar_vagalumes(tela)
        self._desenhar_personagens(tela)
        for c in self.coracoes:
            c.desenhar(tela)
        self._desenhar_dialogo(tela)
        if self.fade > 0:
            veu = pygame.Surface((self.L, self.A))
            veu.set_alpha(int(255 * min(1.0, self.fade)))
            tela.blit(veu, (0, 0))
