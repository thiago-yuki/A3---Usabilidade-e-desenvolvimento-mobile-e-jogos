
import pygame
import os
import math
import random
from nucleo.cena import Cena

class Introducao(Cena):

    def __init__(self, jogo):
        super().__init__(jogo)
        self.jogo.iniciar_musica_menu()

        self.LARGURA = 960
        self.ALTURA = 540

        self.tempo = 0
        self.pagina_atual = 0
        self.transicao = 0
        self.trocando_pagina = False
        self.duracao_transicao = 0.45

        # CORES
        self.dourado = (177, 139, 83)
        self.dourado_claro = (226, 195, 137)
        self.marfin = (225, 220, 210)

        # FONTES
        BASE_DIR = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        pasta_fontes = os.path.join(
            BASE_DIR, "assets", "fontes"
        )

        self.fonte_marca = pygame.font.Font(
            os.path.join(pasta_fontes, "Cinzel-Regular.ttf"), 16
        )

        self.fonte_titulo = pygame.font.Font(
            os.path.join(pasta_fontes, "Cinzel-Bold.ttf"), 43
        )

        self.fonte_texto = pygame.font.Font(
            os.path.join(pasta_fontes, "CormorantGaramond-Medium.ttf"), 32
        )

        self.fonte_frase = pygame.font.Font(
            os.path.join(pasta_fontes, "CormorantGaramond-Italic.ttf"), 23
        )

        self.fonte_pagina = pygame.font.Font(
            os.path.join(pasta_fontes, "Cinzel-Regular.ttf"), 14
        )

        # IMAGEM DE FUNDO
        nome_imagem = "fundo_introducao.jfif"
        caminho_imagem = None

        pasta_busca = os.path.dirname(BASE_DIR)

        for raiz, pastas, arquivos in os.walk(pasta_busca):
            for arquivo in arquivos:
                if arquivo.lower() == nome_imagem.lower():
                    caminho_imagem = os.path.join(raiz, arquivo)
                    break

            if caminho_imagem:
                break

        if caminho_imagem is None:
            raise FileNotFoundError(
                "A imagem fundo_introducao.jfif não foi encontrada."
            )

        self.fundo = pygame.image.load(
            caminho_imagem
        ).convert()

        self.fundo = pygame.transform.scale(
            self.fundo,
            (self.LARGURA, self.ALTURA)
        )

        # HISTÓRIA E APRESENTAÇÃO DOS INIMIGOS
        # Formato: título, texto, tipo de cenário

        self.cenas = [

            (
                "UM REINO DISTANTE",
                "Em um reino distante, duas almas construíram\n"
                "uma história de amor que parecia não ter fim.",
                "normal"
            ),

            (
                "O DESAPARECIMENTO",
                "Mas, em uma noite misteriosa, a princesa\n"
                "desapareceu. E tudo o que restou foi o vazio\n"
                "de quem ela mais amava.",
                "normal"
            ),

            (
                "A GUERREIRA",
                "Determinada a reencontrá-la, uma guerreira\n"
                "parte em uma jornada por terras desconhecidas,\n"
                "sem imaginar os perigos que a aguardam.",
                "normal"
            ),

            (
                "SAPOS RAIVOSOS",
                "Nas águas de um lago sombrio, pequenos sapos\n"
                "vermelhos e furiosos aguardam a guerreira.\n"
                "Não subestime sua aparência!",
                "sapos"
            ),

            (
                "FANTASMAS CINZENTOS",
                "Entre túmulos esquecidos, espíritos cinzentos\n"
                "vagam sem descanso. Suas formas flutuantes\n"
                "escondem perigos inesperados.",
                "fantasmas"
            ),

            (
                "ZUMBIS DA FLORESTA",
                "Na floresta assombrada, criaturas verdes\n"
                "emergem das sombras. A guerreira precisará\n"
                "enfrentar os mortos que voltaram à vida.",
                "zumbis"
            ),

            (
                "O ÚLTIMO DESAFIO",
                "No fim da jornada, um enorme dragão estará\n"
                "entre ela e o reencontro com seu grande amor.\n"
                "Todas as ameaças se encontram em uma só criatura.",
                "dragao"
            )
        ]

        # PARTÍCULAS
        self.particulas = []

        for i in range(65):
            self.particulas.append({
                "x": random.randint(0, 960),
                "y": random.randint(0, 540),
                "vel": random.uniform(12, 40),
                "tamanho": random.randint(1, 3),
                "fase": random.uniform(0, 6.28)
            })

        # NÉVOA
        self.nevoas = []

        for i in range(8):
            self.nevoas.append({
                "x": random.randint(-300, 960),
                "y": random.randint(350, 510),
                "vel": random.uniform(8, 20),
                "largura": random.randint(180, 320),
                "altura": random.randint(35, 65)
            })

        # VINHETA
        self.vinheta = pygame.Surface(
            (960, 540), pygame.SRCALPHA
        )

        for i in range(10):
            pygame.draw.rect(
                self.vinheta,
                (0, 0, 0, 12 + i * 5),
                (
                    i * 22,
                    i * 17,
                    960 - i * 44,
                    540 - i * 34
                ),
                width=25
            )

    # ==========================================
    # EVENTOS
    # ==========================================

    def eventos(self, eventos):

        for evento in eventos:

            if evento.type == pygame.KEYDOWN:

                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.avancar()

                elif evento.key == pygame.K_ESCAPE:
                    self.ir_para_menu()

            if evento.type == pygame.MOUSEBUTTONDOWN:

                if evento.button == 1:
                    self.avancar()

    def avancar(self):

        if self.trocando_pagina:
            return

        self.trocando_pagina = True
        self.transicao = self.duracao_transicao

    def ir_para_menu(self):

        from cenas.menu import Menu
        self.jogo.trocar_cena(Menu(self.jogo))

    # ==========================================
    # ATUALIZAÇÃO
    # ==========================================

    def atualizar(self, dt):

        self.tempo += dt

        for p in self.particulas:

            p["y"] -= p["vel"] * dt

            p["x"] += math.sin(
                self.tempo + p["fase"]
            ) * 10 * dt

            if p["y"] < -10:
                p["y"] = 550
                p["x"] = random.randint(0, 960)

        for n in self.nevoas:

            n["x"] += n["vel"] * dt

            if n["x"] > 1100:
                n["x"] = -n["largura"]

        if self.trocando_pagina:

            self.transicao -= dt

            if self.transicao <= 0:

                self.pagina_atual += 1

                if self.pagina_atual >= len(self.cenas):
                    self.ir_para_menu()
                    return

                self.transicao = 0
                self.trocando_pagina = False

    # ==========================================
    # NÉVOA
    # ==========================================

    def desenhar_nevoa(self, tela):

        camada = pygame.Surface(
            (960, 540), pygame.SRCALPHA
        )

        for n in self.nevoas:

            pygame.draw.ellipse(
                camada,
                (145, 150, 165, 25),
                (
                    int(n["x"]),
                    int(n["y"]),
                    n["largura"],
                    n["altura"]
                )
            )

        tela.blit(camada, (0, 0))

    # ==========================================
    # PARTÍCULAS
    # ==========================================

    def desenhar_particulas(self, tela):

        camada = pygame.Surface(
            (960, 540), pygame.SRCALPHA
        )

        for p in self.particulas:

            brilho = int(
                100 + 100 * abs(
                    math.sin(self.tempo * 2 + p["fase"])
                )
            )

            pygame.draw.circle(
                camada,
                (220, 160, 75, brilho),
                (int(p["x"]), int(p["y"])),
                p["tamanho"]
            )

        tela.blit(camada, (0, 0))

    # ==========================================
    # DESENHO DOS INIMIGOS
    # ==========================================

    def desenhar_sapo(self, tela, x, y, escala=1):

        s = escala

        # Corpo
        pygame.draw.ellipse(
            tela, (155, 35, 43),
            (int(x), int(y + 15*s), int(48*s), int(32*s))
        )

        # Cabeça
        pygame.draw.circle(
            tela, (190, 48, 48),
            (int(x + 24*s), int(y + 17*s)),
            int(20*s)
        )

        # Olhos
        for olho in [12, 36]:

            pygame.draw.circle(
                tela, (220, 190, 140),
                (int(x + olho*s), int(y + 5*s)),
                int(7*s)
            )

            pygame.draw.circle(
                tela, (20, 15, 15),
                (int(x + olho*s), int(y + 5*s)),
                int(3*s)
            )

        # Boca
        pygame.draw.arc(
            tela, (40, 10, 10),
            (
                int(x + 14*s),
                int(y + 17*s),
                int(20*s),
                int(13*s)
            ),
            3.2, 6.1, max(1, int(2*s))
        )

        # Pernas
        pygame.draw.line(
            tela, (115, 25, 32),
            (int(x + 10*s), int(y + 38*s)),
            (int(x + 2*s), int(y + 49*s)),
            max(2, int(5*s))
        )

        pygame.draw.line(
            tela, (115, 25, 32),
            (int(x + 38*s), int(y + 38*s)),
            (int(x + 46*s), int(y + 49*s)),
            max(2, int(5*s))
        )

        # Pequeno elmo medieval
        pygame.draw.polygon(
            tela, (105, 105, 115),
            [
                (int(x + 9*s), int(y + 3*s)),
                (int(x + 24*s), int(y - 10*s)),
                (int(x + 39*s), int(y + 3*s))
            ]
        )

        pygame.draw.line(
            tela, (210, 180, 110),
            (int(x + 9*s), int(y + 3*s)),
            (int(x + 39*s), int(y + 3*s)),
            max(1, int(2*s))
        )

    def desenhar_fantasma(self, tela, x, y, escala=1):

        s = escala

        cor = (145, 150, 160)
        clara = (205, 205, 210)

        # Corpo
        pygame.draw.circle(
            tela, cor,
            (int(x + 25*s), int(y + 18*s)),
            int(23*s)
        )

        pygame.draw.rect(
            tela, cor,
            (
                int(x + 2*s),
                int(y + 17*s),
                int(46*s),
                int(25*s)
            )
        )

        # Base ondulada
        pygame.draw.polygon(
            tela, cor,
            [
                (int(x + 2*s), int(y + 35*s)),
                (int(x + 12*s), int(y + 43*s)),
                (int(x + 23*s), int(y + 35*s)),
                (int(x + 35*s), int(y + 43*s)),
                (int(x + 48*s), int(y + 35*s)),
                (int(x + 48*s), int(y + 43*s)),
                (int(x + 2*s), int(y + 43*s))
            ]
        )

        # Olhos
        for olho in [17, 34]:

            pygame.draw.ellipse(
                tela, (35, 35, 45),
                (
                    int(x + olho*s - 4*s),
                    int(y + 15*s),
                    int(8*s),
                    int(13*s)
                )
            )

        pygame.draw.circle(
            tela, clara,
            (int(x + 25*s), int(y + 2*s)),
            max(1, int(2*s))
        )

    def desenhar_zumbi(self, tela, x, y, escala=1):

        s = escala

        verde = (70, 120, 62)
        escuro = (35, 70, 40)

        # Corpo
        pygame.draw.rect(
            tela, escuro,
            (
                int(x + 9*s),
                int(y + 25*s),
                int(32*s),
                int(35*s)
            )
        )

        # Cabeça
        pygame.draw.rect(
            tela, verde,
            (
                int(x + 7*s),
                int(y),
                int(36*s),
                int(32*s)
            ),
            border_radius=max(1, int(5*s))
        )

        # Olhos
        pygame.draw.circle(
            tela, (210, 190, 90),
            (int(x + 17*s), int(y + 13*s)),
            max(1, int(4*s))
        )

        pygame.draw.circle(
            tela, (210, 190, 90),
            (int(x + 34*s), int(y + 13*s)),
            max(1, int(4*s))
        )

        # Boca
        pygame.draw.line(
            tela, (25, 35, 20),
            (int(x + 17*s), int(y + 25*s)),
            (int(x + 34*s), int(y + 25*s)),
            max(1, int(3*s))
        )

        # Braços
        pygame.draw.line(
            tela, verde,
            (int(x + 10*s), int(y + 32*s)),
            (int(x - 4*s), int(y + 45*s)),
            max(2, int(7*s))
        )

        pygame.draw.line(
            tela, verde,
            (int(x + 40*s), int(y + 32*s)),
            (int(x + 54*s), int(y + 43*s)),
            max(2, int(7*s))
        )

        # Pernas
        pygame.draw.line(
            tela, escuro,
            (int(x + 17*s), int(y + 58*s)),
            (int(x + 12*s), int(y + 73*s)),
            max(2, int(7*s))
        )

        pygame.draw.line(
            tela, escuro,
            (int(x + 33*s), int(y + 58*s)),
            (int(x + 38*s), int(y + 73*s)),
            max(2, int(7*s))
        )

    def desenhar_dragao(self, tela, x, y, escala=1):

        s = escala

        vermelho = (105, 30, 35)
        cinza = (100, 105, 115)
        verde = (55, 95, 55)

        # Asas
        pygame.draw.polygon(
            tela, cinza,
            [
                (int(x + 55*s), int(y + 60*s)),
                (int(x + 5*s), int(y)),
                (int(x + 15*s), int(y + 90*s)),
                (int(x + 60*s), int(y + 105*s))
            ]
        )

        pygame.draw.polygon(
            tela, verde,
            [
                (int(x + 100*s), int(y + 60*s)),
                (int(x + 155*s), int(y)),
                (int(x + 145*s), int(y + 90*s)),
                (int(x + 100*s), int(y + 105*s))
            ]
        )

        # Corpo
        pygame.draw.ellipse(
            tela, vermelho,
            (
                int(x + 38*s),
                int(y + 55*s),
                int(85*s),
                int(65*s)
            )
        )

        # Pescoço
        pygame.draw.polygon(
            tela, vermelho,
            [
                (int(x + 90*s), int(y + 65*s)),
                (int(x + 115*s), int(y + 20*s)),
                (int(x + 135*s), int(y + 45*s)),
                (int(x + 118*s), int(y + 100*s))
            ]
        )

        # Cabeça
        pygame.draw.circle(
            tela, vermelho,
            (int(x + 135*s), int(y + 32*s)),
            int(22*s)
        )

        # Chifres
        pygame.draw.polygon(
            tela, cinza,
            [
                (int(x + 120*s), int(y + 17*s)),
                (int(x + 112*s), int(y - 5*s)),
                (int(x + 132*s), int(y + 15*s))
            ]
        )

        pygame.draw.polygon(
            tela, cinza,
            [
                (int(x + 145*s), int(y + 17*s)),
                (int(x + 158*s), int(y - 5*s)),
                (int(x + 150*s), int(y + 25*s))
            ]
        )

        # Olho
        pygame.draw.circle(
            tela, (255, 190, 65),
            (int(x + 144*s), int(y + 29*s)),
            max(2, int(5*s))
        )

        # Cauda
        pygame.draw.polygon(
            tela, verde,
            [
                (int(x + 45*s), int(y + 90*s)),
                (int(x + 5*s), int(y + 120*s)),
                (int(x + 60*s), int(y + 108*s))
            ]
        )

        # Patas
        pygame.draw.circle(
            tela, cinza,
            (int(x + 58*s), int(y + 117*s)),
            max(2, int(8*s))
        )

        pygame.draw.circle(
            tela, cinza,
            (int(x + 105*s), int(y + 117*s)),
            max(2, int(8*s))
        )

    # ==========================================
    # ANIMAÇÃO DOS INIMIGOS POR PÁGINA
    # ==========================================

    def desenhar_inimigos(self, tela):

        tipo = self.cenas[self.pagina_atual][2]

        camada = pygame.Surface(
            (960, 540),
            pygame.SRCALPHA
        )

        # Sapos vermelhos caindo
        if tipo == "sapos":

            for i in range(7):

                x = 70 + i * 125

                y = (
                    self.tempo * (75 + i * 8)
                    + i * 95
                ) % 650 - 60

                x += math.sin(self.tempo * 2 + i) * 20

                self.desenhar_sapo(
                    camada,
                    int(x),
                    int(y),
                    0.75 + (i % 3) * 0.15
                )

        # Fantasmas flutuando
        elif tipo == "fantasmas":

            for i in range(7):

                x = 65 + i * 130

                y = (
                    self.tempo * (45 + i * 5)
                    + i * 105
                ) % 650 - 70

                x += math.sin(self.tempo * 1.8 + i) * 28

                self.desenhar_fantasma(
                    camada,
                    int(x),
                    int(y),
                    0.8 + (i % 3) * 0.15
                )

        # Zumbis caindo
        elif tipo == "zumbis":

            for i in range(7):

                x = 55 + i * 130

                y = (
                    self.tempo * (55 + i * 7)
                    + i * 100
                ) % 680 - 80

                x += math.sin(self.tempo * 2 + i) * 15

                self.desenhar_zumbi(
                    camada,
                    int(x),
                    int(y),
                    0.7 + (i % 3) * 0.12
                )

        # Dragão final
        elif tipo == "dragao":

            pulsacao = math.sin(self.tempo * 2) * 8

            self.desenhar_dragao(
                camada,
                665,
                int(160 + pulsacao),
                1.35
            )

        # Transparência dos inimigos
        camada.set_alpha(165)

        tela.blit(camada, (0, 0))

    # ==========================================
    # MOLDURA E PAINEL
    # ==========================================

    def desenhar_moldura(self, tela):

        cor = (145, 110, 67)

        pygame.draw.rect(
            tela,
            cor,
            (42, 35, 876, 470),
            1
        )

        cantos = [
            (42, 35, 1, 1),
            (918, 35, -1, 1),
            (42, 505, 1, -1),
            (918, 505, -1, -1)
        ]

        for x, y, dx, dy in cantos:

            pygame.draw.line(
                tela, self.dourado_claro,
                (x, y),
                (x + 24 * dx, y),
                2
            )

            pygame.draw.line(
                tela, self.dourado_claro,
                (x, y),
                (x, y + 24 * dy),
                2
            )

    def desenhar_painel(self, tela):

        painel = pygame.Surface(
            (720, 150),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            painel,
            (10, 10, 17, 190),
            (0, 0, 720, 150),
            border_radius=10
        )

        pygame.draw.rect(
            painel,
            (145, 110, 67, 175),
            (0, 0, 720, 150),
            1,
            border_radius=10
        )

        tela.blit(painel, (120, 270))

    # ==========================================
    # TEXTO
    # ==========================================

    def desenhar_texto(
        self, tela, fonte, texto, cor, centro, alpha=255
    ):

        sombra = fonte.render(
            texto, True, (0, 0, 0)
        )

        sombra.set_alpha(alpha)

        tela.blit(
            sombra,
            sombra.get_rect(
                center=(centro[0] + 2, centro[1] + 3)
            )
        )

        imagem = fonte.render(
            texto, True, cor
        )

        imagem.set_alpha(alpha)

        tela.blit(
            imagem,
            imagem.get_rect(center=centro)
        )

    # ==========================================
    # PROGRESSO
    # ==========================================

    def desenhar_progresso(self, tela):

        total = len(self.cenas)
        largura = 170

        preenchimento = (
            largura * (self.pagina_atual + 1) / total
        )

        pygame.draw.rect(
            tela,
            (65, 55, 45),
            (395, 465, largura, 2)
        )

        pygame.draw.rect(
            tela,
            self.dourado,
            (395, 465, int(preenchimento), 2)
        )

        numero = (
            f"{self.pagina_atual + 1:02d} / {total:02d}"
        )

        imagem = self.fonte_pagina.render(
            numero,
            True,
            self.dourado_claro
        )

        tela.blit(
            imagem,
            imagem.get_rect(center=(480, 486))
        )

    # ==========================================
    # DESENHAR INTRODUÇÃO
    # ==========================================

    def desenhar(self, tela):

        # Fundo
        tela.blit(self.fundo, (0, 0))

        # Escurecimento
        sombra = pygame.Surface(
            (960, 540), pygame.SRCALPHA
        )

        sombra.fill((0, 0, 0, 100))
        tela.blit(sombra, (0, 0))

        # Inimigos específicos da página
        self.desenhar_inimigos(tela)

        # Névoa e partículas
        self.desenhar_nevoa(tela)
        self.desenhar_particulas(tela)

        # Moldura
        self.desenhar_moldura(tela)

        # Nome do jogo
        alpha_marca = min(
            255, int(self.tempo * 150)
        )

        self.desenhar_texto(
            tela,
            self.fonte_marca,
            "F A L L I N G   I N   F E A R S",
            self.dourado_claro,
            (480, 78),
            alpha_marca
        )

        pygame.draw.line(
            tela,
            self.dourado,
            (375, 105),
            (585, 105),
            1
        )

        # Título principal
        titulo, texto, tipo = self.cenas[self.pagina_atual]

        alpha = min(
            255, int(self.tempo * 180)
        )

        if self.trocando_pagina:

            alpha = int(
                255 * max(
                    0,
                    self.transicao / self.duracao_transicao
                )
            )

        self.desenhar_texto(
            tela,
            self.fonte_titulo,
            titulo,
            self.dourado_claro,
            (480, 210),
            alpha
        )

        # Linha decorativa
        pygame.draw.line(
            tela,
            self.dourado,
            (385, 245),
            (575, 245),
            1
        )

        # Caixa menor e mais discreta
        self.desenhar_painel(tela)

        # Texto da história
        linhas = texto.split("\n")

        for i, linha in enumerate(linhas):

            if linha == "":
                continue

            self.desenhar_texto(
                tela,
                self.fonte_texto,
                linha,
                self.marfin,
                (480, 310 + i * 31),
                alpha
            )

        # Frase final menos destacada
        if tipo == "dragao":

            self.desenhar_texto(
                tela,
                self.fonte_frase,
                "Enfrentar os próprios medos também é um ato de amor.",
                (190, 165, 135),
                (480, 435),
                alpha
            )

        # Progresso
        self.desenhar_progresso(tela)

        # Instrução
        if self.tempo > 1.5 and not self.trocando_pagina:

            instrucao = self.fonte_frase.render(
                "Pressione ENTER ou clique para continuar",
                True,
                (195, 180, 150)
            )

            pulsacao = int(
                180 + 40 * abs(math.sin(self.tempo * 2))
            )

            instrucao.set_alpha(pulsacao)

            tela.blit(
                instrucao,
                instrucao.get_rect(center=(480, 518))
            )

        # Vinheta
        tela.blit(self.vinheta, (0, 0))
