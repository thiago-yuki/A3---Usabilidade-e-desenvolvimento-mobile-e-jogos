
import pygame
import config
import math


class Saida:
    """Portal mágico que leva para a próxima fase."""

    def __init__(self, x, y, largura, altura):
        # Mantém a colisão original
        self.rect = pygame.Rect(x, y, largura, altura)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)

        # Não desenha se estiver fora da tela
        if r.right < 0 or r.left > config.LARGURA:
            return

        tempo = pygame.time.get_ticks() / 1000

        # Pulsação suave da luz
        pulso = (math.sin(tempo * 2.5) + 1) / 2

        # Camada de brilho externo
        margem = 22
        brilho = pygame.Surface(
            (r.width + margem * 2, r.height + margem * 2),
            pygame.SRCALPHA
        )

        brilho.fill((0, 0, 0, 0))

        pygame.draw.ellipse(
            brilho,
            (115, 48, 190, int(35 + pulso * 35)),
            brilho.get_rect()
        )

        pygame.draw.ellipse(
            brilho,
            (190, 120, 220, int(20 + pulso * 25)),
            brilho.get_rect().inflate(-12, -12)
        )

        tela.blit(
            brilho,
            (r.x - margem, r.y - margem)
        )

        # Corpo escuro do portal
        pygame.draw.ellipse(
            tela,
            (37, 19, 57),
            r
        )

        interior = r.inflate(-12, -12)

        # Energia roxa no interior
        pygame.draw.ellipse(
            tela,
            (72, 32, 105),
            interior
        )

        centro = interior.inflate(-10, -10)

        # Núcleo mágico
        pygame.draw.ellipse(
            tela,
            (35, 19, 65),
            centro
        )

        # Anéis luminosos
        pygame.draw.ellipse(
            tela,
            (133, 80, 180),
            r,
            4
        )

        pygame.draw.ellipse(
            tela,
            (config.DOURADO),
            r.inflate(-5, -5),
            2
        )

        # Arcos de energia animados
        arco = centro.inflate(-5, -5)

        inicio = tempo * 1.5

        pygame.draw.arc(
            tela,
            (190, 135, 230),
            arco,
            inicio,
            inicio + math.pi * 1.2,
            3
        )

        pygame.draw.arc(
            tela,
            (220, 180, 110),
            arco.inflate(-6, -6),
            -inicio,
            -inicio + math.pi,
            2
        )

        # Pequenos pontos mágicos orbitando o portal
        for i in range(4):
            angulo = tempo * 1.5 + i * math.pi / 2

            px = r.centerx + math.cos(angulo) * (r.width * 0.39)
            py = r.centery + math.sin(angulo) * (r.height * 0.39)

            tamanho = 2 + int((math.sin(tempo * 4 + i) + 1) * 1.5)

            pygame.draw.circle(
                tela,
                (255, 220, 145),
                (int(px), int(py)),
                tamanho
            )

            pygame.draw.circle(
                tela,
                (255, 245, 205),
                (int(px), int(py)),
                1
            )

        # Contorno dourado externo
        pygame.draw.ellipse(
            tela,
            config.DOURADO,
            r,
            2
        )

