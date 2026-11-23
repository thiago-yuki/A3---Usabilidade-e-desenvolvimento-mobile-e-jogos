import math
import os
import random

import pygame

import config
from nucleo.cena import Cena


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def _limitar(valor, minimo=0.0, maximo=1.0):
    return max(minimo, min(maximo, valor))


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_cor(c1, c2, t):
    t = _limitar(t)
    return tuple(int(_lerp(a, b, t)) for a, b in zip(c1, c2))


class Menu(Cena):

    DURACAO_SAIDA = 0.6      # fade-out ao iniciar o jogo / sair
    DURACAO_ENTRADA = 1.1    # fade-in ao abrir o menu

    def __init__(self, jogo):
        super().__init__(jogo)

        self.largura = config.LARGURA
        self.altura = config.ALTURA
        self.centro = self.largura // 2

        # fator de escala (a interface foi pensada em 960x540)
        self.k = min(self.largura / 960, self.altura / 540)
        k = self.k

        self.tempo = 0.0          # tempo total da cena
        self.tempo_tela = 0.0     # tempo desde a última troca de tela

        # -------------------------------------------------
        # CORES
        # -------------------------------------------------

        self.dourado = (177, 139, 83)
        self.dourado_claro = (226, 195, 137)
        self.dourado_vivo = (255, 222, 150)
        self.branco = (225, 220, 210)
        self.cinza = (175, 169, 180)

        # -------------------------------------------------
        # FONTES
        # -------------------------------------------------

        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pasta_fontes = os.path.join(raiz, "assets", "fontes")
        self.pasta_fontes = pasta_fontes

        self.fonte_subtitulo = self._carregar_fonte(
            pasta_fontes, "CormorantGaramond-Italic.ttf", int(31 * k)
        )
        self.fonte_botao = self._carregar_fonte(
            pasta_fontes, "Cinzel-SemiBold.ttf", int(22 * k)
        )
        self.fonte_pequena = self._carregar_fonte(
            pasta_fontes, "CormorantGaramond-Italic.ttf", int(22 * k)
        )
        self.fonte_secundaria = self._carregar_fonte(
            pasta_fontes, "CormorantGaramond-Medium.ttf", int(29 * k)
        )

        # fontes da tela "Como Jogar"
        self.fonte_tecla = self._carregar_fonte(
            pasta_fontes, "Cinzel-SemiBold.ttf", int(13 * k)
        )
        self.fonte_cabecalho = self._carregar_fonte(
            pasta_fontes, "Cinzel-SemiBold.ttf", int(15 * k)
        )
        self.fonte_desc = self._carregar_fonte(
            pasta_fontes, "CormorantGaramond-Medium.ttf", int(20 * k)
        )

        # Dica: para um título ainda mais imponente, coloque um destes
        # arquivos em assets/fontes (ele será usado automaticamente):
        # CinzelDecorative-Black.ttf ou CinzelDecorative-Bold.ttf
        fontes_titulo = [
            "CinzelDecorative-Black.ttf",
            "CinzelDecorative-Bold.ttf",
            "Cinzel-Bold.ttf",
        ]

        self.titulo_principal = self._titulo_ajustado(
            pasta_fontes, fontes_titulo, "FALLING IN FEARS",
            int(60 * k), int(self.largura * 0.84), atraso=0.0
        )
        self.titulo_como = self._titulo_ajustado(
            pasta_fontes, fontes_titulo, "COMO JOGAR",
            int(40 * k), int(self.largura * 0.60), atraso=1.7
        )
        self.titulo_creditos = self._titulo_ajustado(
            pasta_fontes, fontes_titulo, "CRÉDITOS",
            int(42 * k), int(self.largura * 0.60), atraso=3.1
        )

        # -------------------------------------------------
        # TELAS E BOTÕES
        # -------------------------------------------------

        self.tela_atual = "menu"
        self.nomes = [
            "JOGAR",
            "COMO JOGAR",
            "CRÉDITOS",
            "SAIR",
        ]
        self.selecionado = 0

        self.btn_w = int(310 * k)
        self.btn_h = int(self.altura * 0.088)

        inicio_y = int(self.altura * 0.39)
        espacamento = int(self.altura * 0.092)

        self.botoes = {}
        for i, nome in enumerate(self.nomes):
            self.botoes[nome] = pygame.Rect(
                self.centro - self.btn_w // 2,
                inicio_y + espacamento * i,
                self.btn_w,
                self.btn_h
            )

        self.botao_voltar = pygame.Rect(
            self.centro - self.btn_w // 2,
            int(self.altura * 0.835),
            self.btn_w,
            self.btn_h
        )

        self.hover = {nome: 0.0 for nome in self.nomes + ["VOLTAR"]}
        self._ultimo_mouse = None

        self._acao_pendente = None
        self._fade_saida = 0.0

        # -------------------------------------------------
        # SUPERFÍCIES PRÉ-RENDERIZADAS (desempenho)
        # -------------------------------------------------

        self._preparar_fundo(raiz)
        self._preparar_efeitos()
        self._preparar_interface()

    # =====================================================
    # CARREGAMENTO
    # =====================================================

    def _carregar_fonte(self, pasta, arquivos, tamanho):
        if isinstance(arquivos, str):
            arquivos = [arquivos]

        for arquivo in arquivos:
            caminho = os.path.join(pasta, arquivo)
            if os.path.exists(caminho):
                try:
                    return pygame.font.Font(caminho, tamanho)
                except (pygame.error, OSError):
                    pass

        return pygame.font.Font(None, tamanho)

    # =====================================================
    # CONSTRUTORES DE SUPERFÍCIES
    # =====================================================

    def _criar_halo(self, w, h, cor, alpha, potencia=1.6):
        """Gradiente radial suave (centro opaco, bordas transparentes)."""
        base = 48
        c = base // 2
        s = pygame.Surface((base, base), pygame.SRCALPHA)

        for r in range(c, 0, -1):
            f = 1 - r / c
            a = int(alpha * (f ** potencia))
            pygame.draw.circle(s, (cor[0], cor[1], cor[2], a), (c, c), r)

        return pygame.transform.smoothscale(s, (max(1, w), max(1, h)))

    def _sprite_brilho(self, raio, cor, intensidade):
        """Pequena esfera luminosa para ser desenhada com soma de cores."""
        d = raio * 6
        c = d // 2
        s = pygame.Surface((d, d))

        for r in range(c, 0, -1):
            f = ((1 - r / c) ** 2.2) * intensidade
            pygame.draw.circle(
                s,
                (int(cor[0] * f), int(cor[1] * f), int(cor[2] * f)),
                (c, c),
                r
            )

        nucleo = tuple(min(255, int((v + 50) * intensidade)) for v in cor)
        pygame.draw.circle(s, nucleo, (c, c), max(1, raio - 1))

        return s

    def _mascara_texto(self, texto, fonte, espaco):
        letras = [fonte.render(ch, True, (255, 255, 255)) for ch in texto]

        largura = sum(l.get_width() for l in letras) + espaco * (len(letras) - 1)
        altura = max(l.get_height() for l in letras)

        mascara = pygame.Surface((largura, altura), pygame.SRCALPHA)

        x = 0
        for letra in letras:
            mascara.blit(letra, (x, 0))
            x += letra.get_width() + espaco

        return mascara

    def _criar_titulo(self, texto, fonte, espaco, atraso):
        """
        Monta um título em ouro com degradê, contorno, sombra,
        brilho (glow) e uma faixa de luz que passa de tempos em tempos.
        """
        k = self.k

        mascara = self._mascara_texto(texto, fonte, espaco)
        w, h = mascara.get_size()

        pad = int(26 * k)
        W, H = w + pad * 2, h + pad * 2

        # --- degradê dourado ---
        topo = (255, 245, 210)
        meio = (236, 192, 108)
        base = (158, 104, 50)

        grad = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            if t < 0.5:
                cor = _lerp_cor(topo, meio, t / 0.5)
            else:
                cor = _lerp_cor(meio, base, (t - 0.5) / 0.5)
            pygame.draw.line(grad, cor + (255,), (0, y), (w, y))

        grad.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # --- contorno e sombra ---
        escura = mascara.copy()
        escura.fill((38, 20, 8, 255), special_flags=pygame.BLEND_RGBA_MULT)

        sombra = mascara.copy()
        sombra.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)

        final = pygame.Surface((W, H), pygame.SRCALPHA)
        final.blit(sombra, (pad + int(3 * k), pad + int(6 * k)))

        e = max(1, int(2 * k))
        for dx, dy in [(-e, 0), (e, 0), (0, -e), (0, e),
                       (-e, -e), (e, e), (-e, e), (e, -e)]:
            final.blit(escura, (pad + dx, pad + dy))

        final.blit(grad, (pad, pad))

        # --- máscara completa (usada no brilho em movimento) ---
        mascara_full = pygame.Surface((W, H), pygame.SRCALPHA)
        mascara_full.blit(mascara, (pad, pad))

        # --- glow suave ---
        tinta = mascara.copy()
        tinta.fill((255, 185, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)

        grande = pygame.Surface((W, H), pygame.SRCALPHA)
        grande.blit(tinta, (pad, pad))

        pequeno = pygame.transform.smoothscale(
            grande, (max(1, W // 6), max(1, H // 6))
        )
        glow = pygame.transform.smoothscale(pequeno, (W, H))

        # --- faixa de luz inclinada ---
        fw = max(20, int(64 * k))
        extra = int(H * 0.4)

        faixa = pygame.Surface((fw + extra, H), pygame.SRCALPHA)
        tira = pygame.Surface((fw, 1), pygame.SRCALPHA)

        for x in range(fw):
            a = int(210 * (math.sin(math.pi * x / (fw - 1)) ** 2))
            tira.set_at((x, 0), (255, 247, 225, a))

        for y in range(H):
            faixa.blit(tira, (int((H - y) * 0.4), y))

        return {
            "final": final,
            "glow": glow,
            "mascara": mascara_full,
            "faixa": faixa,
            "tam": (W, H),
            "atraso": atraso,
        }

    def _titulo_ajustado(self, pasta, arquivos, texto, tamanho,
                         largura_max, atraso):
        """Reduz a fonte até o título caber na tela."""
        while True:
            fonte = self._carregar_fonte(pasta, arquivos, tamanho)
            espaco = max(1, int(tamanho * 0.09))
            dados = self._criar_titulo(texto, fonte, espaco, atraso)

            if dados["tam"][0] <= largura_max or tamanho <= 20:
                return dados

            tamanho -= 3

    # =====================================================
    # PREPARAÇÃO DE FUNDO, EFEITOS E INTERFACE
    # =====================================================

    def _preparar_fundo(self, raiz):
        L, A = self.largura, self.altura

        imagem = None
        caminho = os.path.join(
            raiz, "assets", "fundo_introducao.jfif"
        )

        if os.path.exists(caminho):
            try:
                imagem = pygame.image.load(caminho).convert()
            except pygame.error:
                imagem = None

        if imagem is not None:
            iw, ih = imagem.get_size()
            escala = max(L / iw, A / ih) * 1.10   # sobra para o "zoom" lento
            self.fundo = pygame.transform.smoothscale(
                imagem, (int(iw * escala), int(ih * escala))
            )
        else:
            self.fundo = pygame.Surface((L, A))
            for y in range(A):
                cor = _lerp_cor((34, 24, 46), (13, 9, 21), y / A)
                pygame.draw.line(self.fundo, cor, (0, y), (L, y))

        # escurecimento com degradê (mais escuro em cima e embaixo)
        self.escurecer = pygame.Surface((L, A), pygame.SRCALPHA)
        for y in range(A):
            t = y / A
            a = int(105 + 75 * (1 - math.sin(t * math.pi)))
            pygame.draw.line(self.escurecer, (13, 9, 22, a), (0, y), (L, y))

        # vinheta radial
        pw, ph = 64, 36
        pequena = pygame.Surface((pw, ph), pygame.SRCALPHA)
        for y in range(ph):
            for x in range(pw):
                dx = (x - pw / 2) / (pw / 2)
                dy = (y - ph / 2) / (ph / 2)
                d = math.sqrt(dx * dx + dy * dy) / 1.414
                a = int((_limitar((d - 0.35) / 0.65) ** 1.8) * 215)
                pequena.set_at((x, y), (6, 3, 12, a))
        self.vinheta = pygame.transform.smoothscale(pequena, (L, A))

        # raios de luz suaves vindos do alto
        raios = pygame.Surface((L, A), pygame.SRCALPHA)
        for x0, larg, incl in [(0.10, 0.07, 0.18), (0.30, 0.05, 0.15),
                               (0.60, 0.08, 0.20), (0.82, 0.05, 0.14)]:
            xs = int(L * x0)
            w = int(L * larg)
            d = int(L * incl)
            fim = int(A * 0.9)
            pygame.draw.polygon(
                raios, (255, 222, 160, 40),
                [(xs, 0), (xs + w, 0), (xs + w * 2 + d, fim), (xs + d, fim)]
            )
        pequeno = pygame.transform.smoothscale(raios, (L // 6, A // 6))
        self.raios = pygame.transform.smoothscale(pequeno, (L, A))

        # cortina preta para os fades
        self.cortina = pygame.Surface((L, A))
        self.cortina.fill((0, 0, 0))

        self._camada = pygame.Surface((L, A), pygame.SRCALPHA)

    def _preparar_efeitos(self):
        L, A, k = self.largura, self.altura, self.k

        # --- névoa ---
        self.nevoas = []
        for _ in range(7):
            w = int(random.randint(380, 620) * k)
            h = int(random.randint(90, 150) * k)
            self.nevoas.append({
                "x": random.uniform(-w, L),
                "y": int(A * random.uniform(0.68, 0.97)),
                "vel": random.uniform(6, 16) * k,
                "w": w,
                "surf": self._criar_halo(w, h, (125, 108, 150), 58),
            })

        # --- sprites de brilho (brasas e vagalumes) ---
        niveis = [0.35, 0.55, 0.8, 1.0]
        cores = {
            "ouro": (255, 175, 70),
            "roxo": (160, 110, 220),
            "claro": (255, 225, 170),
        }

        self.sprites = {}
        for nome, cor in cores.items():
            for raio in (1, 2, 3):
                r = max(1, int(raio * k + 0.5))
                for n, inten in enumerate(niveis):
                    self.sprites[(nome, raio, n)] = self._sprite_brilho(
                        r, cor, inten
                    )

        self.particulas = []
        for _ in range(75):
            self.particulas.append({
                "x": random.uniform(0, L),
                "y": random.uniform(0, A),
                "vel": random.uniform(12, 42) * k,
                "raio": random.choice([1, 1, 2, 2, 3]),
                "fase": random.uniform(0, math.pi * 2),
                "cor": random.choice(["ouro", "ouro", "ouro",
                                      "claro", "roxo"]),
                "deriva": random.uniform(8, 22) * k,
            })

    def _preparar_interface(self):
        k = self.k
        w, h = self.btn_w, self.btn_h

        # botões
        self.bt_normal = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(
            self.bt_normal, (22, 15, 32, 200), (0, 0, w, h), border_radius=7
        )

        self.bt_hover = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(
            self.bt_hover, (100, 62, 118, 225), (0, 0, w, h), border_radius=7
        )

        self.glow_botao = self._criar_halo(
            w + int(90 * k), h + int(70 * k), (225, 170, 90), 120
        )

        # halo escuro atrás do título (legibilidade)
        self.halo_escuro = self._criar_halo(
            int(self.largura * 0.92), int(self.altura * 0.56),
            (6, 4, 12), 170, potencia=1.1
        )

        # brilho do ornamento
        self.halo_ornamento = self._criar_halo(
            int(70 * k), int(70 * k), (255, 215, 140), 190
        )

        # painel das telas secundárias (mesmo estilo da introdução)
        pw = int(700 * k)
        ph = int(self.altura * 0.66)

        self.painel_sec = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(
            self.painel_sec, (10, 10, 17, 205), (0, 0, pw, ph),
            border_radius=10
        )
        pygame.draw.rect(
            self.painel_sec, (145, 110, 67, 190), (0, 0, pw, ph), 1,
            border_radius=10
        )
        pygame.draw.rect(
            self.painel_sec, (145, 110, 67, 70),
            (7, 7, pw - 14, ph - 14), 1, border_radius=7
        )
        self.painel_rect = self.painel_sec.get_rect(
            midtop=(self.centro, int(self.altura * 0.115))
        )

        self._montar_como_jogar()

    # =====================================================
    # TELA "COMO JOGAR" (pré-renderizada uma única vez)
    # =====================================================

    TEXTO_SOBRE = (
        "Você controlará uma guerreira equipada com sua armadura, "
        "pronta para enfrentar criaturas e superar seus medos. "
        "Cada fase apresenta inimigos e desafios diferentes. "
        "Seus ataques e habilidades poderão variar de acordo com a "
        "criatura enfrentada e a mecânica daquela etapa."
    )

    TEXTO_OBJETIVO = (
        "Atravesse os cenários, enfrente ou desvie dos inimigos e "
        "encontre a saída de cada fase. Prepare-se para o confronto "
        "final contra o dragão!"
    )

    # (teclas, descrição) -> "k" = tecla, "t" = texto de ligação
    CONTROLES = [
        ([("k", "W"), ("k", "A"), ("k", "S"), ("k", "D"),
          ("t", "ou"), ("k", "SETAS")],
         "Movimentar a personagem"),
        ([("k", "ESPAÇO")],
         "Pular"),
        ([("k", "MOUSE"), ("t", "/"), ("k", "TECLA DE ATAQUE")],
         "Utilizar o ataque disponível na fase"),
        ([("k", "ESC")],
         "Pausar ou voltar ao menu"),
    ]

    def _quebrar_linhas(self, texto, fonte, largura):
        linhas = []
        atual = ""

        for palavra in texto.split():
            teste = (atual + " " + palavra).strip()

            if fonte.size(teste)[0] <= largura:
                atual = teste
            else:
                linhas.append(atual)
                atual = palavra

        if atual:
            linhas.append(atual)

        return linhas

    def _texto_esq(self, alvo, texto, fonte, cor, x, y):
        sombra = fonte.render(texto, True, (0, 0, 0))
        alvo.blit(sombra, (x + 1, y + 2))
        alvo.blit(fonte.render(texto, True, cor), (x, y))

    def _texto_espacado(self, alvo, texto, fonte, cor, x, y, espaco):
        for ch in texto:
            img = fonte.render(ch, True, cor)
            alvo.blit(img, (x, y))
            x += img.get_width() + espaco
        return x

    def _cabecalho(self, alvo, texto, x, y, largura):
        """Título de seção: losango + texto espaçado + linha que some."""
        k = self.k
        fonte = self.fonte_cabecalho
        cy = y + fonte.get_height() // 2

        m = max(3, int(4 * k))
        pygame.draw.polygon(
            alvo, self.dourado_vivo,
            [(x + m, cy - m), (x + m * 2, cy), (x + m, cy + m), (x, cy)]
        )

        fim = self._texto_espacado(
            alvo, texto, fonte, self.dourado_claro,
            x + int(18 * k), y, max(1, int(2 * k))
        )

        lx0 = fim + int(10 * k)
        lx1 = x + largura
        total = max(1, lx1 - lx0)

        for i in range(0, total, 4):
            a = int(190 * (1 - i / total))
            pygame.draw.line(
                alvo, (177, 139, 83, a),
                (lx0 + i, cy), (min(lx1, lx0 + i + 4), cy), 1
            )

        return int(28 * k)

    def _chip(self, alvo, texto, x, y, altura):
        """Desenha uma 'tecla' e devolve a largura ocupada."""
        k = self.k
        img = self.fonte_tecla.render(texto, True, self.dourado_vivo)
        w = max(altura, img.get_width() + int(18 * k))
        r = pygame.Rect(x, y, w, altura)

        pygame.draw.rect(alvo, (30, 22, 40, 255), r, border_radius=5)
        pygame.draw.rect(alvo, (150, 111, 67, 255), r, 1, border_radius=5)
        pygame.draw.line(
            alvo, (205, 160, 90, 255),
            (r.left + 5, r.bottom - 2), (r.right - 6, r.bottom - 2), 1
        )

        alvo.blit(img, img.get_rect(center=(r.centerx, r.centery - 1)))
        return w

    def _montar_como_jogar(self):
        k = self.k
        A = self.altura

        pw = int(840 * k)
        ph = int(A * 0.705)
        topo = int(A * 0.095)

        self.painel_como_rect = pygame.Rect(0, 0, pw, ph)
        self.painel_como_rect.midtop = (self.centro, topo)

        s = pygame.Surface((pw, ph), pygame.SRCALPHA)

        # fundo do painel (mesmo estilo da introdução)
        pygame.draw.rect(s, (10, 10, 17, 210), (0, 0, pw, ph),
                         border_radius=10)
        pygame.draw.rect(s, (145, 110, 67, 190), (0, 0, pw, ph), 1,
                         border_radius=10)
        pygame.draw.rect(s, (145, 110, 67, 70),
                         (7, 7, pw - 14, ph - 14), 1, border_radius=7)

        pad = int(36 * k)
        y0 = int(A * 0.24) - topo
        col_e = int(300 * k)
        folga = int(30 * k)
        col_d = pw - pad * 2 - col_e - folga
        x_e = pad
        x_d = pad + col_e + folga
        fim_y = ph - int(22 * k)
        disp = fim_y - y0

        # divisória vertical que some nas pontas
        xdiv = pad + col_e + folga // 2
        for y in range(y0, fim_y, 3):
            f = (y - y0) / max(1, fim_y - y0)
            a = int(130 * math.sin(math.pi * f))
            pygame.draw.line(s, (177, 139, 83, a),
                             (xdiv, y), (xdiv, y + 3), 1)

        cor_corpo = (214, 207, 197)

        # ---------- coluna esquerda: controles ----------
        y = y0
        y += self._cabecalho(s, "CONTROLES BÁSICOS", x_e, y, col_e)
        y += int(8 * k)

        alt_chip = int(26 * k)
        passo = int(56 * k)

        for partes, desc in self.CONTROLES:
            cx = x_e

            for tipo, txt in partes:
                if tipo == "k":
                    cx += self._chip(s, txt, cx, y, alt_chip) + int(5 * k)
                else:
                    img = self.fonte_desc.render(txt, True, self.cinza)
                    s.blit(img, (cx + int(4 * k),
                                 y + (alt_chip - img.get_height()) // 2))
                    cx += img.get_width() + int(13 * k)

            self._texto_esq(
                s, desc, self.fonte_desc, cor_corpo,
                x_e + int(2 * k), y + alt_chip + int(6 * k)
            )

            y += passo

        # ---------- coluna direita: aventura e objetivo ----------
        cab = int(28 * k) + int(6 * k)
        entre = int(14 * k)

        for tam in range(int(21 * k), int(13 * k), -1):
            fonte = self._carregar_fonte(
                self.pasta_fontes, "CormorantGaramond-Medium.ttf", tam
            )
            alt_linha = int(fonte.get_linesize() * 0.98)

            ls1 = self._quebrar_linhas(self.TEXTO_SOBRE, fonte, col_d)
            ls2 = self._quebrar_linhas(self.TEXTO_OBJETIVO, fonte, col_d)

            total = cab * 2 + entre + (len(ls1) + len(ls2)) * alt_linha

            if total <= disp:
                break

        y = y0
        y += self._cabecalho(s, "SOBRE A AVENTURA", x_d, y, col_d)
        y += int(6 * k)

        for linha in ls1:
            self._texto_esq(s, linha, fonte, cor_corpo, x_d, y)
            y += alt_linha

        y += entre
        y += self._cabecalho(s, "SEU OBJETIVO", x_d, y, col_d)
        y += int(6 * k)

        for linha in ls2:
            self._texto_esq(s, linha, fonte, cor_corpo, x_d, y)
            y += alt_linha

        self.painel_como = s

    def _conteudo_como_jogar(self, alvo):
        A = self.altura
        k = self.k

        alvo.blit(self.painel_como, self.painel_como_rect)

        self._desenhar_titulo(alvo, self.titulo_como,
                              (self.centro, int(A * 0.145)))

        self._desenhar_ornamento(
            alvo, self.centro, int(A * 0.205), int(190 * k)
        )

        self._desenhar_botao(
            alvo, "VOLTAR", self.botao_voltar, self.hover["VOLTAR"], 1.0
        )

    # =====================================================
    # AÇÕES
    # =====================================================

    def _iniciar(self, numero):
        from cenas.fase import Fase

        self.jogo.habilidades.clear()
        self.jogo.trocar_cena(Fase(self.jogo, numero))

    def _agendar(self, acao):
        self._acao_pendente = acao
        self._fade_saida = 0.0

    def _mudar_tela(self, nome):
        self.tela_atual = nome
        self.tempo_tela = 0.0

    def _ativar(self, nome):
        if nome == "JOGAR":
            self._agendar(lambda: self._iniciar(1))

        elif nome == "COMO JOGAR":
            self._mudar_tela("como_jogar")

        elif nome == "CRÉDITOS":
            self._mudar_tela("creditos")

        elif nome == "SAIR":
            self._agendar(self.jogo.sair)

    # =====================================================
    # EVENTOS
    # =====================================================

    def eventos(self, eventos):
        if self._acao_pendente:
            return

        for e in eventos:

            if e.type == pygame.KEYDOWN:

                if self.tela_atual != "menu":
                    if e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE,
                                 pygame.K_RETURN, pygame.K_SPACE):
                        self._mudar_tela("menu")

                else:
                    if e.key in (pygame.K_UP, pygame.K_w):
                        self.selecionado = (self.selecionado - 1) % len(self.nomes)

                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        self.selecionado = (self.selecionado + 1) % len(self.nomes)

                    elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                   pygame.K_SPACE):
                        self._ativar(self.nomes[self.selecionado])

                    elif e.key == pygame.K_2:
                        # atalho de desenvolvimento (sem texto na tela)
                        self._agendar(lambda: self._iniciar(2))

                    elif e.key == pygame.K_ESCAPE:
                        self._agendar(self.jogo.sair)

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:

                if self.tela_atual == "menu":
                    for i, nome in enumerate(self.nomes):
                        if self.botoes[nome].collidepoint(e.pos):
                            self.selecionado = i
                            self._ativar(nome)
                            break

                elif self.botao_voltar.collidepoint(e.pos):
                    self._mudar_tela("menu")

    # =====================================================
    # ATUALIZAÇÃO
    # =====================================================

    def atualizar(self, dt):
        self.tempo += dt
        self.tempo_tela += dt

        L, A = self.largura, self.altura

        # partículas
        for p in self.particulas:
            p["y"] -= p["vel"] * dt

            if p["y"] < -20:
                p["y"] = A + 20
                p["x"] = random.uniform(0, L)

        # névoa
        for n in self.nevoas:
            n["x"] += n["vel"] * dt

            if n["x"] > L:
                n["x"] = -n["w"]

        # mouse: só muda a seleção se o mouse realmente se moveu,
        # assim o teclado continua funcionando com o mouse parado
        mouse = pygame.mouse.get_pos()

        if mouse != self._ultimo_mouse:
            self._ultimo_mouse = mouse

            if self.tela_atual == "menu":
                for i, nome in enumerate(self.nomes):
                    if self.botoes[nome].collidepoint(mouse):
                        self.selecionado = i

        # animação suave dos botões
        suavizar = min(1.0, dt * 12)

        for i, nome in enumerate(self.nomes):
            alvo = 1.0 if (self.tela_atual == "menu"
                           and i == self.selecionado) else 0.0
            self.hover[nome] += (alvo - self.hover[nome]) * suavizar

        alvo = 1.0 if (self.tela_atual != "menu"
                       and self.botao_voltar.collidepoint(mouse)) else 0.0
        self.hover["VOLTAR"] += (alvo - self.hover["VOLTAR"]) * suavizar

        # ação agendada (fade-out antes de trocar de cena)
        if self._acao_pendente:
            self._fade_saida += dt

            if self._fade_saida >= self.DURACAO_SAIDA:
                acao = self._acao_pendente
                self._acao_pendente = None
                acao()

    # =====================================================
    # DESENHO PRINCIPAL
    # =====================================================

    def desenhar(self, tela):

        self._desenhar_fundo(tela)
        self._desenhar_raios(tela)
        self._desenhar_nevoa(tela)
        self._desenhar_particulas(tela)

        # conteúdo com fade ao trocar de tela
        alpha_tela = _limitar(self.tempo_tela / 0.45)

        if alpha_tela < 1:
            self._camada.fill((0, 0, 0, 0))
            alvo = self._camada
        else:
            alvo = tela

        if self.tela_atual == "menu":
            self._conteudo_menu(alvo)
        elif self.tela_atual == "como_jogar":
            self._conteudo_como_jogar(alvo)
        elif self.tela_atual == "creditos":
            self._conteudo_secundario(
                alvo, self.titulo_creditos,
                [
                    ("Uma aventura criada por nossa equipe",
                     self.fonte_secundaria, self.branco, 0.42),
                    ("FALLING IN FEARS",
                     self.fonte_subtitulo, self.cinza, 0.52),
                ]
            )

        if alpha_tela < 1:
            self._camada.set_alpha(int(255 * alpha_tela))
            tela.blit(self._camada, (0, 0))

        self._desenhar_moldura(tela)
        tela.blit(self.vinheta, (0, 0))

        # fades (entrada e saída)
        entrada = 1 - _limitar(self.tempo / self.DURACAO_ENTRADA)
        saida = _limitar(self._fade_saida / self.DURACAO_SAIDA) \
            if self._acao_pendente else 0.0

        escuro = max(entrada, saida)

        if escuro > 0:
            self.cortina.set_alpha(int(255 * escuro))
            tela.blit(self.cortina, (0, 0))

    # =====================================================
    # FUNDO E EFEITOS
    # =====================================================

    def _desenhar_fundo(self, tela):
        fw, fh = self.fundo.get_size()
        extra_x = max(0, fw - self.largura)
        extra_y = max(0, fh - self.altura)

        # movimento lento de câmera (efeito "respirando")
        ox = int(extra_x * (0.5 + 0.5 * math.sin(self.tempo * 0.12)))
        oy = int(extra_y * (0.5 + 0.5 * math.sin(self.tempo * 0.09 + 1.3)))

        tela.blit(self.fundo, (-ox, -oy))
        tela.blit(self.escurecer, (0, 0))

    def _desenhar_raios(self, tela):
        pulso = 0.6 + 0.4 * math.sin(self.tempo * 0.7)
        self.raios.set_alpha(int(255 * pulso))
        tela.blit(self.raios, (0, 0))

    def _desenhar_nevoa(self, tela):
        for n in self.nevoas:
            tela.blit(n["surf"], (int(n["x"]), n["y"]))

    def _desenhar_particulas(self, tela):
        t = self.tempo

        for p in self.particulas:
            x = p["x"] + math.sin(t * 0.8 + p["fase"]) * p["deriva"]
            y = p["y"]

            nivel = int((0.5 + 0.5 * math.sin(t * 2.2 + p["fase"])) * 3.99)

            sprite = self.sprites[(p["cor"], p["raio"], nivel)]

            tela.blit(
                sprite,
                (int(x) - sprite.get_width() // 2,
                 int(y) - sprite.get_height() // 2),
                special_flags=pygame.BLEND_RGB_ADD
            )

    # =====================================================
    # MOLDURA (mesma linguagem visual da introdução)
    # =====================================================

    def _desenhar_moldura(self, tela):
        mx = int(self.largura * 0.044)
        my = int(self.altura * 0.065)

        r = pygame.Rect(mx, my, self.largura - mx * 2, self.altura - my * 2)

        pygame.draw.rect(tela, (145, 110, 67), r, 1)

        comp = int(26 * self.k)

        cantos = [
            (r.left, r.top, 1, 1),
            (r.right - 1, r.top, -1, 1),
            (r.left, r.bottom - 1, 1, -1),
            (r.right - 1, r.bottom - 1, -1, -1),
        ]

        for i, (x, y, dx, dy) in enumerate(cantos):
            pygame.draw.line(
                tela, self.dourado_claro, (x, y), (x + comp * dx, y), 2
            )
            pygame.draw.line(
                tela, self.dourado_claro, (x, y), (x, y + comp * dy), 2
            )

            brilho = 0.5 + 0.5 * math.sin(self.tempo * 2 + i * 1.3)
            cor = _lerp_cor(self.dourado, self.dourado_vivo, brilho)
            pygame.draw.circle(
                tela, cor, (x + 7 * dx, y + 7 * dy),
                max(2, int(3 * self.k))
            )

    # =====================================================
    # TÍTULO
    # =====================================================

    def _desenhar_titulo(self, alvo, dados, centro, shimmer=True):
        W, H = dados["tam"]
        x = centro[0] - W // 2
        y = centro[1] - H // 2

        # glow pulsante
        pulso = 0.60 + 0.40 * math.sin(self.tempo * 1.7)
        dados["glow"].set_alpha(int(255 * pulso))
        alvo.blit(dados["glow"], (x, y))
        alvo.blit(dados["glow"], (x, y))

        alvo.blit(dados["final"], (x, y))

        # faixa de luz que atravessa as letras
        if shimmer:
            fase = ((self.tempo + dados["atraso"]) % 6.5) / 1.5

            if fase < 1:
                faixa = dados["faixa"]
                fx = int(-faixa.get_width() + fase * (W + faixa.get_width()))

                temp = pygame.Surface((W, H), pygame.SRCALPHA)
                temp.blit(faixa, (fx, 0))
                temp.blit(
                    dados["mascara"], (0, 0),
                    special_flags=pygame.BLEND_RGBA_MULT
                )
                alvo.blit(temp, (x, y))

    # =====================================================
    # ORNAMENTO
    # =====================================================

    def _desenhar_ornamento(self, alvo, cx, y, meia_largura):
        k = self.k
        gap = int(16 * k)
        seg = 28

        for i in range(seg):
            f0 = i / seg
            f1 = (i + 1) / seg

            x0 = int(gap + f0 * (meia_largura - gap))
            x1 = int(gap + f1 * (meia_largura - gap))

            cor = _lerp_cor(self.dourado, (45, 34, 42), f0 ** 0.8)

            pygame.draw.line(alvo, cor, (cx - x1, y), (cx - x0, y), 1)
            pygame.draw.line(alvo, cor, (cx + x0, y), (cx + x1, y), 1)

        pulso = 0.5 + 0.5 * math.sin(self.tempo * 2.2)

        # brilho do losango central
        self.halo_ornamento.set_alpha(int(110 + 145 * pulso))
        alvo.blit(
            self.halo_ornamento,
            self.halo_ornamento.get_rect(center=(cx, y))
        )

        s = int(7 * k + pulso * 1.5)
        pygame.draw.polygon(
            alvo, self.dourado_vivo,
            [(cx, y - s), (cx + s, y), (cx, y + s), (cx - s, y)]
        )

        s2 = max(2, s - 4)
        pygame.draw.polygon(
            alvo, (40, 26, 20),
            [(cx, y - s2), (cx + s2, y), (cx, y + s2), (cx - s2, y)]
        )

        # losangos pequenos nas laterais
        for lado in (-1, 1):
            px = cx + lado * (gap + int(11 * k))
            m = max(2, int(3 * k))
            pygame.draw.polygon(
                alvo, self.dourado,
                [(px, y - m), (px + m, y), (px, y + m), (px - m, y)]
            )

    # =====================================================
    # TEXTO
    # =====================================================

    def _texto(self, alvo, texto, fonte, cor, centro, alpha=255,
               sombra=True):
        if alpha <= 0:
            return

        if sombra:
            s = fonte.render(texto, True, (0, 0, 0))
            if alpha < 255:
                s.set_alpha(alpha)
            alvo.blit(s, s.get_rect(center=(centro[0] + 2, centro[1] + 3)))

        img = fonte.render(texto, True, cor)
        if alpha < 255:
            img.set_alpha(alpha)
        alvo.blit(img, img.get_rect(center=centro))

    # =====================================================
    # MENU PRINCIPAL
    # =====================================================

    def _conteudo_menu(self, alvo):
        A = self.altura
        k = self.k
        tt = self.tempo_tela

        # sombra suave atrás do título
        alvo.blit(
            self.halo_escuro,
            self.halo_escuro.get_rect(center=(self.centro, int(A * 0.34)))
        )

        # título "cai" suavemente para o lugar e depois flutua
        e = _limitar((tt - 0.1) / 1.3)
        ease = 1 - (1 - e) ** 3
        queda = -int((1 - ease) * 55 * k)
        flutuar = int(math.sin(self.tempo * 0.9) * 3 * k)

        self._desenhar_titulo(
            alvo, self.titulo_principal,
            (self.centro, int(A * 0.19) + queda + flutuar)
        )

        # ornamento + subtítulo
        alpha_sub = int(255 * _limitar((tt - 0.9) / 0.8))

        self._desenhar_ornamento(
            alvo, self.centro, int(A * 0.275), int(190 * k)
        )

        self._texto(
            alvo, "Uma jornada entre os medos",
            self.fonte_subtitulo, self.branco,
            (self.centro, int(A * 0.328)), alpha_sub
        )

        # botões (entram um após o outro)
        for i, nome in enumerate(self.nomes):
            ap = _limitar((tt - 0.55 - i * 0.12) / 0.5)

            if ap > 0:
                self._desenhar_botao(
                    alvo, nome, self.botoes[nome], self.hover[nome], ap
                )

        # dica discreta de controles
        if tt > 1.6:
            pulso = int(150 + 60 * abs(math.sin(self.tempo * 2)))
            self._texto(
                alvo, "Setas para navegar   ·   ENTER para confirmar",
                self.fonte_pequena, (195, 180, 150),
                (self.centro, int(A * 0.925)), pulso
            )

    # =====================================================
    # TELAS SECUNDÁRIAS
    # =====================================================

    def _conteudo_secundario(self, alvo, titulo, linhas):
        A = self.altura
        k = self.k

        alvo.blit(self.painel_sec, self.painel_rect)

        self._desenhar_titulo(alvo, titulo, (self.centro, int(A * 0.225)))

        self._desenhar_ornamento(
            alvo, self.centro, int(A * 0.315), int(170 * k)
        )

        for texto, fonte, cor, y in linhas:
            self._texto(alvo, texto, fonte, cor, (self.centro, int(A * y)))

        self._desenhar_botao(
            alvo, "VOLTAR", self.botao_voltar, self.hover["VOLTAR"], 1.0
        )

    # =====================================================
    # BOTÕES
    # =====================================================

    def _desenhar_botao(self, alvo, texto, rect, hover, ap=1.0):
        if ap < 1:
            pad = int(40 * self.k)
            temp = pygame.Surface(
                (rect.w + pad * 2, rect.h + pad * 2), pygame.SRCALPHA
            )
            local = pygame.Rect(pad, pad, rect.w, rect.h)

            self._corpo_botao(temp, texto, local, hover)

            temp.set_alpha(int(255 * ap))
            deslocamento = int((1 - ap) * 16 * self.k)
            alvo.blit(temp, (rect.x - pad, rect.y - pad + deslocamento))
        else:
            self._corpo_botao(alvo, texto, rect, hover)

    def _corpo_botao(self, alvo, texto, r, h):
        k = self.k

        # brilho atrás do botão selecionado
        if h > 0.02:
            self.glow_botao.set_alpha(int(255 * h))
            alvo.blit(
                self.glow_botao,
                self.glow_botao.get_rect(center=r.center)
            )

        # fundo
        alvo.blit(self.bt_normal, r.topleft)

        if h > 0.02:
            self.bt_hover.set_alpha(int(255 * h))
            alvo.blit(self.bt_hover, r.topleft)

        # bordas
        cor_borda = _lerp_cor((150, 111, 67), self.dourado_vivo, h)
        pygame.draw.rect(alvo, cor_borda, r, 2, border_radius=7)

        cor_interna = _lerp_cor((70, 52, 45), (176, 134, 80), h)
        pygame.draw.rect(alvo, cor_interna, r.inflate(-12, -12), 1,
                         border_radius=5)

        # linha que se abre sob o texto
        if h > 0.02:
            meia = int(h * r.w * 0.30)
            y = r.bottom - int(9 * k)
            pygame.draw.line(
                alvo, self.dourado_claro,
                (r.centerx - meia, y), (r.centerx + meia, y), 1
            )

        # texto
        cor_texto = _lerp_cor(self.branco, self.dourado_vivo, h)
        self._texto(alvo, texto, self.fonte_botao, cor_texto, r.center)

        # ornamentos laterais
        for lado in (-1, 1):
            ponto_x = r.centerx + lado * (r.w // 2 - int(18 * k))
            m = max(2, int(3 * k + h * 2))
            cor = _lerp_cor(self.dourado, self.dourado_vivo, h)

            pygame.draw.polygon(
                alvo, cor,
                [(ponto_x, r.centery - m), (ponto_x + m, r.centery),
                 (ponto_x, r.centery + m), (ponto_x - m, r.centery)]
            )

            # "lâmina" que sai das laterais quando o botão está ativo
            comp = int(h * 38 * k)

            if comp > 3:
                inicio = r.centerx + lado * (r.w // 2 + int(8 * k))
                fim = inicio + lado * comp

                pygame.draw.line(
                    alvo, self.dourado_claro,
                    (inicio, r.centery), (fim, r.centery), 2
                )

                ponta = max(2, int(3 * k))
                pygame.draw.polygon(
                    alvo, self.dourado_vivo,
                    [(fim + lado * ponta, r.centery),
                     (fim, r.centery - ponta),
                     (fim - lado * ponta, r.centery),
                     (fim, r.centery + ponta)]
                )