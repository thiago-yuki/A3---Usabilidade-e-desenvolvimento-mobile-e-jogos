
import os
import math
import random
import pygame
import config
from nucleo.cena import Cena


class Final(Cena):
    """
    Fase 4 - O Castelo das Três Maldições.

    Camada visual da batalha final:
    fundo, névoa, brasas, esporos e iluminação ambiental.

    As mecânicas do chefão e do jogador ficam com a equipe
    responsável pela programação do gameplay.
    """

    def __init__(self, jogo, resolucao=None):
        super().__init__(jogo)
        self.largura, self.altura = resolucao or (config.LARGURA, config.ALTURA)

        # =====================================
        # FUNDO DO CASTELO
        # =====================================

        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_fundo = os.path.join(
            raiz, "assets", "fundofase4.jpeg"
        )

        self.fundo = pygame.image.load(caminho_fundo).convert()
        self.fundo = pygame.transform.smoothscale(
            self.fundo,
            (self.largura, self.altura)
        )

        # =====================================
        # CONTROLE DE ANIMAÇÃO
        # =====================================

        self.tempo = 0.0

        # =====================================
        # NÉVOA VERDE
        # =====================================

        self.nevoas = []

        for _ in range(9):
            self.nevoas.append({
                "x": random.randint(-100, self.largura),
                "y": random.randint(350, self.altura),
                "largura": random.randint(130, 260),
                "altura": random.randint(35, 75),
                "velocidade": random.uniform(15, 48),
                "alpha": random.randint(12, 28)
            })

        # =====================================
        # BRASAS VERMELHAS
        # =====================================

        self.brasas = []

        for _ in range(45):
            self.brasas.append(self._criar_brasa(True))

        # =====================================
        # ESPOROS VERDES
        # =====================================

        self.esporos = []

        for _ in range(24):
            self.esporos.append(self._criar_esporo(True))

        # =====================================
        # FUMAÇA ESCURA
        # =====================================

        self.fumacas = []

        for _ in range(7):
            self.fumacas.append({
                "x": random.randint(-100, self.largura),
                "y": random.randint(250, self.altura),
                "tamanho": random.randint(35, 80),
                "velocidade": random.uniform(8, 18),
                "alpha": random.randint(8, 17)
            })

    # =====================================
    # CRIAÇÃO DOS EFEITOS
    # =====================================

    def _criar_brasa(self, random_y=False):
        return {
            "x": random.randint(0, self.largura),
            "y": (
                random.randint(0, self.altura)
                if random_y
                else self.altura + 10
            ),
            "velocidade": random.uniform(30, 102),
            "tamanho": random.randint(2, 4),
            "oscilacao": random.uniform(0, 6.28)
        }

    def _criar_esporo(self, random_y=False):
        return {
            "x": random.randint(0, self.largura),
            "y": (
                random.randint(0, self.altura)
                if random_y
                else self.altura + 10
            ),
            "velocidade": random.uniform(18, 54),
            "tamanho": random.randint(2, 4),
            "oscilacao": random.uniform(0, 6.28)
        }

    # =====================================
    # ATUALIZAÇÃO DOS EFEITOS
    # =====================================

    def atualizar(self, dt):
        # Limita variações muito grandes entre frames.
        dt = min(dt, 0.05)

        self.tempo += dt

        # Névoa deslizando pela arena.
        for nevoa in self.nevoas:
            nevoa["x"] += nevoa["velocidade"] * dt

            if nevoa["x"] > self.largura + 150:
                nevoa["x"] = -nevoa["largura"]

        # Brasas subindo com movimento lateral.
        for brasa in self.brasas:
            brasa["y"] -= brasa["velocidade"] * dt

            brasa["x"] += math.sin(
                self.tempo * 2 + brasa["oscilacao"]
            ) * 27 * dt

            if brasa["y"] < -10:
                brasa.update(self._criar_brasa())

        # Esporos verdes flutuando.
        for esporo in self.esporos:
            esporo["y"] -= esporo["velocidade"] * dt

            esporo["x"] += math.sin(
                self.tempo * 1.5 + esporo["oscilacao"]
            ) * 36 * dt

            if esporo["y"] < -10:
                esporo.update(self._criar_esporo())

        # Fumaça escura se espalhando pelo castelo.
        for fumaca in self.fumacas:
            fumaca["x"] += fumaca["velocidade"] * dt

            if fumaca["x"] > self.largura + 100:
                fumaca["x"] = -100
                fumaca["y"] = random.randint(250, self.altura)

    # =====================================
    # DESENHO DA NÉVOA
    # =====================================

    def _desenhar_nevoa(self, tela):
        camada = pygame.Surface(
            (self.largura, self.altura),
            pygame.SRCALPHA
        )

        for nevoa in self.nevoas:
            x = int(nevoa["x"])
            y = int(nevoa["y"])

            largura = nevoa["largura"]
            altura = nevoa["altura"]

            pygame.draw.ellipse(
                camada,
                (65, 130, 65, nevoa["alpha"]),
                (x, y, largura, altura)
            )

            pygame.draw.ellipse(
                camada,
                (55, 110, 70, nevoa["alpha"] // 2),
                (x + 25, y - 12, largura, altura)
            )

        tela.blit(camada, (0, 0))

    # =====================================
    # DESENHO DAS BRASAS
    # =====================================

    def _desenhar_brasas(self, tela):
        camada = pygame.Surface(
            (self.largura, self.altura),
            pygame.SRCALPHA
        )

        for brasa in self.brasas:
            brilho = int(
                170 + 70 * math.sin(
                    self.tempo * 3 + brasa["oscilacao"]
                )
            )

            brilho = max(0, min(255, brilho))

            pygame.draw.circle(
                camada,
                (255, brilho // 2, 45, 220),
                (int(brasa["x"]), int(brasa["y"])),
                brasa["tamanho"]
            )

        tela.blit(camada, (0, 0))

    # =====================================
    # DESENHO DOS ESPOROS
    # =====================================

    def _desenhar_esporos(self, tela):
        camada = pygame.Surface(
            (self.largura, self.altura),
            pygame.SRCALPHA
        )

        for esporo in self.esporos:
            pulsacao = math.sin(
                self.tempo * 2 + esporo["oscilacao"]
            )

            alpha = int(100 + 80 * (pulsacao + 1) / 2)

            pygame.draw.circle(
                camada,
                (100, 220, 105, alpha),
                (int(esporo["x"]), int(esporo["y"])),
                esporo["tamanho"]
            )

        tela.blit(camada, (0, 0))

    # =====================================
    # DESENHO DA FUMAÇA
    # =====================================

    def _desenhar_fumacas(self, tela):
        camada = pygame.Surface(
            (self.largura, self.altura),
            pygame.SRCALPHA
        )

        for fumaca in self.fumacas:
            tamanho = fumaca["tamanho"]
            x = int(fumaca["x"])
            y = int(fumaca["y"])

            pygame.draw.ellipse(
                camada,
                (15, 18, 20, fumaca["alpha"]),
                (x, y, tamanho * 2, tamanho)
            )

        tela.blit(camada, (0, 0))

    # =====================================
    # ILUMINAÇÃO AMBIENTAL
    # =====================================

    def _desenhar_iluminacao(self, tela):
        camada = pygame.Surface(
            (self.largura, self.altura),
            pygame.SRCALPHA
        )

        pulsacao = (math.sin(self.tempo * 1.8) + 1) / 2

        alpha_vermelho = int(7 + pulsacao * 9)

        camada.fill((90, 15, 10, alpha_vermelho))

        tela.blit(camada, (0, 0))

    # =====================================
    # EVENTOS
    # =====================================

    def eventos(self, eventos):
        for e in eventos:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    from cenas.menu import Menu
                    self.jogo.trocar_cena(Menu(self.jogo))

    # =====================================
    # DESENHO PRINCIPAL
    # =====================================

    def desenhar(self, tela):

        # Fundo original do castelo.
        tela.blit(self.fundo, (0, 0))

        # Camadas de atmosfera.
        self._desenhar_fumacas(tela)
        self._desenhar_nevoa(tela)
        self._desenhar_esporos(tela)
        self._desenhar_brasas(tela)

        # Luz avermelhada sutil para reforçar o clima
        # da batalha final.