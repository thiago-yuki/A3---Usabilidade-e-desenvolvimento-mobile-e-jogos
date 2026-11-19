import math
import pygame
import config


class TroncoCaido:
    """Tronco caído ou toco velho apodrecido (L): obstáculo sólido na floresta."""

    def __init__(self, x, y, largura, altura):
        self.rect = pygame.Rect(x, y, largura, altura)
        self.eh_tronco_longo = largura > config.TAMANHO_TILE

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -20 or r.left > config.LARGURA + 20:
            return

        if self.eh_tronco_longo:
            corpo = pygame.Rect(r.x + 2, r.y + 10, r.width - 4, r.height - 10)
            pygame.draw.rect(tela, (36, 28, 22), corpo, border_radius=8)
            pygame.draw.rect(tela, (22, 17, 14), corpo, 2, border_radius=8)

            for ry in (corpo.y + 10, corpo.y + 20, corpo.y + 29):
                pygame.draw.line(tela, (24, 18, 15), (corpo.x + 12, ry), (corpo.right - 14, ry), 2)
            pygame.draw.line(tela, (16, 12, 10), (corpo.centerx - 16, corpo.y + 4), (corpo.centerx + 4, corpo.y + 18), 2)

            for cx in (corpo.x + 10, corpo.right - 10):
                pygame.draw.ellipse(tela, (64, 52, 38), (cx - 8, corpo.y + 4, 16, corpo.height - 8))
                pygame.draw.ellipse(tela, (38, 30, 22), (cx - 5, corpo.y + 9, 10, corpo.height - 18), 1)

            pygame.draw.rect(tela, (32, 48, 30), (corpo.x + 14, corpo.y - 2, corpo.width - 28, 6), border_radius=3)
            pygame.draw.line(tela, (44, 34, 26), (corpo.x + 26, corpo.y + 2), (corpo.x + 16, corpo.y - 10), 3)
            pygame.draw.line(tela, (44, 34, 26), (corpo.right - 30, corpo.y + 2), (corpo.right - 20, corpo.y - 12), 3)
        else:
            pygame.draw.polygon(tela, (34, 26, 21), [
                (r.x + 2, r.bottom),
                (r.x + 8, r.y + 8),
                (r.centerx - 4, r.y + 2),
                (r.centerx + 5, r.y + 11),
                (r.right - 7, r.y + 6),
                (r.right - 2, r.bottom),
            ])
            pygame.draw.polygon(tela, (20, 15, 12), [
                (r.x + 2, r.bottom),
                (r.x + 8, r.y + 8),
                (r.centerx - 4, r.y + 2),
                (r.centerx + 5, r.y + 11),
                (r.right - 7, r.y + 6),
                (r.right - 2, r.bottom),
            ], 2)
            pygame.draw.line(tela, (20, 15, 12), (r.centerx - 6, r.y + 12), (r.centerx - 8, r.bottom - 2), 2)
            pygame.draw.line(tela, (20, 15, 12), (r.centerx + 7, r.y + 14), (r.centerx + 9, r.bottom - 2), 2)
            pygame.draw.ellipse(tela, (30, 46, 28), (r.x + 8, r.y + 6, 16, 6))


class GalhosEspinhos:
    """Emaranhado de galhos secos e espinhos amaldiçoados no chão (G): causa dano ao pisar."""

    def __init__(self, x, y_base, largura):
        altura = 26
        self.rect = pygame.Rect(x + 4, y_base - altura, max(16, largura - 8), altura)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -20 or r.left > config.LARGURA + 20:
            return

        base_y = r.bottom
        ini_x = r.x - 4
        fim_x = r.right + 4

        pygame.draw.line(tela, (42, 31, 23), (ini_x + 2, base_y - 4), (fim_x - 2, base_y - 5), 4)
        pygame.draw.line(tela, (28, 21, 16), (ini_x + 6, base_y - 2), (fim_x - 6, base_y - 2), 3)

        passo = 14
        idx = 0
        for gx in range(ini_x + 4, fim_x - 4, passo):
            alt = 22 if idx % 2 == 0 else 17
            incl = -5 if idx % 3 == 0 else 5
            ponta = (gx + incl, base_y - alt)
            pygame.draw.line(tela, (54, 40, 29), (gx - 4, base_y - 2), ponta, 3)
            pygame.draw.line(tela, (34, 24, 18), (gx + 5, base_y - 2), (gx - incl, base_y - alt + 4), 2)
            pygame.draw.circle(tela, (135, 118, 96), ponta, 2)
            idx += 1


