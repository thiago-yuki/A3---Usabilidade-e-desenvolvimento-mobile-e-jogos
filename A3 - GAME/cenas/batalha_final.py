"""Batalha final contra o dragão (tela estática) + cutscene do final.

Tudo é desenhado numa tela lógica de 1280x720 e depois ajustado ao tamanho da janela,
então funciona em HD (1280x720) e em Full HD (1920x1080) sem mudar nada aqui.

Teclas:  A/D andar | ESPAÇO pular | E espada | Q gosma | K/SHIFT avançar | ESC pausa
"""
import math
import random

import pygame

import config
from entidades.dragao import Dragao
from entidades.heroi_batalha import HeroiBatalha
from entidades.plataforma import Plataforma
from entidades.projeteis import BolaDeFogo, Gosma, OndaDeFogo
from nucleo.cena import Cena
from sistemas import cenario as C
from sistemas.audio import Audio
from sistemas.hud_batalha import HudBatalha
from sistemas.recursos import imagem, texto

LARG, ALT = C.LARGURA, C.ALTURA
CHAO = C.CHAO_Y
PAREDE_X = 1040              # parede invisível: o herói não passa para o castelo antes da hora
DRAGAO_X = 645               # canto esquerdo do sprite do dragão (corpo ~ x 880, na frente da porta)

ESC_CAVALO = 0.85
ESC_PRINCESA = 0.72
CAVALO_PES = 242             # linha dos cascos no sprite do cavalo (340x256)

# ---- Textos de orientação (mude aqui o que aparece na tela) ----
# ---- Noite: depois de resgatar a princesa o pôr do sol vira noite ----
NOITE_COMECA_EM = ("cs_cavalo", "cs_cavalgar", "fim_fade", "fim")   # estados da cutscene em que anoitece
NOITE_DURACAO = 7.0            # segundos para o céu virar noite por completo

DICA_INICIAL = "A/D andar   ESPAÇO pular   E espada   Q gosma   K avançar   ESC pausar"
DICA_TAMANHO = 24                       # tamanho da letra da dica
DICA_COR = (240, 236, 245)
DICA_POS_Y = ALT - 28                   # altura da dica (ALT - 28 = rente à borda de baixo)
DICA_SEGUNDOS = 9.0                     # por quanto tempo a dica fica na tela
TECLAS_PAUSA = [                        # lista mostrada no menu de pausa
    ("A / D", "andar"), ("ESPAÇO", "pular (2x no ar)"), ("E", "espada"),
    ("Q", "gosma (em linha reta)"), ("K / SHIFT", "avançar"), ("ESC", "continuar"),
]


