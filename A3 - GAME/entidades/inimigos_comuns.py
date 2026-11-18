import math
import pygame
import config
from entidades.inimigo import Inimigo


class GuerreiroCorrompido(Inimigo):
    def __init__(self, x_centro, y_base):
        super().__init__(x_centro, y_base, largura=38, altura=52,
                         vida=3, dano=1, velocidade=90, cor=(110, 60, 150))


class Fantasma(Inimigo):
    """Espectro sombrio com aura etérea, capuz rasgado e cauda ondulante."""

    def __init__(self, x_centro, y_base):
        super().__init__(x_centro, y_base, largura=38, altura=50,
                         vida=3, dano=1, velocidade=135, cor=(140, 215, 235))
        self.t = 0.0
        self.alvo = None

    def atualizar(self, dt, plataformas):
        self.t += dt
        self.tempo_dano = max(0.0, self.tempo_dano - dt)

        if self.recuo > 0:
            self.recuo -= dt
            self.pos += self.vel * dt
        elif self.alvo:
            dx = self.alvo.rect.centerx - self.rect.centerx
            dy = (self.alvo.rect.centery - 12) - self.rect.centery
            dist = math.hypot(dx, dy)
            if 0 < dist < 560:
                self.direcao = 1 if dx >= 0 else -1
                self.vel.x = (dx / dist) * self.velocidade
                self.vel.y = (dy / dist) * (self.velocidade * 0.78)
            else:
                self.vel.x = 0
                self.vel.y = math.sin(self.t * 3.2) * 28
            self.pos += self.vel * dt

        self.rect.x = round(self.pos.x)
        self.rect.y = round(self.pos.y)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -40 or r.left > config.LARGURA + 40:
            return

        flutuar = int(math.sin(self.t * 5) * 5)
        onda = math.sin(self.t * 8) * 4

        aura = pygame.Surface((r.width + 36, r.height + 36), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (90, 200, 220, 42), (0, 0, r.width + 36, r.height + 36))
        tela.blit(aura, (r.x - 18, r.y - 18 + flutuar))

        surf = pygame.Surface((r.width + 16, r.height + 16), pygame.SRCALPHA)
        cx = (r.width + 16) // 2
        cor_corpo = (255, 255, 255, 235) if self.tempo_dano > 0 else (155, 215, 230, 175)
        cor_sombra = (55, 95, 115, 190)

        pts = [
            (cx - 16, 22),
            (cx - 12, 6),
            (cx, 2),
            (cx + 12, 6),
            (cx + 16, 22),
            (cx + 14 - onda, 46),
            (cx + 6, 38),
            (cx - onda, 50),
            (cx - 8, 39),
            (cx - 15 - onda, 46),
        ]
        pygame.draw.polygon(surf, cor_corpo, pts)
        pygame.draw.polygon(surf, cor_sombra, pts, 2)
        tela.blit(surf, (r.x - 8, r.y + flutuar))

        olho_base = r.centerx + (5 if self.direcao == 1 else -9)
        pygame.draw.ellipse(tela, (15, 25, 35), (r.centerx - 10, r.y + 10 + flutuar, 20, 14))
        pygame.draw.circle(tela, (140, 255, 255), (olho_base, r.y + 17 + flutuar), 2)
        pygame.draw.circle(tela, (140, 255, 255), (olho_base + 5, r.y + 17 + flutuar), 2)

        if self.vida < self.vida_max:
            pygame.draw.rect(tela, (25, 45, 55), (r.x, r.y - 10 + flutuar, r.width, 4))
            larg = int(r.width * max(self.vida, 0) / self.vida_max)
            pygame.draw.rect(tela, (100, 240, 255), (r.x, r.y - 10 + flutuar, larg, 4))


class OrbeSombrio:
    """Projétil lançado pelo Monstro Pálido contra a guerreira."""

    def __init__(self, x, y, alvo_x, alvo_y):
        self.pos = pygame.Vector2(x, y)
        dx = alvo_x - x
        dy = alvo_y - y
        dist = max(1.0, math.hypot(dx, dy))
        vel = 270
        self.vel = pygame.Vector2((dx / dist) * vel, (dy / dist) * vel)
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)
        self.ativo = True
        self.tempo_vida = 3.2
        self.dano = 1

    def atualizar(self, dt, solidos):
        self.tempo_vida -= dt
        if self.tempo_vida <= 0:
            self.ativo = False
            return
        self.pos += self.vel * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if any(self.rect.colliderect(s.rect) for s in solidos):
            self.ativo = False

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -30 or r.left > config.LARGURA + 30:
            return
        aura = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(aura, (170, 30, 80, 95), (20, 20), 18)
        pygame.draw.circle(aura, (255, 90, 130, 220), (20, 20), 9)
        pygame.draw.circle(aura, (255, 220, 230, 255), (20, 20), 4)
        tela.blit(aura, (r.centerx - 20, r.centery - 20))