class VinhaEspinhosa:
    """Obstáculo aéreo suspenso (V): cipós retorcidos com espinhos venenosos pendurados do alto."""

    def __init__(self, x, y_topo, largura, altura):
        self.rect = pygame.Rect(x + 6, y_topo, max(18, largura - 12), max(24, altura - 4))
        self.fase = (x * 0.03) % math.tau

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -30 or r.left > config.LARGURA + 30:
            return

        t = pygame.time.get_ticks() * 0.0025
        balanco = math.sin(t + self.fase) * 4.0

        # Raiz / galho superior de fixação
        pygame.draw.rect(tela, (28, 21, 19), (r.x - 4, r.y, r.width + 8, 7), border_radius=3)

        # Três hastes pendentes balançando suavemente
        colunas = (r.left + 4, r.centerx, r.right - 4)
        for idx, bx in enumerate(colunas):
            comp = r.height - (6 if idx == 1 else 14)
            pts = []
            passos = 5
            for s in range(passos + 1):
                prog = s / passos
                ox = bx + math.sin(prog * 3.2 + idx) * 4 + balanco * prog
                oy = r.y + prog * comp
                pts.append((round(ox), round(oy)))

            pygame.draw.lines(tela, (38, 26, 28), False, pts, 3)
            pygame.draw.lines(tela, (24, 46, 28), False, pts, 1)

            # Espinhos afiados ao longo da vinha
            for s in range(1, passos):
                px, py = pts[s]
                lado = 1 if (s + idx) % 2 == 0 else -1
                pygame.draw.polygon(tela, (165, 42, 58), [
                    (px, py - 3),
                    (px + lado * 7, py),
                    (px, py + 3),
                ])


