"""
Tela de GAME OVER aprimorada (pygame 2.x)

Efeitos:
  - Fundo em camadas (gradiente, montanhas com luz de contorno, névoa em movimento)
  - Fogo procedural com partículas aditivas (brilho real, sem sprites externos)
  - Brasas com parallax, fumaça suave e luz pulsante
  - Chama central que se apaga de verdade (falha, encolhe, vira brasa e fumaça)
  - Título com gradiente, brilho, aberração cromática e glitch
  - Painel translúcido com luz percorrendo a borda
  - Menu selecionável (setas / mouse / ENTER / ESC) com fade de saída
  - Tremor de tela, flash inicial, vinheta e scanlines
"""
import math
import random

import pygame

import config
from nucleo.cena import Cena


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _lerp(a, b, t):
    return a + (b - a) * t


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def _ease_out(t):
    t = _clamp(t)
    return 1 - (1 - t) ** 3


def _mix(c1, c2, t):
    t = _clamp(t)
    return tuple(int(_lerp(a, b, t)) for a, b in zip(c1, c2))


def _escala(cor, f):
    return tuple(int(_clamp(c * f, 0, 255)) for c in cor)


def _cor_fogo(t):
    """t: 0 (nasceu) -> 1 (morreu). Branco-amarelo -> laranja -> vermelho -> escuro."""
    t = _clamp(t)
    pontos = [
        (0.00, (255, 245, 190)),
        (0.25, (255, 170, 60)),
        (0.60, (205, 65, 22)),
        (1.00, (40, 10, 8)),
    ]
    for (t0, c0), (t1, c1) in zip(pontos, pontos[1:]):
        if t <= t1:
            return _mix(c0, c1, (t - t0) / (t1 - t0))
    return pontos[-1][1]


ADD = pygame.BLEND_RGB_ADD
MULT = pygame.BLEND_RGB_MULT