class MonstroPalido(Inimigo):
    """Chefe necromante pálido: nunca cai de plataformas, invoca fantasmas e lança orbes."""

    def __init__(self, x_centro, y_base):
        super().__init__(x_centro, y_base, largura=64, altura=104,
                         vida=26, dano=1, velocidade=80, cor=(225, 222, 232))
        self.t = 0.0
        self.tempo_invocacao = 1.4
        self.intervalo_invocacao = 3.75  # 1,2x mais frequente que 4.5s
        self.tempo_tiro = 1.6
        self.alvo = None
        self.fantasmas_invocados = []
        self.orbes_lancados = []
        self.anim_invocar = 0.0
        self.fantasmas_ativos_arena = 0

    def receber_dano(self, dano, origem_x):
        super().receber_dano(dano, origem_x)
        self.vel.x *= 0.12
        self.vel.y = 0

    def _tem_chao_na_direcao(self, direcao, plataformas):
        sonda_x = self.rect.centerx + direcao * (self.rect.width // 2 + 12)
        sonda_y = self.rect.bottom + 8
        return any(p.rect.collidepoint((sonda_x, sonda_y)) for p in plataformas)

    def atualizar(self, dt, plataformas):
        self.t += dt
        self.anim_invocar = max(0.0, self.anim_invocar - dt)

        if self.alvo and self.recuo <= 0:
            dx = self.alvo.rect.centerx - self.rect.centerx
            if abs(dx) < 750:
                self.direcao = 1 if dx >= 0 else -1

        pos_x_anterior = self.pos.x
        super().atualizar(dt, plataformas)

        if self.no_chao:
            sentido_mov = 1 if self.pos.x >= pos_x_anterior else -1
            if not self._tem_chao_na_direcao(sentido_mov, plataformas):
                self.pos.x = pos_x_anterior
                self.rect.x = round(self.pos.x)
                self.vel.x = 0
                self.direcao *= -1

        if self.vivo and self.alvo:
            dist = abs(self.alvo.rect.centerx - self.rect.centerx)
            if dist < 760:
                self.tempo_invocacao -= dt
                if self.tempo_invocacao <= 0:
                    self.tempo_invocacao = self.intervalo_invocacao
                    if self.fantasmas_ativos_arena < 5:
                        self.anim_invocar = 0.85
                        # Em fúria (<= 50% de vida), invoca 2 fantasmas de uma vez
                        qtd = 2 if self.vida <= self.vida_max // 2 else 1
                        for i in range(qtd):
                            lado = self.direcao if i == 0 else -self.direcao
                            spawn_x = self.rect.centerx + (lado * 46)
                            spawn_y = self.rect.centery - 38 - (i * 18)
                            novo = Fantasma(spawn_x, spawn_y)
                            novo.alvo = self.alvo
                            self.fantasmas_invocados.append(novo)

                self.tempo_tiro -= dt
                if self.tempo_tiro <= 0:
                    self.tempo_tiro = 2.4
                    orbe = OrbeSombrio(
                        self.rect.centerx + self.direcao * 35,
                        self.rect.y + 42,
                        self.alvo.rect.centerx,
                        self.alvo.rect.centery
                    )
                    self.orbes_lancados.append(orbe)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -80 or r.left > config.LARGURA + 80:
            return

        d = self.direcao
        cx = r.centerx
        respirar = math.sin(self.t * 3.5) * 2
        cor_pele = (255, 190, 190) if self.tempo_dano > 0 else (228, 226, 235)
        cor_sombra_pele = (155, 150, 168)

        if self.anim_invocar > 0:
            aura = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(aura, (90, 230, 220, 75), (80, 80), 75)
            tela.blit(aura, (cx - 80, r.centery - 80))

        onda = math.sin(self.t * 5) * 4
        manto = [
            (cx - 24, r.y + 30),
            (cx + 24, r.y + 30),
            (cx + 30 + onda, r.bottom),
            (cx + 12, r.bottom - 8),
            (cx, r.bottom),
            (cx - 14, r.bottom - 7),
            (cx - 30 + onda, r.bottom),
        ]
        pygame.draw.polygon(tela, (24, 22, 34), manto)
        pygame.draw.polygon(tela, (55, 50, 72), manto, 2)

        torso = pygame.Rect(cx - 16, r.y + 28 + int(respirar), 32, 36)
        pygame.draw.rect(tela, cor_pele, torso, border_radius=8)
        for costela_y in range(torso.y + 8, torso.bottom - 6, 7):
            pygame.draw.line(tela, cor_sombra_pele, (torso.x + 5, costela_y), (torso.right - 5, costela_y), 2)

        cranio = pygame.Rect(cx - 14, r.y + int(respirar), 28, 30)
        pygame.draw.ellipse(tela, cor_pele, cranio)
        pygame.draw.ellipse(tela, cor_sombra_pele, cranio, 2)

        olho_x = cranio.centerx + (4 if d == 1 else -10)
        pygame.draw.ellipse(tela, (25, 20, 30), (olho_x - 2, cranio.y + 10, 12, 8))
        pygame.draw.circle(tela, (235, 35, 65), (olho_x + 4, cranio.y + 14), 3)

        ombro = (cx + d * 14, r.y + 34 + int(respirar))
        cotovelo = (cx + d * 32, r.y + 52 - (18 if self.anim_invocar > 0 else 0))
        mao = (cx + d * 46, r.y + 66 - (32 if self.anim_invocar > 0 else 0))
        pygame.draw.lines(tela, cor_pele, False, [ombro, cotovelo, mao], 6)
        for g in (-4, 0, 4):
            pygame.draw.line(tela, (90, 85, 100), mao, (mao[0] + d * 10, mao[1] + g + 4), 2)