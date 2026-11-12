import pygame
import config


class Inimigo:
    """Classe base: patrulha, gravidade, vida e dano. Os tipos novos herdam daqui."""

    def __init__(self, x_centro, y_base, largura, altura, vida, dano, velocidade, cor):
        self.rect = pygame.Rect(0, 0, largura, altura)
        self.rect.midbottom = (x_centro, y_base)
        self.pos = pygame.Vector2(self.rect.topleft)
        self.vel = pygame.Vector2(0, 0)

        self.vida = vida
        self.vida_max = vida
        self.dano = dano
        self.velocidade = velocidade
        self.cor = cor

        self.direcao = -1
        self.vivo = True
        self.no_chao = False
        self.tempo_dano = 0.0     # > 0 = pisca branco ao ser atingido
        self.recuo = 0.0

    def receber_dano(self, dano, origem_x):
        self.vida -= dano
        self.tempo_dano = 0.15
        sentido = 1 if self.rect.centerx >= origem_x else -1
        self.vel.x = sentido * config.RECUO_INIMIGO
        self.vel.y = -200
        self.recuo = 0.15
        if self.vida <= 0:
            self.vivo = False

    def atualizar(self, dt, plataformas):
        self.tempo_dano = max(0.0, self.tempo_dano - dt)

        if self.recuo > 0:
            self.recuo -= dt
        else:
            self.vel.x = self.direcao * self.velocidade

        self.vel.y = min(self.vel.y + config.GRAVIDADE * dt, config.VELOCIDADE_QUEDA_MAX)

        # --- eixo X: se bater numa parede, vira ---
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)
        bateu = False
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                if self.vel.x > 0:
                    self.rect.right = p.rect.left
                elif self.vel.x < 0:
                    self.rect.left = p.rect.right
                self.pos.x = self.rect.x
                bateu = True
        if bateu and self.recuo <= 0:
            self.direcao *= -1

        # --- eixo Y ---
        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)
        self.no_chao = False
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                if self.vel.y > 0:
                    self.rect.bottom = p.rect.top
                    self.no_chao = True
                elif self.vel.y < 0:
                    self.rect.top = p.rect.bottom
                self.vel.y = 0
                self.pos.y = self.rect.y

        # --- não cai de plataformas: se não há chão à frente, vira ---
        if self.no_chao and self.recuo <= 0:
            frente = (self.rect.centerx + self.direcao * (self.rect.width // 2 + 2),
                      self.rect.bottom + 4)
            if not any(p.rect.collidepoint(frente) for p in plataformas):
                self.direcao *= -1

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < 0 or r.left > config.LARGURA:
            return
        cor = config.BRANCO if self.tempo_dano > 0 else self.cor
        pygame.draw.rect(tela, cor, r)
        olho_x = r.right - 12 if self.direcao == 1 else r.left + 4
        pygame.draw.rect(tela, (255, 80, 60), (olho_x, r.y + 10, 8, 6))
        # barrinha de vida (só aparece depois de apanhar)
        if self.vida < self.vida_max:
            pygame.draw.rect(tela, (60, 20, 20), (r.x, r.y - 10, r.width, 5))
            largura = int(r.width * max(self.vida, 0) / self.vida_max)
            pygame.draw.rect(tela, config.VERMELHO, (r.x, r.y - 10, largura, 5))
