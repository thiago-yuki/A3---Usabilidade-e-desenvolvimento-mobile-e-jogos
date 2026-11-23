import math
import random
import pygame
import config


class Saida:
    """Portal que leva para a próxima fase."""

    def __init__(self, x, y, largura, altura):
        self.rect = pygame.Rect(x, y, largura, altura)
        self.t = 0.0
        self.bizarro = False
        self.selado = False
        self.design_fase1 = False

    def atualizar(self, dt):
        self.t += dt

    def _desenhar_portal_fase1(self, tela, r):
        tempo = self.t
        pulso = (math.sin(tempo * 2.5) + 1) / 2
        margem = 22
        brilho = pygame.Surface(
            (r.width + margem * 2, r.height + margem * 2),
            pygame.SRCALPHA,
        )
        pygame.draw.ellipse(
            brilho,
            (115, 48, 190, int(35 + pulso * 35)),
            brilho.get_rect(),
        )
        pygame.draw.ellipse(
            brilho,
            (190, 120, 220, int(20 + pulso * 25)),
            brilho.get_rect().inflate(-12, -12),
        )
        tela.blit(brilho, (r.x - margem, r.y - margem))

        pygame.draw.ellipse(tela, (37, 19, 57), r)
        interior = r.inflate(-12, -12)
        pygame.draw.ellipse(tela, (72, 32, 105), interior)
        centro = interior.inflate(-10, -10)
        pygame.draw.ellipse(tela, (35, 19, 65), centro)
        pygame.draw.ellipse(tela, (133, 80, 180), r, 4)
        pygame.draw.ellipse(tela, config.DOURADO, r.inflate(-5, -5), 2)

        arco = centro.inflate(-5, -5)
        inicio = tempo * 1.5
        pygame.draw.arc(tela, (190, 135, 230), arco, inicio, inicio + math.pi * 1.2, 3)
        pygame.draw.arc(
            tela,
            (220, 180, 110),
            arco.inflate(-6, -6),
            -inicio,
            -inicio + math.pi,
            2,
        )

        for i in range(4):
            angulo = tempo * 1.5 + i * math.pi / 2
            px = r.centerx + math.cos(angulo) * (r.width * 0.39)
            py = r.centery + math.sin(angulo) * (r.height * 0.39)
            tamanho = 2 + int((math.sin(tempo * 4 + i) + 1) * 1.5)
            pygame.draw.circle(tela, (255, 220, 145), (int(px), int(py)), tamanho)
            pygame.draw.circle(tela, (255, 245, 205), (int(px), int(py)), 1)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -80 or r.left > tela.get_width() + 80:
            return

        if not self.bizarro:
            if self.design_fase1:
                self._desenhar_portal_fase1(tela, r)
                return
            pygame.draw.ellipse(tela, config.DOURADO, r, 4)
            pygame.draw.ellipse(tela, (90, 60, 20), r.inflate(-16, -16))
            return

        # --- Portal Dimensional Bizarro Vermelho ---
        cx, cy = r.centerx, r.centery
        pulso = math.sin(self.t * 6.0) * 5

        # 1. Aura externa carmesim distorcida
        aura = pygame.Surface((160, 190), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (160, 10, 30, 45), (10 - pulso, 10 - pulso, 140 + pulso * 2, 170 + pulso * 2))
        pygame.draw.ellipse(aura, (230, 25, 50, 85), (26, 24, 108, 142))
        tela.blit(aura, (cx - 80, cy - 95))

        # 2. Vórtice espiral giratório
        for anel in range(4):
            ang_base = self.t * (3.5 + anel * 1.2) * (-1 if anel % 2 == 0 else 1)
            rx = (28 - anel * 5) + math.sin(self.t * 8 + anel) * 3
            ry = (46 - anel * 8) + math.cos(self.t * 7 + anel) * 4
            pts = []
            for p in range(10):
                ang = ang_base + (p / 10) * math.tau
                distorcao = math.sin(ang * 3 + self.t * 10) * 4
                px = cx + math.cos(ang) * (rx + distorcao)
                py = cy + math.sin(ang) * (ry + distorcao)
                pts.append((px, py))
            cor_anel = (255, 60 + anel * 35, 80 + anel * 30)
            pygame.draw.polygon(tela, cor_anel, pts, 2)

        # 3. Núcleo abissal negro rasgado no centro da dimensão
        nucleo = pygame.Rect(0, 0, int(22 + pulso * 0.6), int(48 + pulso))
        nucleo.center = (cx, cy)
        pygame.draw.ellipse(tela, (8, 2, 6), nucleo)
        pygame.draw.ellipse(tela, (255, 190, 200), nucleo, 2)

        # 4. Descargas / fissuras vermelhas saindo das bordas do portal
        for i in range(4):
            ang = self.t * 4 + i * (math.pi / 2)
            x1 = cx + math.cos(ang) * 24
            y1 = cy + math.sin(ang) * 40
            x2 = x1 + math.cos(ang + 0.4) * 16 + random.randint(-3, 3)
            y2 = y1 + math.sin(ang + 0.4) * 18 + random.randint(-3, 3)
            pygame.draw.line(tela, (255, 70, 90), (x1, y1), (x2, y2), 2)

        # 5. Correntes dimensionais enquanto o Monstro Pálido estiver vivo
        if self.selado:
            pygame.draw.line(tela, (255, 40, 70), (r.left - 8, r.top + 12), (r.right + 8, r.bottom - 12), 4)
            pygame.draw.line(tela, (255, 40, 70), (r.right + 8, r.top + 12), (r.left - 8, r.bottom - 12), 4)