class CipoEscalada:
    """Cipó grosso e raízes entrelaçadas (H): permite à guerreira escalar penhascos e copas."""

    def __init__(self, x_centro, y_topo, altura):
        self.rect = pygame.Rect(x_centro - 11, y_topo, 22, altura)
        self.fase = (x_centro * 0.02) % math.tau

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -25 or r.left > config.LARGURA + 25:
            return

        t = pygame.time.get_ticks() * 0.002
        cx = r.centerx

        # Nó superior preso na rocha ou galho
        pygame.draw.ellipse(tela, (46, 36, 26), (cx - 10, r.y - 3, 20, 8))

        # Duas cordas/cipós trançados de cima até embaixo
        passo = 16
        pts_a = []
        pts_b = []
        for y in range(r.y, r.bottom + passo, passo):
            yy = min(y, r.bottom)
            prog = (yy - r.y) / max(1, r.height)
            onda = math.sin(prog * 10.0 + t + self.fase) * 4
            pts_a.append((round(cx - 3 + onda), yy))
            pts_b.append((round(cx + 3 - onda), yy))

        if len(pts_a) >= 2:
            pygame.draw.lines(tela, (58, 44, 30), False, pts_a, 4)
            pygame.draw.lines(tela, (38, 56, 32), False, pts_b, 3)

        # Nós e folhas pequenas para facilitar a leitura visual de escalada
        for y in range(r.y + 14, r.bottom - 6, 24):
            pygame.draw.circle(tela, (76, 58, 38), (cx, y), 3)
            lado = 1 if (y // 24) % 2 == 0 else -1
            pygame.draw.ellipse(tela, (34, 68, 36), (cx + lado * 2, y - 3, 7, 4))


class ArmadilhaCacador:
    """Armadilha de ferro enferrujada escondida no mato (M): fecha e fere jogador ou zumbis."""

    def __init__(self, x_centro, y_base):
        self.rect = pygame.Rect(0, 0, 34, 16)
        self.rect.midbottom = (x_centro, y_base)
        self.fechada = False
        self.tempo_rearmar = 0.0

    def atualizar(self, dt):
        if self.fechada:
            self.tempo_rearmar -= dt
            if self.tempo_rearmar <= 0:
                self.fechada = False

    def acionar(self):
        self.fechada = True
        self.tempo_rearmar = 2.2

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -20 or r.left > config.LARGURA + 20:
            return

        cor_ferro = (88, 62, 52)
        cor_dente = (155, 148, 140)
        pygame.draw.rect(tela, (46, 36, 34), (r.x + 2, r.bottom - 5, r.width - 4, 5), border_radius=2)

        if self.fechada:
            pygame.draw.polygon(tela, cor_ferro, [
                (r.x + 5, r.bottom - 4),
                (r.centerx - 2, r.y - 4),
                (r.centerx + 2, r.y - 4),
                (r.right - 5, r.bottom - 4),
            ])
            pygame.draw.line(tela, cor_dente, (r.centerx, r.y - 4), (r.centerx, r.bottom - 5), 2)
        else:
            pygame.draw.line(tela, cor_ferro, (r.x + 2, r.bottom - 4), (r.x + 8, r.y + 2), 3)
            pygame.draw.line(tela, cor_ferro, (r.right - 2, r.bottom - 4), (r.right - 8, r.y + 2), 3)
            for dx in range(r.x + 7, r.right - 6, 6):
                pygame.draw.polygon(tela, cor_dente, [
                    (dx, r.bottom - 5),
                    (dx + 2, r.y + 3),
                    (dx + 4, r.bottom - 5),
                ])


class LapideAntiga:
    """Lápide antiga, cruz de pedra quebrada e crânios (R): ambientação sombria e velha."""

    def __init__(self, x_centro, y_base, variante=0):
        self.x_centro = x_centro
        self.y_base = y_base
        self.variante = variante

    def desenhar(self, tela, camera):
        sx = round(self.x_centro - camera.x)
        sy = round(self.y_base - camera.y)
        if sx < -50 or sx > config.LARGURA + 50:
            return

        cor_pedra = (52, 56, 54)
        cor_sombra = (32, 35, 34)
        cor_musgo = (30, 46, 31)

        if self.variante % 2 == 0:
            pts = [
                (sx - 13, sy),
                (sx - 15, sy - 30),
                (sx - 7, sy - 38),
                (sx + 8, sy - 37),
                (sx + 14, sy - 28),
                (sx + 12, sy),
            ]
            pygame.draw.polygon(tela, cor_pedra, pts)
            pygame.draw.polygon(tela, cor_sombra, pts, 2)
            pygame.draw.line(tela, cor_sombra, (sx - 1, sy - 30), (sx - 1, sy - 14), 2)
            pygame.draw.line(tela, cor_sombra, (sx - 6, sy - 24), (sx + 4, sy - 24), 2)
            pygame.draw.line(tela, (22, 24, 24), (sx + 9, sy - 24), (sx + 2, sy - 14), 2)
            pygame.draw.ellipse(tela, cor_musgo, (sx - 14, sy - 5, 16, 6))
        else:
            pygame.draw.polygon(tela, cor_pedra, [
                (sx - 4, sy), (sx - 6, sy - 42), (sx + 1, sy - 42), (sx + 3, sy)
            ])
            pygame.draw.polygon(tela, cor_pedra, [
                (sx - 14, sy - 31), (sx + 11, sy - 28), (sx + 10, sy - 22), (sx - 15, sy - 25)
            ])
            pygame.draw.ellipse(tela, cor_musgo, (sx - 10, sy - 4, 20, 5))
            pygame.draw.circle(tela, (150, 144, 126), (sx + 13, sy - 5), 5)
            pygame.draw.circle(tela, (24, 22, 20), (sx + 12, sy - 5), 1)
            pygame.draw.circle(tela, (24, 22, 20), (sx + 15, sy - 5), 1)


class OrbeChama:
    """Brasa viva deixada por inimigos derrotados: restaura 1 de vida e ilumina o chão."""

    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel_y = -180.0
        self.rect = pygame.Rect(round(x) - 9, round(y) - 9, 18, 18)
        self.no_chao = False
        self.anim_t = 0.0
        self.tempo_vida = 18.0
        self.coletado = False

    def atualizar(self, dt, solidos):
        self.anim_t += dt
        self.tempo_vida -= dt
        if self.tempo_vida <= 0:
            self.coletado = True
            return

        if not self.no_chao:
            self.vel_y = min(self.vel_y + config.GRAVIDADE * 0.7 * dt, config.VELOCIDADE_QUEDA_MAX)
            self.pos.y += self.vel_y * dt
            self.rect.centery = round(self.pos.y)
            for s in solidos:
                if self.rect.colliderect(s.rect) and self.vel_y >= 0:
                    self.rect.bottom = s.rect.top - 4
                    self.pos.y = self.rect.centery
                    self.vel_y = 0
                    self.no_chao = True
                    break

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -20 or r.left > config.LARGURA + 20:
            return
        if self.tempo_vida < 3.0 and int(self.tempo_vida * 10) % 2 == 0:
            return

        flutuar = int(math.sin(self.anim_t * 5.5) * 3) if self.no_chao else 0
        cx, cy = r.centerx, r.centery + flutuar

        halo = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 130, 35, 55), (20, 20), 18)
        pygame.draw.circle(halo, (255, 200, 70, 95), (20, 20), 11)
        tela.blit(halo, (cx - 20, cy - 20))

        pygame.draw.circle(tela, (255, 110, 30), (cx, cy), 6)
        pygame.draw.circle(tela, (255, 225, 110), (cx, cy - 1), 4)
        pygame.draw.circle(tela, config.BRANCO, (cx, cy - 1), 2)