class BatalhaFinal(Cena):
    def __init__(self, jogo):
        super().__init__(jogo)
        if not hasattr(jogo, "audio"):
            jogo.audio = Audio()
        self.audio = jogo.audio
        self.audio.pre_carregar(["espada", "gosma", "dano_heroi", "dano_dragao", "fogo", "rugido",
                                 "impacto_fogo", "pulo", "asas", "derrota"])
        self.canvas = pygame.Surface((LARG, ALT))
        self.mundo = pygame.Surface((LARG, ALT))
        self.hud = HudBatalha()
        self.tentativa = 1
        self.max_tentativas = config.BATALHA_TENTATIVAS
        self.dragao = None
        self.fade = 1.0                       # 1 = preto total (abre no começo)
        self.pausado = False
        self._nova_tentativa()

    # ================================================================ preparo
    def _nova_tentativa(self):
        self.solidos = [Plataforma(-300, CHAO, LARG + 600, 300),
                        Plataforma(PAREDE_X, -600, 400, 1400)]
        self.heroi = HeroiBatalha(120, CHAO - HeroiBatalha.ALTURA)
        for habilidade in self.jogo.habilidades:
            self.heroi.desbloquear(habilidade)
        if self.dragao is None:
            self.dragao = Dragao(DRAGAO_X, CHAO)
        elif config.BATALHA_RESETAR_DRAGAO:
            self.dragao.vida = self.dragao.vida_max
            self.dragao.reiniciar_comportamento()
        else:
            self.dragao.reiniciar_comportamento()
        self.hud.vida_visual = float(self.dragao.vida)
        self.bolas, self.ondas, self.gosmas, self.particulas = [], [], [], []
        self.tempo = 0.0
        self.tremor_forca = 0.0
        self.tremor_t = 0.0
        self.tremor_dur = 1.0
        self.flash_cor = (255, 255, 255)
        self.flash_t = 0.0
        self.flash_dur = 0.3
        self.porta_aberta = False
        self.luzes = 0
        self.noite = 0.0                       # 0 = pôr do sol, 1 = noite
        self.estado = "intro"
        self.t_estado = 0.0
        self.fade = 1.0
        self.audio.musica("musica_boss")

    def _ir(self, estado):
        self.estado = estado
        self.t_estado = 0.0
        self.cs_passo_t = 0.0                   # cada cena de cutscene começa com o timer de passos zerado

    # ================================================================ eventos
    def eventos(self, eventos):
        for e in eventos:
            if e.type != pygame.KEYDOWN:
                continue
            if e.key == pygame.K_ESCAPE:
                self._alternar_pausa()
                return
            if self.pausado:
                if e.key == pygame.K_RETURN:
                    self._sair_do_jogo()
                continue
            if self.estado in ("intro", "luta"):
                self._tecla_luta(e.key)
            elif e.key == pygame.K_RETURN:
                if self.estado == "derrota" and self.t_estado > 1.6:
                    self._continuar_apos_derrota()
                elif self.estado == "fim" and self.t_estado > 1.0:
                    self._sair_do_jogo()

    def _tecla_luta(self, tecla):
        h = self.heroi
        if tecla in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
            if h.pulos_restantes > 0:
                self.audio.tocar("pulo", 0.5)
            h.pular()
        elif tecla == pygame.K_e:
            if h.tempo_recarga <= 0:
                self.audio.tocar("espada")
            h.atacar()
        elif tecla in (pygame.K_k, pygame.K_LSHIFT, pygame.K_RSHIFT):
            h.avancar()
        elif tecla == pygame.K_q:
            if h.pode_atirar():
                x, y = h.boca_gosma
                self.gosmas.append(Gosma(x, y, h.direcao))   # sai em linha reta, para onde o herói olha
                h.atirar()
                self.audio.tocar("gosma")

    def _silenciar(self):
        """Corta todos os efeitos que ainda estiverem tocando (evita som 'preso' entre as cenas)."""
        if self.audio.ativo:
            try:
                pygame.mixer.stop()
            except pygame.error:
                pass

    def _alternar_pausa(self):
        self.pausado = not self.pausado
        if self.audio.ativo:
            try:
                if self.pausado:
                    pygame.mixer.pause()
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.unpause()
                    pygame.mixer.music.unpause()
            except pygame.error:
                pass

    def _sair_do_jogo(self):
        self.audio.parar_musica()
        self.jogo.sair()

    def _continuar_apos_derrota(self):
        if self.tentativa < self.max_tentativas:
            self.tentativa += 1
            self._nova_tentativa()
        else:
            self._recomecar_jogo()

    def _recomecar_jogo(self):
        """Perdeu todas as tentativas: refaz tudo do zero.
        Aqui só existe a batalha, então ela recomeça na tentativa 1. Quando as outras fases
        forem integradas, troque o corpo deste método por: voltar para a Fase 1
        (jogo.habilidades.clear() e jogo.trocar_cena(Fase(jogo, 1)))."""
        self.audio.parar_musica()
        self.tentativa = 1
        self.dragao.vida = self.dragao.vida_max
        self._nova_tentativa()

    # ================================================================ efeitos
    def _tremer(self, forca, duracao):
        if forca >= self.tremor_forca * (self.tremor_t / max(self.tremor_dur, 0.01)):
            self.tremor_forca, self.tremor_t, self.tremor_dur = forca, duracao, duracao

    def _piscar(self, cor, duracao):
        self.flash_cor, self.flash_t, self.flash_dur = cor, duracao, duracao

    def _faiscas(self, x, y, cor, n=10, vel=260.0, grav=700.0, vida=0.45):
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            v = random.uniform(0.3, 1.0) * vel
            self.particulas.append([x, y, math.cos(ang) * v, math.sin(ang) * v - 60,
                                    random.uniform(0.6, 1.0) * vida, vida, cor, random.randint(2, 5), grav])

    def _atualizar_particulas(self, dt):
        for p in self.particulas:
            p[2] *= 1.0 - min(1.0, 1.5 * dt)
            p[3] += p[8] * dt
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
        self.particulas = [p for p in self.particulas if p[4] > 0]

    # ================================================================ lógica
    def atualizar(self, dt):
        if self.pausado:
            return
        self.t_estado += dt
        self.tempo += dt
        if self.estado in NOITE_COMECA_EM:
            self.noite = min(1.0, self.noite + dt / NOITE_DURACAO)
        self.fade = max(0.0, self.fade - dt / 0.6) if self.estado != "fim_fade" else self.fade
        self.tremor_t = max(0.0, self.tremor_t - dt)
        self.flash_t = max(0.0, self.flash_t - dt)
        self._atualizar_particulas(dt)
        self.hud.atualizar(dt, self.dragao)

        e = self.estado
        if e in ("intro", "luta"):
            self._atualizar_luta(dt)
            if e == "intro" and self.t_estado >= 2.6:
                self._ir("luta")
        elif e == "derrota":
            pass
        elif e.startswith("cs_") or e == "fim_fade":
            self._atualizar_cutscene(dt)

    def _atualizar_luta(self, dt):
        h, d = self.heroi, self.dragao
        h.atualizar(dt, self.solidos, LARG)
        d.atualizar(dt, h.rect.center)
        corpo, cabeca = d.caixas()

        # espada acerta o dragão (1 vez por golpe)
        area = h.hitbox_ataque
        if area and id(d) not in h.alvos_acertados and (area.colliderect(corpo) or area.colliderect(cabeca)):
            if d.receber_dano(config.BATALHA_DANO_ESPADA):
                h.alvos_acertados.add(id(d))
                self.audio.tocar("dano_dragao")
                self._faiscas(area.centerx + h.direcao * 20, area.centery, (255, 226, 120), 12)
                self._tremer(3, 0.1)

        # encostar no dragão machuca
        if d.vulneravel and h.rect.colliderect(d.caixa_contato()):
            self._dano_heroi(d.caixa_contato().centerx)

        # gosma
        for g in self.gosmas:
            g.atualizar(dt, CHAO, LARG)
            if g.vivo and (g.rect.colliderect(corpo) or g.rect.colliderect(cabeca)):
                g.vivo = False
                if d.receber_dano(config.BATALHA_DANO_GOSMA):
                    self.audio.tocar("dano_dragao")
                self._faiscas(g.pos.x, g.pos.y, (130, 230, 100), 14, 240)
                self._tremer(3, 0.1)
            elif not g.vivo:
                self._faiscas(g.pos.x, min(g.pos.y, CHAO - 4), (130, 230, 100), 5, 150)
        self.gosmas = [g for g in self.gosmas if g.vivo]

        # fogo do dragão
        for b in self.bolas:
            b.atualizar(dt, CHAO, LARG)
            if b.vivo and b.rect.colliderect(h.rect):
                if self._dano_heroi(b.pos.x):
                    b.vivo = False
                    self._faiscas(b.pos.x, b.pos.y, (255, 170, 60), 12)
            if b.bateu_chao:
                self._faiscas(b.pos.x, CHAO - 6, (255, 150, 50), 10, 200)
                self.audio.tocar("impacto_fogo", 0.35)
        self.bolas = [b for b in self.bolas if b.vivo]
        for o in self.ondas:
            o.atualizar(dt)
            if o.vivo and o.rect.colliderect(h.rect) and self._dano_heroi(o.x + o.LARGURA / 2):
                o.vivo = False
                self._faiscas(h.rect.centerx, h.rect.bottom - 20, (255, 160, 50), 14)
        self.ondas = [o for o in self.ondas if o.vivo]

        self._processar_eventos_dragao()

        if h.vida <= 0 and self.estado == "luta":
            h.invencivel = 0.0
            self.audio.parar_musica()
            self.audio.tocar("derrota")
            self._ir("derrota")

    def _dano_heroi(self, origem_x):
        h = self.heroi
        if h.receber_dano(1, origem_x):
            self.audio.tocar("dano_heroi")
            self._tremer(7, 0.25)
            self._piscar((255, 40, 40), 0.18)
            self._faiscas(h.rect.centerx, h.rect.centery, (255, 90, 80), 10, 220)
            return True
        return False

    def _processar_eventos_dragao(self):
        d = self.dragao
        for ev in d.eventos:
            tipo = ev[0]
            if tipo == "rugido":
                self.audio.tocar("rugido")
            elif tipo == "projetil":
                (self.ondas if isinstance(ev[1], OndaDeFogo) else self.bolas).append(ev[1])
            elif tipo == "tremor":
                self._tremer(ev[1], ev[2])
            elif tipo == "fogo":
                self.audio.tocar("fogo", 0.8)
            elif tipo == "asas":
                self.audio.tocar("asas", ev[1] if len(ev) > 1 else 1.0)
            elif tipo == "pouso":
                self.audio.tocar("impacto_fogo")
            elif tipo == "barra":
                self._piscar((255, 255, 255), 0.35)
                cx, cy = d.centro()
                self._faiscas(cx, cy, (255, 230, 140), 40, 420, 500, 0.9)
            elif tipo == "morreu":
                self.bolas, self.ondas, self.gosmas = [], [], []
                self._piscar((255, 255, 255), 0.6)
                cx, cy = d.centro()
                self._faiscas(cx, cy, (255, 220, 120), 60, 520, 400, 1.1)
                self.audio.parar_musica()
                self.audio.tocar("rugido")
                self._tremer(12, 1.2)
                self._preparar_cutscene()
        d.eventos.clear()

    # ================================================================ cutscene
    def _preparar_cutscene(self):
        h = self.heroi
        h.rect.bottom = CHAO
        h.pos.update(h.rect.topleft)
        h.vel.update(0, 0)
        h.no_chao = True
        h.invencivel = 0.0
        h.tempo_ataque = 0.0
        h.direcao = 1
        self.cs_alfa_heroi = 255
        self.cs_alfa_princesa = 0
        self.cs_ultima_luz = 0
        self.cs_passo_t = 0.0
        self.cav_x = -240.0
        self.cav_espelhar = False
        self.cav_vel = 0.0
        self.cav_chegou = False
        self.princesa_x = 0.0
        self.cs_fade = 0.0
        self._ir("cs_dragao")

    def _atualizar_cutscene(self, dt):
        e, t = self.estado, self.t_estado
        h, d = self.heroi, self.dragao
        d.atualizar(dt, h.rect.center)
        for ev in d.eventos:                           # o dragão ferido bate as asas ao fugir (some com a distância)
            if ev[0] == "asas":
                self.audio.tocar("asas", ev[1] if len(ev) > 1 else 1.0)
        d.eventos.clear()
        h.tempo_anim += dt

        if e == "cs_dragao":
            if d.estado == "morrendo" and t >= 1.6:
                d.fugir()
                self._tremer(6, 0.6)
            if d.estado == "fugindo" and (d.fora_da_tela or t > 6.0):
                self.porta_aberta = True
                self._silenciar()                       # o dragão já foi embora: nada de asas
                self.audio.tocar("porta")
                self._ir("cs_porta")

        elif e == "cs_porta":
            alvo = C.PORTA_CENTRO_X
            if h.rect.centerx < alvo:
                h.rect.centerx = min(alvo, h.rect.centerx + round(230 * dt))
                h.vel.x = 230
                self.cs_passo_t -= dt
                if self.cs_passo_t <= 0 and t > 0.5:      # passos só enquanto ele anda
                    self.cs_passo_t = 0.3
                    self.audio.tocar("passo", 0.4)
            else:
                h.vel.x = 0
                self.cs_alfa_heroi = max(0, self.cs_alfa_heroi - round(255 * dt / 0.7))
                if self.cs_alfa_heroi <= 0:
                    self._ir("cs_subindo")

        elif e == "cs_subindo":
            self.luzes = min(len(C.JANELAS_TORRE), int(t / 0.8) + 1)
            if self.luzes != self.cs_ultima_luz:
                self.cs_ultima_luz = self.luzes
                self.audio.tocar("passo")
                self.audio.tocar("luz", 0.6)
            if t >= 0.8 * len(C.JANELAS_TORRE) + 0.6:
                self._piscar((255, 230, 160), 0.4)
                self.audio.tocar("vitoria")
                self._ir("cs_princesa")

        elif e == "cs_princesa":
            if t >= 3.2:
                h.rect.centerx = C.PORTA_CENTRO_X
                h.direcao = 1
                self.cs_alfa_heroi = 0
                self.princesa_x = C.PORTA_CENTRO_X + 40
                self.cs_alfa_princesa = 0
                self._ir("cs_cavalo")

        elif e == "cs_cavalo":
            self.cs_alfa_heroi = min(255, self.cs_alfa_heroi + round(255 * dt / 0.5))
            self.cs_alfa_princesa = self.cs_alfa_heroi
            if not self.cav_chegou:
                if t > 0.6:
                    self.cs_passo_t -= dt
                    if self.cs_passo_t <= 0:
                        self.cs_passo_t = 0.19
                        self.audio.tocar("galope", 0.6)
                    self.cav_x += 560 * dt
                    if self.cav_x >= 640:
                        self.cav_x = 640.0
                        self.cav_chegou = True
                        self.audio.tocar("relincho")
                        self._ir("cs_cavalo")  # reinicia t_estado para a caminhada
                        self.cs_alfa_heroi = self.cs_alfa_princesa = 255
            else:
                if t > 0.9:
                    h.direcao = -1
                    alvo = self.cav_x + 30
                    if h.rect.centerx > alvo:
                        h.rect.centerx -= round(210 * dt)
                        h.vel.x = -210
                        self.princesa_x = h.rect.centerx + 52
                        self.cs_passo_t -= dt
                        if self.cs_passo_t <= 0:
                            self.cs_passo_t = 0.3
                            self.audio.tocar("passo", 0.4)
                    else:
                        h.vel.x = 0
                        self.cav_espelhar = True
                        self.audio.tocar("relincho")
                        self._ir("cs_cavalgar")

        elif e == "cs_cavalgar":
            self.cav_vel = min(760.0, 90.0 + 520.0 * t)
            self.cav_x -= self.cav_vel * dt
            self.cs_passo_t -= dt
            if self.cs_passo_t <= 0:
                self.cs_passo_t = 0.18
                self.audio.tocar("galope", max(0.1, min(0.7, 0.7 - (640 - self.cav_x) / 1200.0)))
            if self.cav_x < -300:
                self._silenciar()
                self._ir("fim_fade")

        elif e == "fim_fade":
            self.cs_fade = min(1.0, t / 1.2)
            if t >= 1.4:
                self._ir("fim")

    # ================================================================ desenho
    def desenhar(self, tela):
        m = self.mundo
        m.blit(imagem("fundo_batalha.png"), (0, 0))
        self._desenhar_noite(m)
        self._desenhar_cenario(m)
        self._desenhar_atores(m)
        self._tingir_noite(m)
        for p in self.particulas:
            pygame.draw.circle(m, p[6], (round(p[0]), round(p[1])), p[7])

        c = self.canvas
        c.fill((0, 0, 0))
        ox = oy = 0
        if self.tremor_t > 0 and not self.pausado:
            forca = self.tremor_forca * (self.tremor_t / max(self.tremor_dur, 0.01))
            ox, oy = random.randint(-int(forca), int(forca)), random.randint(-int(forca), int(forca))
        c.blit(m, (ox, oy))
        if self.flash_t > 0:
            sobre = pygame.Surface((LARG, ALT))
            sobre.fill(self.flash_cor)
            sobre.set_alpha(int(190 * self.flash_t / max(self.flash_dur, 0.01)))
            c.blit(sobre, (0, 0))

        if self.estado in ("intro", "luta", "derrota"):
            self.hud.desenhar(c, self.heroi, self.dragao, self.tentativa, self.max_tentativas)
        self._desenhar_textos(c)

        if self.estado in ("fim_fade", "fim") or self.fade > 0:
            nivel = 1.0 if self.estado == "fim" else (self.cs_fade if self.estado == "fim_fade" else self.fade)
            if nivel > 0:
                preto = pygame.Surface((LARG, ALT))
                preto.set_alpha(int(255 * nivel))
                c.blit(preto, (0, 0))
        if self.estado == "fim":
            self._desenhar_fim(c)

        if self.pausado:
            self._desenhar_pausa(c)

        if tela.get_size() == (LARG, ALT):
            tela.blit(c, (0, 0))
        else:
            tela.blit(pygame.transform.smoothscale(c, tela.get_size()), (0, 0))

    # ----- noite
    def _desenhar_noite(self, m):
        """Mistura aos poucos o céu da noite (fundo_noite.png) por cima do pôr do sol."""
        if self.noite <= 0:
            return
        suave = self.noite * self.noite * (3 - 2 * self.noite)      # começa e termina devagar
        try:
            ceu = imagem("fundo_noite.png")
        except (pygame.error, OSError):
            ceu = None                                              # sem a imagem: só escurece
        if ceu is not None:
            ceu.set_alpha(int(255 * suave))
            m.blit(ceu, (0, 0))

    def _tingir_noite(self, m):
        """Luz azulada da lua sobre personagens e castelo (e escurece se faltar fundo_noite.png)."""
        if self.noite <= 0:
            return
        suave = self.noite * self.noite * (3 - 2 * self.noite)
        tom = pygame.Surface((LARG, ALT))
        tom.fill((255 - int(75 * suave), 255 - int(62 * suave), 255 - int(20 * suave)))
        m.blit(tom, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    # ----- cenário
    def _janela_acesa(self, m, cx, cy, w, h, forca=1.0):
        halo = pygame.Surface((w + 70, h + 70), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (255, 190, 90, int(70 * forca)), halo.get_rect())
        m.blit(halo, (cx - (w + 70) // 2, cy - (h + 70) // 2))
        vidro = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(vidro, (255, 226, 150, int(255 * forca)), (0, 0, w, w))
        pygame.draw.rect(vidro, (255, 226, 150, int(255 * forca)), (0, w // 2, w, h - w // 2))
        m.blit(vidro, (cx - w // 2, cy - h // 2))

    def _desenhar_cenario(self, m):
        for tx, ty in C.TOCHAS:  # tochas tremeluzindo
            r = 9 + random.randint(0, 3)
            halo = pygame.Surface((90, 90), pygame.SRCALPHA)
            pygame.draw.circle(halo, (255, 150, 50, int(45 + 70 * self.noite)), (45, 45), 40)
            m.blit(halo, (tx - 45, ty - 40))
            pygame.draw.ellipse(m, (255, 130, 30), (tx - r // 2 - 2, ty - r - 6, r + 4, r + 12))
            pygame.draw.ellipse(m, (255, 226, 120), (tx - r // 3, ty - r // 2 - 2, r * 2 // 3 + 2, r + 2))
        if not self.porta_aberta:
            m.blit(imagem("porta.png"), (C.PORTA[0], C.PORTA[1]))

        # janelas da torre acesas durante a subida do herói
        if self.estado in ("cs_subindo", "cs_princesa", "cs_cavalo", "cs_cavalgar", "fim_fade", "fim"):
            for cx, cy, w, h in C.JANELAS_TORRE[:self.luzes]:
                self._janela_acesa(m, cx, cy, w, h)

        # janela da princesa (sempre acesa, com ela dentro)
        cx, cy, w, h = C.JANELA_PRINCESA
        self._janela_acesa(m, cx, cy, w, h, 0.9)
        balanco = round(math.sin(self.tempo * 1.6) * 1.5)
        pe_sacada = cy + h // 2 + 2          # chão da sacada
        if self.estado == "cs_princesa":     # herói e princesa juntos na sacada
            m.blit(imagem("princesa.png", 0.40), (cx - 40, pe_sacada - round(176 * 0.40)))
            m.blit(imagem("heroi_parado.png", 0.30), (cx + 22 - round(88 * 0.30), pe_sacada - round(234 * 0.30)))
        else:
            m.blit(imagem("princesa.png", 0.40), (cx - 22, pe_sacada - round(176 * 0.40) + balanco))

    # ----- personagens
    def _sombra(self, m, cx, largura, alfa=90):
        s = pygame.Surface((largura, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (10, 6, 16, alfa), s.get_rect())
        m.blit(s, (round(cx - largura / 2), CHAO - 6))

    def _desenhar_atores(self, m):
        e = self.estado
        h, d = self.heroi, self.dragao
        if e in ("intro", "luta", "derrota", "cs_dragao", "cs_porta", "cs_cavalo"):
            self._sombra(m, h.rect.centerx, 90)
        if d.estado != "fugindo" or not d.fora_da_tela:
            d.desenhar_sombra(m)
            d.desenhar(m)

        if e in ("intro", "luta", "derrota", "cs_dragao"):
            h.desenhar(m)
        elif e == "cs_porta":
            h.desenhar(m, alfa=self.cs_alfa_heroi)
        elif e == "cs_cavalo":
            self._desenhar_cavalo(m, self.cav_x, False, False)
            self._desenhar_princesa(m, self.princesa_x, self.cs_alfa_princesa)
            h.desenhar(m, alfa=self.cs_alfa_heroi)
        elif e in ("cs_cavalgar", "fim_fade"):
            self._desenhar_cavalo(m, self.cav_x, self.cav_espelhar, True)

        for o in self.ondas:
            o.desenhar(m)
        for b in self.bolas:
            b.desenhar(m)
        for g in self.gosmas:
            g.desenhar(m)

    def _desenhar_princesa(self, m, x_centro, alfa=255):
        img = imagem("princesa.png", ESC_PRINCESA, self.heroi.direcao == -1)
        if alfa < 255:
            img = img.copy()
            img.set_alpha(alfa)
        m.blit(img, (round(x_centro - img.get_width() / 2), CHAO - round(176 * ESC_PRINCESA)))

    def _desenhar_cavalo(self, m, cx, espelhar, com_cavaleiros):
        img = imagem("cavalo.png", ESC_CAVALO, espelhar)
        correndo = self.estado in ("cs_cavalgar", "fim_fade") or (self.estado == "cs_cavalo" and not self.cav_chegou and self.t_estado > 0.6)
        bob = round(abs(math.sin(self.tempo * 14)) * 7) if correndo else 0
        topo = CHAO - round(CAVALO_PES * ESC_CAVALO) - bob
        self._sombra(m, cx, 220, 80)
        m.blit(img, (round(cx - img.get_width() / 2), topo))
        if not com_cavaleiros:
            return
        sinal = -1 if espelhar else 1
        sela_y = topo + round(72 * ESC_CAVALO)
        sela_x = cx + sinal * round(-20 * ESC_CAVALO)
        # princesa (atrás) e herói (na frente)
        prin = imagem("princesa.png", 0.5, espelhar)
        m.blit(prin, (round(sela_x - sinal * 30 - prin.get_width() / 2), sela_y + 8 - round(176 * 0.5)))
        her = imagem("heroi_parado.png", 0.40, espelhar)
        ax = (240 - 88) if espelhar else 88
        m.blit(her, (round(sela_x + sinal * 12 - ax * 0.40), sela_y + 14 - round(234 * 0.40)))

    # ----- textos
    def _alfa_pulso(self, t, entrada=0.5, total=2.6, saida=0.6):
        if t < entrada:
            return t / entrada
        if t > total - saida:
            return max(0.0, (total - t) / saida)
        return 1.0

    def _desenhar_textos(self, c):
        e, t = self.estado, self.t_estado
        if e == "intro":
            a = int(255 * self._alfa_pulso(t))
            texto(c, "BATALHA FINAL", 88, (255, 214, 120), (LARG // 2, 300), alfa=a)
            texto(c, "Derrote o dragão e resgate a princesa!", 34, (245, 240, 250), (LARG // 2, 372), alfa=a)
        elif e == "luta" and t < DICA_SEGUNDOS:
            a = int(255 * min(1.0, (DICA_SEGUNDOS - t) / 1.5))
            texto(c, DICA_INICIAL, DICA_TAMANHO, DICA_COR, (LARG // 2, DICA_POS_Y), alfa=a)
        elif e == "derrota":
            a = int(255 * min(1.0, max(0.0, (t - 0.5) / 0.6)))
            if a > 0:
                veu = pygame.Surface((LARG, ALT))
                veu.fill((10, 6, 18))
                veu.set_alpha(int(a * 0.7))
                c.blit(veu, (0, 0))
                restantes = self.max_tentativas - self.tentativa
                if restantes > 0:
                    texto(c, "VOCÊ CAIU...", 84, (230, 70, 64), (LARG // 2, 290), alfa=a)
                    texto(c, f"Tentativas restantes: {restantes}", 36, (245, 240, 250), (LARG // 2, 366), alfa=a)
                    if t > 1.6:
                        texto(c, "ENTER - tentar de novo", 28, (210, 206, 220), (LARG // 2, 430))
                else:
                    texto(c, "O DRAGÃO VENCEU", 84, (230, 70, 64), (LARG // 2, 290), alfa=a)
                    texto(c, "Acabaram as tentativas: a jornada recomeça do início.", 32, (245, 240, 250),
                          (LARG // 2, 366), alfa=a)
                    if t > 1.6:
                        texto(c, "ENTER - recomeçar", 28, (210, 206, 220), (LARG // 2, 430))
        elif e == "cs_princesa":
            a = int(255 * self._alfa_pulso(t, 0.6, 3.2, 0.6))
            texto(c, "Você a encontrou!", 52, (255, 226, 150), (LARG // 2, 110), alfa=a)

    def _desenhar_pausa(self, c):
        veu = pygame.Surface((LARG, ALT))
        veu.fill((8, 6, 16))
        veu.set_alpha(170)
        c.blit(veu, (0, 0))
        texto(c, "PAUSADO", 84, (255, 214, 120), (LARG // 2, 170))
        y = 262
        for tecla, acao in TECLAS_PAUSA:
            texto(c, tecla, 30, (255, 226, 150), (LARG // 2 - 30, y), "direita")
            texto(c, acao, 30, (240, 236, 245), (LARG // 2 + 30, y), "esquerda")
            y += 44
        texto(c, "ENTER - sair do jogo", 28, (210, 206, 220), (LARG // 2, y + 30))

    def _desenhar_fim(self, c):
        t = self.t_estado
        a = int(255 * min(1.0, t / 1.0))
        texto(c, "FIM", 120, (255, 214, 120), (LARG // 2, 270), alfa=a)
        texto(c, "A Última Chama de Esparta", 40, (245, 240, 250), (LARG // 2, 372), alfa=a)
        texto(c, "Obrigado por jogar!", 30, (210, 206, 220), (LARG // 2, 430), alfa=a)
        if t > 1.0:
            texto(c, "ENTER - sair", 26, (170, 166, 184), (LARG // 2, 560))