# ---------------------------------------------------------------------------
# Cena
# ---------------------------------------------------------------------------
class GameOver(Cena):
    OPCOES = [("Tentar novamente", "ENTER"), ("Voltar ao menu", "ESC")]

    def __init__(self, jogo, numero):
        super().__init__(jogo)
        self.numero = numero

        self.L = config.LARGURA
        self.A = config.ALTURA
        self.cx = self.L // 2
        self.cy = self.A // 2

        self.tempo = 0.0
        self.luz = 1.0
        self.selecionado = 0
        self.destino = None
        self.t_saida = 0.0

        self.glitch_ate = 1.0          # glitch de entrada
        self.proximo_glitch = 3.5

        self.cache_glow = {}
        self.cache_suave = {}

        # Cores
        self.dourado = (255, 196, 104)
        self.cinza = (150, 140, 136)
        self.branco = (238, 231, 222)

        self._criar_fontes()
        self._criar_layout()
        self._pre_renderizar()
        self._criar_particulas()

    # ------------------------------------------------------------------
    # Preparação
    # ------------------------------------------------------------------
    def _fonte(self, tam, negrito=False, italico=False):
        try:
            return pygame.font.SysFont(
                "georgia,palatinolinotype,timesnewroman,serif",
                tam, bold=negrito, italic=italico
            )
        except Exception:
            return pygame.font.Font(None, tam)

    def _criar_fontes(self):
        self.f_titulo = self._fonte(78, True)
        self.f_sub = self._fonte(30, False, True)
        self.f_opcao = self._fonte(27, True)
        self.f_tecla = self._fonte(16, True)
        self.f_detalhe = self._fonte(19, False, True)
        self.f_mini = self._fonte(15, True)

    def _criar_layout(self):
        self.pw, self.ph = 640, 440
        self.px = self.cx - self.pw // 2
        self.py = max(10, self.cy - self.ph // 2)

        self.chama_pos = (self.cx, self.py + 90)
        self.y_titulo = self.py + 185
        self.y_sub = self.py + 236
        self.y_div = self.py + 266
        self.y_frase = self.py + 398
        self.y_dica = self.py + 420

        self.rects_opcoes = []
        for i in range(len(self.OPCOES)):
            r = pygame.Rect(0, 0, 380, 42)
            r.center = (self.cx, self.py + 306 + i * 48)
            self.rects_opcoes.append(r)

    def _pre_renderizar(self):
        self.buffer = pygame.Surface((self.L, self.A))
        self._pre_fundo()
        self._pre_vinheta_scanlines()
        self._pre_painel()
        self._pre_titulo()
        self._pre_textos()

        self.flash = pygame.Surface((self.L, self.A))
        self.flash.fill((255, 70, 45))
        self.preto = pygame.Surface((self.L, self.A))
        self.preto.fill((0, 0, 0))

        self.paleta_fogo = [_escala(_cor_fogo(i / 23), 0.6) for i in range(24)]

    # ---- fundo -------------------------------------------------------
    def _pre_fundo(self):
        L, A = self.L, self.A
        s = pygame.Surface((L, A))
        for y in range(A):
            t = y / A
            pygame.draw.line(s, _mix((7, 5, 11), (32, 13, 17), t ** 1.6), (0, y), (L, y))

        # Camadas de montanhas (fundo -> frente) com luz de contorno
        camadas = [
            (A - 170, 95, (24, 12, 17), 1, 40, (80, 26, 22)),
            (A - 100, 70, (16, 8, 13), 2, 28, (60, 20, 18)),
            (A - 45, 40, (9, 5, 8), 3, 20, None),
        ]
        for base, amp, cor, seed, passo, rim in camadas:
            rnd = random.Random(seed)
            pts = []
            x = 0
            while x <= L + passo:
                pts.append((x, base - rnd.randint(0, amp)))
                x += passo
            poligono = [(0, A)] + pts + [(L, A)]
            pygame.draw.polygon(s, cor, poligono)
            if rim:
                pygame.draw.lines(s, rim, False, pts, 1)
        self.fundo = s

        # Luz avermelhada vinda do fogo (por baixo)
        altura = int(A * 0.6)
        luz = pygame.Surface((L, A), pygame.SRCALPHA)
        for i in range(altura):
            a = int(125 * (1 - i / altura) ** 2)
            pygame.draw.line(luz, (160, 34, 20, a), (0, A - i), (L, A - i))
        self.luz_base = luz

    def _pre_vinheta_scanlines(self):
        L, A = self.L, self.A
        w, h = 64, 36
        pq = pygame.Surface((w, h), pygame.SRCALPHA)
        for yy in range(h):
            for xx in range(w):
                dx = (xx / (w - 1) - 0.5) * 2
                dy = (yy / (h - 1) - 0.5) * 2
                d = math.sqrt(dx * dx * 0.9 + dy * dy * 1.1)
                a = int(_clamp((d - 0.45) / 0.85) ** 1.8 * 235)
                pq.set_at((xx, yy), (0, 0, 0, a))
        self.vinheta = pygame.transform.smoothscale(pq, (L, A))

        sc = pygame.Surface((L, A), pygame.SRCALPHA)
        for y in range(0, A, 3):
            pygame.draw.line(sc, (0, 0, 0, 34), (0, y), (L, y))
        self.scanlines = sc

    def _pre_painel(self):
        pw, ph = self.pw, self.ph

        grad = pygame.Surface((pw, ph), pygame.SRCALPHA)
        for y in range(ph):
            c = _mix((32, 23, 27), (15, 11, 14), y / ph)
            pygame.draw.line(grad, c + (226,), (0, y), (pw, y))

        mascara = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, pw, ph), border_radius=16)
        grad.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        pygame.draw.rect(grad, (66, 30, 28, 255), (0, 0, pw, ph), 1, border_radius=16)

        # Ornamentos de canto
        orn = (170, 105, 52, 255)
        m, c = 14, 24
        for sx in (m, pw - m):
            for sy in (m, ph - m):
                dx = 1 if sx == m else -1
                dy = 1 if sy == m else -1
                pygame.draw.line(grad, orn, (sx, sy), (sx + dx * c, sy), 2)
                pygame.draw.line(grad, orn, (sx, sy), (sx, sy + dy * c), 2)
                pygame.draw.circle(grad, (230, 150, 70, 255), (sx, sy), 3)

        # Divisor com losango
        yd = self.y_div - self.py
        cxl = pw // 2
        for lado in (-1, 1):
            for i in range(150):
                a = int(255 * (1 - i / 150))
                x = cxl + lado * (14 + i)
                grad.fill((125, 58, 46, a), (x, yd, 1, 1))
        pygame.draw.polygon(
            grad, (255, 170, 80, 255),
            [(cxl, yd - 5), (cxl + 6, yd), (cxl, yd + 5), (cxl - 6, yd)]
        )
        self.painel = grad

        # Sombra suave
        pad = 40
        sh = pygame.Surface((pw + pad * 2, ph + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 175), (pad, pad + 8, pw, ph), border_radius=20)
        pequeno = pygame.transform.smoothscale(sh, (sh.get_width() // 8, sh.get_height() // 8))
        self.sombra = pygame.transform.smoothscale(pequeno, sh.get_size())
        self.pad_sombra = pad

    def _texto_espacado(self, texto, fonte, cor, espaco):
        glifos = [fonte.render(ch, True, cor) for ch in texto]
        w = sum(g.get_width() for g in glifos) + espaco * (len(glifos) - 1)
        h = max(g.get_height() for g in glifos)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        x = 0
        for g in glifos:
            s.blit(g, (x, 0))
            x += g.get_width() + espaco
        return s

    def _sobre_preto(self, surf):
        base = pygame.Surface(surf.get_size())
        base.fill((0, 0, 0))
        base.blit(surf, (0, 0))
        return base

    def _glow_texto(self, surf, cor, pad=36, reducao=6):
        w, h = surf.get_size()
        base = pygame.Surface((w + pad * 2, h + pad * 2))
        base.fill((0, 0, 0))
        tint = surf.copy()
        tint.fill(cor + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        base.blit(tint, (pad, pad))
        peq = pygame.transform.smoothscale(
            base, (max(1, base.get_width() // reducao), max(1, base.get_height() // reducao))
        )
        return pygame.transform.smoothscale(peq, base.get_size()), pad

    def _pre_titulo(self):
        branco = self._texto_espacado("GAME OVER", self.f_titulo, (255, 255, 255), 7)
        w, h = branco.get_size()
        max_w = self.pw - 70
        if w > max_w:
            h = int(h * max_w / w)
            w = max_w
            branco = pygame.transform.smoothscale(branco, (w, h))

        grad = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            c = _mix((255, 150, 110), (165, 26, 26), y / max(1, h - 1))
            pygame.draw.line(grad, c + (255,), (0, y), (w, y))

        face = branco.copy()
        face.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        sombra = branco.copy()
        sombra.fill((20, 4, 4, 255), special_flags=pygame.BLEND_RGBA_MULT)

        final = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
        final.blit(sombra, (3, 4))
        final.blit(face, (0, 0))
        self.titulo = final

        self.titulo_glow, self.pad_glow = self._glow_texto(final, (255, 70, 35))

        ciano = self._sobre_preto(final)
        ciano.fill((0, 150, 190), special_flags=MULT)
        verm = self._sobre_preto(final)
        verm.fill((190, 0, 0), special_flags=MULT)
        self.titulo_ciano, self.titulo_verm = ciano, verm

    def _pre_textos(self):
        self.txt_fase = self._texto_espacado(
            f"FASE {self.numero}", self.f_mini, (190, 120, 60), 4
        )
        self.txt_sub = "Consumed by fear"
        self.txt_sub_larg = self.f_sub.size(self.txt_sub)[0]
        self.txt_frase = self.f_detalhe.render(
            "Sua jornada ainda não terminou.", True, (130, 117, 112)
        )
        self.txt_dica = self.f_mini.render(
            "SETAS / W S  navegar     ENTER  confirmar     ESC  menu",
            True, (92, 84, 82)
        )

        self.op_surfs = []
        for i, (rotulo, tecla) in enumerate(self.OPCOES):
            r = self.rects_opcoes[i]

            barra = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.rect(barra, (255, 130, 50, 38), barra.get_rect(), border_radius=10)
            pygame.draw.rect(barra, (230, 110, 50, 170), barra.get_rect(), 1, border_radius=10)

            badge = pygame.Surface((70, 26), pygame.SRCALPHA)
            pygame.draw.rect(badge, (255, 255, 255, 18), badge.get_rect(), border_radius=6)
            pygame.draw.rect(badge, (170, 150, 120, 120), badge.get_rect(), 1, border_radius=6)
            t = self.f_tecla.render(tecla, True, (205, 190, 165))
            badge.blit(t, t.get_rect(center=badge.get_rect().center))

            self.op_surfs.append({
                "barra": barra,
                "badge": badge,
                "sel": self.f_opcao.render(rotulo, True, self.dourado),
                "nor": self.f_opcao.render(rotulo, True, self.cinza),
            })

    def _criar_particulas(self):
        L, A = self.L, self.A

        self.fogo = []
        self.acum_fogo = 0.0
        self.taxa_fogo = 170

        self.brasas = []
        for _ in range(80):
            self.brasas.append(self._nova_brasa(inicial=True))

        self.fumaca = []
        self.acum_fumaca = 0.0

        self.nevoa = []
        for _ in range(5):
            w = random.randint(380, 620)
            h = random.randint(70, 130)
            self.nevoa.append({
                "x": random.uniform(-w, L),
                "y": random.uniform(A * 0.45, A * 0.85),
                "vx": random.uniform(6, 16),
                "surf": self._sprite_elipse(w, h, (80, 42, 46)),
                "alpha": random.randint(28, 55),
            })

    def _nova_brasa(self, inicial=False):
        depth = random.uniform(0.25, 1.0)
        return {
            "x": random.uniform(0, self.L),
            "y": random.uniform(0, self.A) if inicial else self.A + random.uniform(5, 60),
            "vy": random.uniform(22, 70) * (0.5 + depth),
            "depth": depth,
            "fase": random.uniform(0, math.pi * 2),
            "tam": int(1 + depth * 2.4),
        }

    # ------------------------------------------------------------------
    # Sprites procedurais (cache)
    # ------------------------------------------------------------------
    def _glow(self, raio, cor):
        raio = max(2, int(raio) // 2 * 2)
        cor = tuple(min(255, (c // 16) * 16) for c in cor)
        chave = (raio, cor)
        s = self.cache_glow.get(chave)
        if s is None:
            d = raio * 2
            s = pygame.Surface((d, d))
            s.fill((0, 0, 0))
            for r in range(raio, 0, -1):
                f = (1 - r / raio) ** 2
                pygame.draw.circle(
                    s, (int(cor[0] * f), int(cor[1] * f), int(cor[2] * f)),
                    (raio, raio), r
                )
            self.cache_glow[chave] = s
        return s

    def _blit_glow(self, destino, x, y, raio, cor):
        if max(cor) < 16:
            return
        s = self._glow(raio, cor)
        destino.blit(s, (x - s.get_width() // 2, y - s.get_height() // 2), special_flags=ADD)

    def _suave(self, raio):
        raio = max(4, int(raio) // 4 * 4)
        s = self.cache_suave.get(raio)
        if s is None:
            n = 16
            pq = pygame.Surface((n, n), pygame.SRCALPHA)
            for yy in range(n):
                for xx in range(n):
                    d = math.hypot((xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1)
                    pq.set_at((xx, yy), (120, 105, 105, int(_clamp(1 - d) ** 1.5 * 255)))
            s = pygame.transform.smoothscale(pq, (raio * 2, raio * 2))
            self.cache_suave[raio] = s
        return s

    def _sprite_elipse(self, w, h, cor):
        nw, nh = 24, 10
        pq = pygame.Surface((nw, nh), pygame.SRCALPHA)
        for yy in range(nh):
            for xx in range(nw):
                d = math.hypot((xx + 0.5) / nw * 2 - 1, (yy + 0.5) / nh * 2 - 1)
                pq.set_at((xx, yy), cor + (int(_clamp(1 - d) ** 1.4 * 255),))
        return pygame.transform.smoothscale(pq, (w, h))

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def eventos(self, eventos):
        if self.destino:
            return
        n = len(self.OPCOES)
        for e in eventos:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.selecionado = (self.selecionado - 1) % n
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.selecionado = (self.selecionado + 1) % n
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self._confirmar(self.selecionado)
                elif e.key == pygame.K_ESCAPE:
                    self._confirmar(1)

            elif e.type == pygame.MOUSEMOTION:
                for i, r in enumerate(self.rects_opcoes):
                    if r.collidepoint(e.pos):
                        self.selecionado = i

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(self.rects_opcoes):
                    if r.collidepoint(e.pos):
                        self.selecionado = i
                        self._confirmar(i)

    def _confirmar(self, indice):
        self.destino = "fase" if indice == 0 else "menu"
        self.t_saida = 0.0

    def _executar_destino(self):
        if self.destino == "fase":
            from cenas.fase import Fase
            self.jogo.trocar_cena(Fase(self.jogo, self.numero))
        else:
            from cenas.menu import Menu
            self.jogo.trocar_cena(Menu(self.jogo))

    # ------------------------------------------------------------------
    # Atualização
    # ------------------------------------------------------------------
    def atualizar(self, dt):
        if dt > 1:          # veio em milissegundos
            dt /= 1000.0
        dt = min(dt, 0.05)

        self.tempo += dt
        t = self.tempo

        # Luz instável do fogo
        self.luz = _clamp(
            0.8 + 0.2 * math.sin(t * 9) * math.sin(t * 3.7) + 0.05 * math.sin(t * 23),
            0.4, 1.1
        )

        self._atualizar_fogo(dt)
        self._atualizar_brasas(dt)
        self._atualizar_fumaca(dt)
        for n in self.nevoa:
            n["x"] += n["vx"] * dt
            if n["x"] > self.L:
                n["x"] = -n["surf"].get_width()

        if t >= self.proximo_glitch:
            self.glitch_ate = t + random.uniform(0.12, 0.28)
            self.proximo_glitch = t + random.uniform(3, 6)

        if self.destino:
            self.t_saida += dt
            if self.t_saida >= 0.5:
                self._executar_destino()

    def _atualizar_fogo(self, dt):
        t, L, A = self.tempo, self.L, self.A
        self.acum_fogo += dt * self.taxa_fogo
        while self.acum_fogo >= 1:
            self.acum_fogo -= 1
            if len(self.fogo) > 320:
                break
            x = random.uniform(-20, L + 20)
            onda = 0.55 + 0.45 * math.sin(x * 0.018 + t * 2.2) * math.sin(x * 0.007 - t * 1.3)
            if random.random() > onda:
                continue
            vida = random.uniform(0.7, 1.4)
            self.fogo.append({
                "x": x, "y": A + 8,
                "vx": random.uniform(-14, 14),
                "vy": -random.uniform(70, 170),
                "vida": vida, "max": vida,
                "tam": random.uniform(12, 26),
                "fase": random.uniform(0, math.pi * 2),
            })

        vivos = []
        for p in self.fogo:
            p["vida"] -= dt
            if p["vida"] <= 0:
                continue
            p["y"] += p["vy"] * dt
            p["x"] += (p["vx"] + math.sin(t * 4 + p["fase"]) * 22) * dt
            vivos.append(p)
        self.fogo = vivos

    def _atualizar_brasas(self, dt):
        t = self.tempo
        for i, b in enumerate(self.brasas):
            b["y"] -= b["vy"] * dt
            b["x"] += (math.sin(t * 0.9 + b["fase"]) * 18 + 12) * b["depth"] * dt
            if b["y"] < -10 or b["x"] > self.L + 20:
                self.brasas[i] = self._nova_brasa()

    def _estado_chama(self):
        t = self.tempo
        p = _clamp((t - 1.1) / 3.0)
        k = 1 - p ** 0.7
        if 0 < p < 1:
            k *= 0.7 + 0.3 * abs(math.sin(t * 14 + math.sin(t * 5) * 3))
        return p, k

    def _atualizar_fumaca(self, dt):
        t = self.tempo
        p, k = self._estado_chama()
        if t > 1.1:
            taxa = (14 if p < 1 else 5) * _clamp(p * 2)
            self.acum_fumaca += dt * taxa
            cx, cy = self.chama_pos
            while self.acum_fumaca >= 1:
                self.acum_fumaca -= 1
                if len(self.fumaca) < 60:
                    vida = random.uniform(2.5, 3.5)
                    self.fumaca.append({
                        "x": cx + random.uniform(-3, 3),
                        "y": cy + 26 - 63 * k,
                        "vx": random.uniform(-8, 8),
                        "vy": -random.uniform(22, 40),
                        "r": random.uniform(6, 10),
                        "vida": vida, "max": vida,
                        "fase": random.uniform(0, math.pi * 2),
                    })
        vivos = []
        for s in self.fumaca:
            s["vida"] -= dt
            if s["vida"] <= 0:
                continue
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            vivos.append(s)
        self.fumaca = vivos

    # ------------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------------
    def desenhar(self, tela):
        buf = self.buffer
        t = self.tempo

        buf.blit(self.fundo, (0, 0))
        self._desenhar_nevoa(buf)

        self.luz_base.set_alpha(int(_clamp(0.65 + 0.35 * self.luz) * 255))
        buf.blit(self.luz_base, (0, 0))

        self._desenhar_fogo(buf)
        self._desenhar_brasas(buf, frente=False)
        self._desenhar_painel(buf)
        self._desenhar_conteudo(buf)
        self._desenhar_brasas(buf, frente=True)

        # Tremor de tela
        amp = 14 * math.exp(-t * 3.5)
        if t > 0.5:
            amp += 9 * math.exp(-(t - 0.5) * 9)
        ox = int(random.uniform(-amp, amp)) if amp > 0.4 else 0
        oy = int(random.uniform(-amp, amp)) if amp > 0.4 else 0
        tela.fill((0, 0, 0))
        tela.blit(buf, (ox, oy))

        # Pós-processamento
        a = int(200 * math.exp(-t * 6.5))
        if a > 2:
            self.flash.set_alpha(a)
            tela.blit(self.flash, (0, 0))

        tela.blit(self.vinheta, (0, 0))
        tela.blit(self.scanlines, (0, 0))

        fade = 255 * (1 - _clamp(t / 0.9))
        if self.destino:
            fade = max(fade, 255 * _clamp(self.t_saida / 0.5))
        if fade > 1:
            self.preto.set_alpha(int(fade))
            tela.blit(self.preto, (0, 0))

    # ---- camadas de fundo --------------------------------------------
    def _desenhar_nevoa(self, buf):
        for n in self.nevoa:
            n["surf"].set_alpha(int(n["alpha"] * (0.7 + 0.3 * self.luz)))
            buf.blit(n["surf"], (int(n["x"]), int(n["y"])))

    def _desenhar_fogo(self, buf):
        pal = self.paleta_fogo
        for p in self.fogo:
            u = 1 - p["vida"] / p["max"]
            cor = pal[min(len(pal) - 1, int(u * len(pal)))]
            tam = p["tam"] * (1 - u * 0.75)
            self._blit_glow(buf, int(p["x"]), int(p["y"]), tam, cor)

    def _desenhar_brasas(self, buf, frente):
        t = self.tempo
        for b in self.brasas:
            if (b["depth"] > 0.75) != frente:
                continue
            pulso = 0.55 + 0.45 * abs(math.sin(t * 3 + b["fase"]))
            fade = _clamp(b["y"] / (self.A * 0.35))
            f = pulso * fade
            cor = (int(255 * f), int(110 * f + 20 * fade), int(30 * fade))
            x, y = int(b["x"]), int(b["y"])
            pygame.draw.circle(buf, cor, (x, y), b["tam"])
            if b["tam"] >= 2:
                self._blit_glow(buf, x, y, b["tam"] * 5, _escala((140, 55, 20), f))

    # ---- painel -------------------------------------------------------
    def _desenhar_painel(self, buf):
        t = self.tempo
        a = int(255 * _ease_out((t - 0.15) / 0.5))
        if a <= 0:
            return
        px, py, pw, ph = self.px, self.py, self.pw, self.ph

        self.sombra.set_alpha(a)
        self.painel.set_alpha(a)
        buf.blit(self.sombra, (px - self.pad_sombra, py - self.pad_sombra))
        buf.blit(self.painel, (px, py))

        # Borda pulsante
        pulso = 0.5 + 0.5 * math.sin(t * 2)
        cor = _mix((95, 36, 32), (190, 70, 40), pulso * _clamp(self.luz))
        pygame.draw.rect(buf, cor, (px, py, pw, ph), 2, border_radius=16)

        # Linha superior com luz percorrendo
        y = py + 2
        pygame.draw.line(buf, (120, 50, 36), (px + 50, y), (px + pw - 50, y), 2)
        pos = math.sin(t * 0.9) * 0.5 + 0.5
        xl = px + 50 + int(pos * (pw - 100))
        self._blit_glow(buf, xl, y, 40, (255, 130, 60))

    # ---- conteúdo -----------------------------------------------------
    def _desenhar_conteudo(self, buf):
        t = self.tempo
        cx = self.cx

        # Rótulo da fase
        a = _clamp((t - 0.3) / 0.5)
        if a > 0:
            self.txt_fase.set_alpha(int(255 * a))
            buf.blit(self.txt_fase, self.txt_fase.get_rect(center=(cx, self.py + 24)))

        self._desenhar_chama(buf)
        self._desenhar_titulo(buf)
        self._desenhar_subtitulo(buf)
        self._desenhar_fumaca(buf)
        self._desenhar_opcoes(buf)

        a = _clamp((t - 2.3) / 0.8)
        if a > 0:
            self.txt_frase.set_alpha(int(255 * a))
            buf.blit(self.txt_frase, self.txt_frase.get_rect(center=(cx, self.y_frase)))
            self.txt_dica.set_alpha(int(255 * a))
            buf.blit(self.txt_dica, self.txt_dica.get_rect(center=(cx, self.y_dica)))

    def _poly_chama(self, cx, base_y, altura, largura, seed):
        t = self.tempo
        n = 16
        esq, dir_ = [], []
        for i in range(n + 1):
            u = i / n
            w = largura * math.sin(math.pi * (0.12 + 0.88 * u ** 0.85))
            bal = (math.sin(t * 6.5 + u * 3.2 + seed) * 0.55
                   + math.sin(t * 11 + u * 5 + seed * 2) * 0.25) * largura * 0.55 * u
            y = base_y - u * altura
            esq.append((cx + bal - w, y))
            dir_.append((cx + bal + w, y))
        return esq + dir_[::-1] + [(cx, base_y + largura * 0.4)]

    def _desenhar_chama(self, buf):
        t = self.tempo
        cx, cy = self.chama_pos
        p, k = self._estado_chama()
        base_y = cy + 30

        # Luz ambiente da chama
        if k > 0.02:
            raio = 30 + 80 * k
            self._blit_glow(
                buf, cx, cy + 10, raio,
                _escala((150, 60, 22), k * self.luz)
            )

        # Toras
        pygame.draw.line(buf, (52, 34, 30), (cx - 36, cy + 44), (cx + 32, cy + 28), 9)
        pygame.draw.line(buf, (44, 28, 25), (cx - 32, cy + 28), (cx + 36, cy + 44), 9)
        pygame.draw.line(buf, (95, 50, 36), (cx - 36, cy + 41), (cx + 32, cy + 25), 2)

        # Chama
        if k > 0.05:
            H = 70 * k ** 0.8
            W = 20 * (0.55 + 0.45 * k)
            capas = [
                (1.00, (185, 36, 30), 0.0),
                (0.80, (238, 100, 38), 1.7),
                (0.58, (255, 170, 66), 3.1),
                (0.34, (255, 238, 190), 4.4),
            ]
            for esc, cor, seed in capas:
                pts = self._poly_chama(cx, base_y, H * esc, W * esc, seed)
                pygame.draw.polygon(buf, cor, pts)
            self._blit_glow(buf, cx, int(base_y - H * 0.4), 18 + 34 * k,
                            _escala((120, 50, 15), k))

        # Brasa que sobra
        e = (0.35 + 0.65 * p) * (1 - k)
        if e > 0.02:
            pulso = 0.6 + 0.4 * math.sin(t * 2.5)
            self._blit_glow(buf, cx, cy + 26, 14 + 12 * e,
                            _escala((230, 90, 25), e * pulso))
            pygame.draw.circle(
                buf, _escala((255, 150, 60), 0.5 + 0.5 * pulso * e),
                (cx, cy + 26), 3
            )

    def _desenhar_fumaca(self, buf):
        for s in self.fumaca:
            u = 1 - s["vida"] / s["max"]
            idade = s["max"] - s["vida"]
            raio = s["r"] + 12 * idade
            alpha = int(80 * (1 - u) ** 1.5 * min(1, u * 6))
            if alpha < 2:
                continue
            spr = self._suave(raio)
            spr.set_alpha(alpha)
            x = s["x"] + math.sin(idade * 2 + s["fase"]) * 10
            buf.blit(spr, (x - spr.get_width() // 2, s["y"] - spr.get_height() // 2))

    def _desenhar_titulo(self, buf):
        t = self.tempo
        a = _ease_out((t - 0.5) / 0.7)
        if a <= 0:
            return
        rect = self.titulo.get_rect(center=(self.cx, self.y_titulo))

        # Brilho pulsante
        k = int(255 * a * _clamp(0.55 + 0.45 * self.luz))
        g = self.titulo_glow.copy()
        g.fill((k, k, k), special_flags=MULT)
        buf.blit(g, (rect.x - self.pad_glow, rect.y - self.pad_glow), special_flags=ADD)

        if t < self.glitch_ate:
            d = random.randint(3, 9)
            buf.blit(self.titulo_ciano, (rect.x - d, rect.y), special_flags=ADD)
            buf.blit(self.titulo_verm, (rect.x + d, rect.y), special_flags=ADD)

            h = self.titulo.get_height()
            w = self.titulo.get_width()
            y = 0
            self.titulo.set_alpha(int(255 * a))
            while y < h:
                fh = random.randint(6, 18)
                dx = random.randint(-16, 16) if random.random() < 0.45 else 0
                area = pygame.Rect(0, y, w, min(fh, h - y))
                buf.blit(self.titulo, (rect.x + dx, rect.y + y), area)
                y += fh
        else:
            self.titulo.set_alpha(int(255 * a))
            buf.blit(self.titulo, rect)

    def _desenhar_subtitulo(self, buf):
        t = self.tempo
        if t < 1.3:
            return
        n = int((t - 1.3) * 14)
        texto = self.txt_sub[:n]
        if not texto:
            return
        img = self.f_sub.render(texto, True, self.branco)
        x = self.cx - self.txt_sub_larg // 2
        buf.blit(img, (x, self.y_sub - img.get_height() // 2))

    def _desenhar_opcoes(self, buf):
        t = self.tempo
        for i, rect in enumerate(self.rects_opcoes):
            surfs = self.op_surfs[i]
            ap = _clamp((t - 1.8 - i * 0.15) / 0.5)
            if ap <= 0:
                continue
            sel = (i == self.selecionado)

            if sel:
                surfs["barra"].set_alpha(int(255 * ap * (0.75 + 0.25 * math.sin(t * 5))))
                buf.blit(surfs["barra"], rect)

                off = 3 * math.sin(t * 6)
                cy = rect.centery
                xe = rect.x - 16 + off
                xd = rect.right + 16 - off
                pygame.draw.polygon(buf, self.dourado,
                                    [(xe, cy - 6), (xe + 8, cy), (xe, cy + 6)])
                pygame.draw.polygon(buf, self.dourado,
                                    [(xd, cy - 6), (xd - 8, cy), (xd, cy + 6)])

            surfs["badge"].set_alpha(int(255 * ap))
            buf.blit(surfs["badge"], (rect.x + 16, rect.centery - 13))

            txt = surfs["sel"] if sel else surfs["nor"]
            txt.set_alpha(int(255 * ap))
            buf.blit(txt, (rect.x + 16 + 70 + 18, rect.centery - txt.get_height() // 2))