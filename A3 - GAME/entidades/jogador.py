import pygame
import config


class Jogador:
    """Dáron. Por enquanto é um retângulo; os sprites entram depois."""

    LARGURA = 40
    ALTURA = 56

    def __init__(self, x, y):
        self.inicio = (x, y)
        self.rect = pygame.Rect(x, y, self.LARGURA, self.ALTURA)
        self.pos = pygame.Vector2(x, y)   # posição com decimais (movimento suave)
        self.vel = pygame.Vector2(0, 0)
        self.no_chao = False
        self.direcao = 1                  # 1 = direita, -1 = esquerda

        # Pulo (a relíquia do salto duplo muda pulos_maximos para 2)
        self.pulos_maximos = 1
        self.pulos_restantes = 1

        # Habilidades conquistadas
        self.tem_salto_duplo = False
        self.tem_avanco = False
        self.tempo_avanco = 0.0
        self.recarga_avanco = 0.0

        # Combate
        self.vida = config.VIDA_JOGADOR
        self.tempo_ataque = 0.0           # > 0 enquanto o golpe está ativo
        self.tempo_recarga = 0.0
        self.alvos_acertados = set()      # garante 1 acerto por inimigo em cada golpe
        self.invencivel = 0.0
        self.recuo = 0.0                  # > 0 enquanto está sendo empurrado

    # ---------- ações ----------
    def reiniciar(self):
        self.pos.update(self.inicio)
        self.rect.topleft = self.inicio
        self.vel.update(0, 0)
        self.tempo_ataque = 0.0
        self.tempo_avanco = 0.0
        self.recuo = 0.0
        self.invencivel = config.TEMPO_INVENCIVEL

    def desbloquear(self, habilidade):
        if habilidade == "salto_duplo" and not self.tem_salto_duplo:
            self.tem_salto_duplo = True
            self.pulos_maximos = 2
            self.pulos_restantes += 1
        elif habilidade == "avanco":
            self.tem_avanco = True

    def pular(self):
        if self.pulos_restantes > 0:
            self.vel.y = -config.FORCA_PULO
            self.pulos_restantes -= 1

    def avancar(self):
        if self.tem_avanco and self.recarga_avanco <= 0 and self.recuo <= 0:
            self.tempo_avanco = config.AVANCO_DURACAO
            self.recarga_avanco = config.AVANCO_RECARGA
            self.invencivel = max(self.invencivel, config.AVANCO_DURACAO)  # não leva dano no avanço

    def atacar(self):
        if self.tempo_recarga <= 0:
            self.tempo_ataque = config.ATAQUE_DURACAO
            self.tempo_recarga = config.ATAQUE_RECARGA
            self.alvos_acertados.clear()

    def receber_dano(self, dano, origem_x):
        """Devolve True se levou o dano (False se estava invencível)."""
        if self.invencivel > 0:
            return False
        self.vida -= dano
        self.invencivel = config.TEMPO_INVENCIVEL
        sentido = 1 if self.rect.centerx >= origem_x else -1
        self.vel.x = sentido * config.RECUO_X
        self.vel.y = -config.RECUO_Y
        self.recuo = 0.2
        return True

    @property
    def avancando(self):
        return self.tempo_avanco > 0

    @property
    def atacando(self):
        return self.tempo_ataque > 0

    @property
    def hitbox_ataque(self):
        """Área do golpe (None se não está atacando)."""
        if not self.atacando:
            return None
        alcance, altura = config.ATAQUE_ALCANCE, 40
        if self.direcao == 1:
            area = pygame.Rect(self.rect.right, 0, alcance, altura)
        else:
            area = pygame.Rect(self.rect.left - alcance, 0, alcance, altura)
        area.centery = self.rect.centery
        return area

    # ---------- atualização ----------
    def atualizar(self, dt, plataformas, largura_mundo):
        self.tempo_ataque = max(0.0, self.tempo_ataque - dt)
        self.tempo_recarga = max(0.0, self.tempo_recarga - dt)
        self.tempo_avanco = max(0.0, self.tempo_avanco - dt)
        self.recarga_avanco = max(0.0, self.recarga_avanco - dt)
        self.invencivel = max(0.0, self.invencivel - dt)

        # --- movimento horizontal ---
        if self.avancando:
            self.vel.x = self.direcao * config.AVANCO_VELOCIDADE
            self.vel.y = 0                    # o avanço ignora a gravidade
        elif self.recuo > 0:
            self.recuo -= dt                  # sendo empurrado: ignora o teclado
        else:
            teclas = pygame.key.get_pressed()
            direcao = 0
            if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
                direcao -= 1
            if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
                direcao += 1
            self.vel.x = direcao * config.VELOCIDADE_JOGADOR
            if direcao != 0:
                self.direcao = direcao

        # --- gravidade ---
        if not self.avancando:
            self.vel.y = min(self.vel.y + config.GRAVIDADE * dt, config.VELOCIDADE_QUEDA_MAX)

        # --- move no eixo X e resolve colisões ---
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                if self.vel.x > 0:
                    self.rect.right = p.rect.left
                elif self.vel.x < 0:
                    self.rect.left = p.rect.right
                self.pos.x = self.rect.x

        # --- move no eixo Y e resolve colisões ---
        estava_no_chao = self.no_chao
        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)
        self.no_chao = False
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                if self.vel.y > 0:            # caindo: pousou em cima
                    self.rect.bottom = p.rect.top
                    self.no_chao = True
                elif self.vel.y < 0:          # subindo: bateu a cabeça
                    self.rect.top = p.rect.bottom
                self.vel.y = 0
                self.pos.y = self.rect.y

        # parado em cima de algo, a gravidade move menos de 1px e o retângulo nem sempre
        # encosta; então "sonda" 1px abaixo dos pés para saber se ainda há chão
        if not self.no_chao and self.vel.y >= 0:
            sonda = self.rect.move(0, 1)
            if any(sonda.colliderect(p.rect) for p in plataformas):
                self.no_chao = True

        if self.no_chao:
            self.pulos_restantes = self.pulos_maximos
        elif estava_no_chao and self.vel.y >= 0:
            # saiu de uma beirada sem pular: sobra no máximo 1 pulo no ar
            self.pulos_restantes = min(self.pulos_restantes, max(1, self.pulos_maximos - 1))

        # --- não deixa sair pelos lados do mapa ---
        if self.rect.left < 0:
            self.rect.left = 0
            self.pos.x = self.rect.x
        if self.rect.right > largura_mundo:
            self.rect.right = largura_mundo
            self.pos.x = self.rect.x

    # ---------- desenho ----------
    def desenhar(self, tela, camera):
        # pisca enquanto está invencível (menos durante o avanço)
        if self.invencivel > 0 and not self.avancando and int(self.invencivel * 20) % 2 == 0:
            return

        rect = camera.aplicar(self.rect)

        if self.avancando:  # rastro do avanço
            rastro = pygame.Surface(rect.size, pygame.SRCALPHA)
            rastro.fill((*config.VERMELHO, 90))
            tela.blit(rastro, (rect.x - self.direcao * 26, rect.y))

        pygame.draw.rect(tela, config.VERMELHO, rect)
        olho_x = rect.right - 14 if self.direcao == 1 else rect.left + 6
        pygame.draw.rect(tela, config.BRANCO, (olho_x, rect.y + 10, 8, 8))

        area = self.hitbox_ataque
        if area:
            area = camera.aplicar(area)
            golpe = pygame.Surface(area.size, pygame.SRCALPHA)
            golpe.fill((*config.DOURADO, 170))
            tela.blit(golpe, area.topleft)
