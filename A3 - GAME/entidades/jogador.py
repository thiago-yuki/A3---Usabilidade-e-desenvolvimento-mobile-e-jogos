import math
import random
import pygame
import config


class Tiro12:
    """Chumbinho disparado pela calibre 12 da guerreira na Fase 1."""

    def __init__(self, x, y, direcao, angulo_graus):
        self.pos = pygame.Vector2(x, y)
        self.pos_anterior = pygame.Vector2(x, y)
        rad = math.radians(angulo_graus)
        velocidade = 860
        self.vel = pygame.Vector2(
            math.cos(rad) * velocidade * direcao,
            math.sin(rad) * velocidade,
        )
        self.rect = pygame.Rect(round(x) - 3, round(y) - 3, 6, 6)
        self.distancia = 0.0
        self.alcance_max = 265
        self.ativo = True
        self.atingiu_parede = False

    def atualizar(self, dt, solidos):
        self.pos_anterior.update(self.pos)
        passo = self.vel * dt
        self.pos += passo
        self.distancia += passo.length()
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.distancia >= self.alcance_max:
            self.ativo = False
            return

        for s in solidos:
            if self.rect.colliderect(s.rect):
                self.ativo = False
                self.atingiu_parede = True
                return

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -20 or r.left > config.LARGURA + 20:
            return
        ini = (round(self.pos_anterior.x - camera.x), round(self.pos_anterior.y - camera.y))
        fim = r.center
        pygame.draw.line(tela, (255, 165, 45), ini, fim, 2)
        pygame.draw.circle(tela, (255, 235, 120), fim, 4)
        pygame.draw.circle(tela, config.BRANCO, fim, 2)


class ViroteBesta:
    """Virote metálico disparado pela Besta de 3 tiros na Fase 3."""

    def __init__(self, x, y, direcao, angulo_graus):
        self.pos = pygame.Vector2(x, y)
        self.pos_anterior = pygame.Vector2(x, y)
        self.direcao = direcao
        rad = math.radians(angulo_graus)
        velocidade = 780
        self.vel = pygame.Vector2(
            math.cos(rad) * velocidade * direcao,
            math.sin(rad) * velocidade,
        )
        self.rect = pygame.Rect(round(x) - 6, round(y) - 3, 12, 6)
        self.distancia = 0.0
        self.alcance_max = 620
        self.ativo = True
        self.atingiu_parede = False

    def atualizar(self, dt, solidos):
        self.pos_anterior.update(self.pos)
        passo = self.vel * dt
        self.pos += passo
        self.distancia += passo.length()
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.distancia >= self.alcance_max:
            self.ativo = False
            return

        for s in solidos:
            if self.rect.colliderect(s.rect):
                self.ativo = False
                self.atingiu_parede = True
                return

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -30 or r.left > config.LARGURA + 30:
            return
        cx, cy = r.center
        d = self.direcao
        # Rastro de vento
        ini = (round(self.pos_anterior.x - camera.x), round(self.pos_anterior.y - camera.y))
        pygame.draw.line(tela, (180, 220, 235), ini, (cx - d * 8, cy), 1)
        # Haste de madeira escura
        pygame.draw.line(tela, (130, 82, 42), (cx - d * 9, cy), (cx + d * 6, cy), 3)
        # Penas da traseira (carmesim)
        pygame.draw.polygon(tela, (190, 40, 55), [
            (cx - d * 9, cy),
            (cx - d * 13, cy - 3),
            (cx - d * 6, cy),
        ])
        pygame.draw.polygon(tela, (190, 40, 55), [
            (cx - d * 9, cy),
            (cx - d * 13, cy + 3),
            (cx - d * 6, cy),
        ])
        # Ponta de aço afiada
        pygame.draw.polygon(tela, (220, 230, 240), [
            (cx + d * 12, cy),
            (cx + d * 5, cy - 3),
            (cx + d * 5, cy + 3),
        ])


class Jogador:
    """Personagem das fases 1 (Espingarda) e 3 (Besta de 3 tiros)."""

    LARGURA = 40
    ALTURA = 56
    RECARGA_12 = 0.52
    RECARGA_BESTA = 0.44

    def __init__(self, x, y, modo_arma="espingarda", modo_guerreira=None, aparencia_guerreira=True):
        if modo_guerreira is not None:
            modo_arma = "besta" if modo_guerreira else "espingarda"
        self.modo_arma = modo_arma  # "espingarda" (Fase 1) ou "besta" (Fase 3)
        self.modo_guerreira = True
        self.aparencia_guerreira = True
        self.inicio = (x, y)
        self.rect = pygame.Rect(x, y, self.LARGURA, self.ALTURA)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.no_chao = False
        self.direcao = 1
        self.anim_t = 0.0

        # Escalada em cipós/escadas e em paredes
        self.escalando = False
        self.na_parede = 0
        self.parede_coyote = 0.0
        self.ultima_parede_dir = 0
        self.recuo_parede = 0.0

        # Habilidades padronizadas ativas em todas as fases
        self.tem_salto_duplo = True
        self.pulos_maximos = 2
        self.pulos_restantes = 2
        self.coyote_tempo = 0.0
        self.buffer_pulo = 0.0

        self.tem_avanco = True
        self.tempo_avanco = 0.0
        self.recarga_avanco = 0.0

        self.vida_max = 3 if modo_arma == "besta" else config.VIDA_JOGADOR
        self.vida = self.vida_max
        self.tempo_ataque = 0.0
        self.tempo_recarga = 0.0
        self.alvos_acertados = set()
        self.invencivel = 0.0
        self.recuo = 0.0
        self.coice_tiro = 0.0

    # ---------- ações ----------
    def reiniciar(self):
        self.pos.update(self.inicio)
        self.rect.topleft = self.inicio
        self.vel.update(0, 0)
        self.tempo_ataque = 0.0
        self.tempo_avanco = 0.0
        self.recuo = 0.0
        self.coice_tiro = 0.0
        self.coyote_tempo = 0.0
        self.buffer_pulo = 0.0
        self.escalando = False
        self.na_parede = 0
        self.parede_coyote = 0.0
        self.recuo_parede = 0.0
        self.invencivel = config.TEMPO_INVENCIVEL

    def desbloquear(self, habilidade):
        if habilidade == "salto_duplo" and not self.tem_salto_duplo:
            self.tem_salto_duplo = True
            self.pulos_maximos = 2
            self.pulos_restantes = max(self.pulos_restantes, 2)
        elif habilidade == "avanco":
            self.tem_avanco = True

    def pular(self):
        self.buffer_pulo = 0.10
        return self._tentar_executar_pulo()

    def _tentar_executar_pulo(self):
        if self.buffer_pulo <= 0:
            return False
        if self.escalando:
            self.escalando = False
            self.vel.y = -config.FORCA_PULO * 0.95
            self.buffer_pulo = 0.0
            self.pulos_restantes = max(0, self.pulos_maximos - 1)
            return True
        elif self.no_chao or self.coyote_tempo > 0:
            self.vel.y = -config.FORCA_PULO
            self.no_chao = False
            self.coyote_tempo = 0.0
            self.buffer_pulo = 0.0
            self.pulos_restantes = max(0, self.pulos_maximos - 1)
            return True
        elif self.na_parede != 0 or self.parede_coyote > 0:
            lado = self.na_parede if self.na_parede != 0 else self.ultima_parede_dir
            self.vel.y = -config.FORCA_PULO * 0.94
            self.vel.x = -lado * config.VELOCIDADE_JOGADOR * 1.15
            self.direcao = -lado
            self.recuo_parede = 0.14
            self.parede_coyote = 0.0
            self.buffer_pulo = 0.0
            self.pulos_restantes = max(0, self.pulos_maximos - 1)
            return True
        elif self.pulos_restantes > 0:
            self.vel.y = -config.FORCA_PULO
            self.pulos_restantes -= 1
            self.buffer_pulo = 0.0
            return True
        return False

    def avancar(self):
        if self.tem_avanco and self.recarga_avanco <= 0 and self.recuo <= 0:
            self.escalando = False
            self.tempo_avanco = config.AVANCO_DURACAO
            self.recarga_avanco = config.AVANCO_RECARGA
            self.invencivel = max(self.invencivel, config.AVANCO_DURACAO + 0.08)
            return True
        return False

    def atacar(self):
        """Espingarda calibre 12 na Fase 1; Besta de 3 virotes na Fase 3."""
        if self.tempo_recarga > 0:
            return []

        self.escalando = False
        boca_x = self.rect.centerx + 28 * self.direcao
        boca_y = self.rect.centery + 3

        if self.modo_arma == "besta":
            self.tempo_ataque = 0.14
            self.tempo_recarga = self.RECARGA_BESTA
            self.coice_tiro = -self.direcao * 45.0
            angulos = [-7.0, 0.0, 7.0]
            return [ViroteBesta(boca_x, boca_y, self.direcao, ang) for ang in angulos]

        # Espingarda Calibre 12 (Fase 1)
        self.tempo_ataque = 0.16
        self.tempo_recarga = self.RECARGA_12
        self.coice_tiro = -self.direcao * 115.0
        angulos = [-10, -4, 0, 4, 10]
        return [
            Tiro12(boca_x, boca_y, self.direcao, ang + random.uniform(-1.4, 1.4))
            for ang in angulos
        ]

    def receber_dano(self, dano, origem_x):
        if self.invencivel > 0 or self.avancando:
            return False
        self.escalando = False
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
        return None

    # ---------- atualização ----------
    def atualizar(self, dt, plataformas, largura_mundo, cipos=()):
        self.tempo_ataque = max(0.0, self.tempo_ataque - dt)
        self.tempo_recarga = max(0.0, self.tempo_recarga - dt)
        self.tempo_avanco = max(0.0, self.tempo_avanco - dt)
        self.recarga_avanco = max(0.0, self.recarga_avanco - dt)
        self.invencivel = max(0.0, self.invencivel - dt)
        self.coyote_tempo = max(0.0, self.coyote_tempo - dt)
        self.buffer_pulo = max(0.0, self.buffer_pulo - dt)
        self.parede_coyote = max(0.0, self.parede_coyote - dt)
        self.recuo_parede = max(0.0, self.recuo_parede - dt)

        if abs(self.coice_tiro) > 1.0:
            self.coice_tiro *= max(0.0, 1.0 - 14.0 * dt)
        else:
            self.coice_tiro = 0.0

        teclas = pygame.key.get_pressed()
        direcao = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            direcao -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            direcao += 1

        subindo = teclas[pygame.K_w] or teclas[pygame.K_UP]
        descendo = teclas[pygame.K_s] or teclas[pygame.K_DOWN]

        cipo_tocado = None
        for c in cipos:
            if self.rect.colliderect(c.rect):
                cipo_tocado = c
                break

        if cipo_tocado is not None and not self.avancando and self.recuo <= 0:
            if subindo or (descendo and not self.no_chao):
                self.escalando = True
        else:
            self.escalando = False

        if self.escalando:
            self.pulos_restantes = self.pulos_maximos
            self.vel.x = direcao * (config.VELOCIDADE_JOGADOR * 0.55)
            if direcao != 0:
                self.direcao = direcao
            if subindo:
                self.vel.y = -195.0
            elif descendo:
                self.vel.y = 215.0
            else:
                self.vel.y = 0.0

            if abs(self.vel.y) > 10 or abs(self.vel.x) > 10:
                self.anim_t += dt
        elif self.avancando:
            self.vel.x = self.direcao * config.AVANCO_VELOCIDADE
            self.vel.y = 0
        elif self.recuo > 0:
            self.recuo -= dt
        elif self.recuo_parede > 0:
            pass
        else:
            self.vel.x = direcao * config.VELOCIDADE_JOGADOR + self.coice_tiro
            if direcao != 0:
                self.direcao = direcao

        if not self.escalando:
            if abs(self.vel.x) > 10 and self.no_chao:
                self.anim_t += dt
            else:
                self.anim_t = 0.0

        if not self.avancando and not self.escalando:
            limite_queda = 125.0 if (self.na_parede != 0 and self.vel.y > 0) else config.VELOCIDADE_QUEDA_MAX
            self.vel.y = min(self.vel.y + config.GRAVIDADE * dt, limite_queda)

        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)
        self.na_parede = 0
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                if self.vel.x > 0:
                    self.rect.right = p.rect.left
                    self.na_parede = 1
                elif self.vel.x < 0:
                    self.rect.left = p.rect.right
                    self.na_parede = -1
                self.pos.x = self.rect.x

        if self.na_parede == 0 and not self.no_chao and direcao != 0:
            sonda_lat = self.rect.move(direcao * 2, 0)
            if any(sonda_lat.colliderect(p.rect) for p in plataformas):
                self.na_parede = direcao

        if self.na_parede != 0 and not self.no_chao:
            self.parede_coyote = 0.14
            self.ultima_parede_dir = self.na_parede

        estava_no_chao = self.no_chao
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

        if not self.no_chao and self.vel.y >= 0 and not self.escalando:
            sonda = self.rect.move(0, 1)
            if any(sonda.colliderect(p.rect) for p in plataformas):
                self.no_chao = True

        if self.no_chao:
            self.escalando = False
            self.na_parede = 0
            self.pulos_restantes = self.pulos_maximos
            self.coyote_tempo = 0.09
            if self.buffer_pulo > 0:
                self._tentar_executar_pulo()
        elif estava_no_chao and self.vel.y >= 0 and not self.escalando:
            self.pulos_restantes = min(self.pulos_restantes, max(1, self.pulos_maximos - 1))

        if self.buffer_pulo > 0 and (self.escalando or self.na_parede != 0 or self.parede_coyote > 0):
            self._tentar_executar_pulo()

        if self.rect.left < 0:
            self.rect.left = 0
            self.pos.x = self.rect.x
        if self.rect.right > largura_mundo:
            self.rect.right = largura_mundo
            self.pos.x = self.rect.x

    # ---------- desenho ----------
    def desenhar(self, tela, camera):
        if self.invencivel > 0 and not self.avancando and int(self.invencivel * 20) % 2 == 0:
            return

        rect = camera.aplicar(self.rect)
        self._desenhar_guerreira(tela, rect)

    def _desenhar_guerreira(self, tela, rect):
        """Desenha a Mulher Guerreira com Espingarda Calibre 12 (Fase 1) ou Besta (Fase 3)."""
        d = self.direcao
        cx = rect.centerx
        correndo = abs(self.vel.x) > 10
        escalando_ativo = self.escalando or (self.na_parede != 0 and not self.no_chao)
        passo = int(math.sin(self.anim_t * 15) * 4) if (self.no_chao or self.escalando) else 3
        balanco = int(math.sin(pygame.time.get_ticks() * 0.009) * 3) + (5 if correndo else 0)
        impulso_ar = -3 if not self.no_chao and self.vel.y < 0 else (3 if not self.no_chao else 0)

        cor_pele = (238, 194, 165)
        cor_pele_sombra = (206, 158, 130)
        cor_cabelo = (36, 18, 26)
        cor_cabelo_brilho = (74, 38, 52)
        cor_aco = (72, 78, 96)
        cor_aco_escuro = (42, 46, 58)
        cor_carmesim = (146, 26, 52)
        cor_carmesim_escuro = (96, 16, 36)

        if self.na_parede != 0 and not self.no_chao:
            parede_x = rect.right if self.na_parede == 1 else rect.left
            for i in range(3):
                fy = rect.y + 18 + i * 16 + int(math.sin(self.anim_t * 25 + i) * 4)
                pygame.draw.circle(tela, (255, 220, 130), (parede_x, fy), 2)

        if self.avancando:
            for k in (1, 2):
                rastro = pygame.Surface(rect.size, pygame.SRCALPHA)
                rastro.fill((0, 225, 255, 110 // k))
                tela.blit(rastro, (rect.x - d * 22 * k, rect.y))
            ponta_x = rect.right + 16 if d == 1 else rect.left - 16
            onda_dash = [
                (ponta_x, rect.centery),
                (rect.centerx + d * 8, rect.top - 4),
                (rect.centerx + d * 14, rect.centery),
                (rect.centerx + d * 8, rect.bottom + 4),
            ]
            pygame.draw.polygon(tela, (160, 250, 255), onda_dash)

        # 1. Capa espartana carmesim
        ombro_tras_x = cx - d * 6
        ponta_capa_x = cx - d * (19 + balanco)
        pygame.draw.polygon(tela, cor_carmesim_escuro, [
            (ombro_tras_x, rect.y + 18),
            (ponta_capa_x, rect.bottom - 6 + impulso_ar),
            (cx - d * 7, rect.bottom - 5),
        ])
        pygame.draw.polygon(tela, cor_carmesim, [
            (ombro_tras_x, rect.y + 18),
            (ponta_capa_x + d * 4, rect.bottom - 11 + impulso_ar),
            (cx - d * 3, rect.y + 37),
        ])

        # 2. Cabelo longo
        nuca_x = cx - d * 6
        nuca_y = rect.y + 7
        ponta_cabelo_x = cx - d * (18 + balanco)
        ponta_cabelo_y = rect.y + 27 + impulso_ar
        pygame.draw.polygon(tela, cor_cabelo, [
            (nuca_x, nuca_y - 2),
            (cx - d * (15 + balanco // 2), rect.y + 13),
            (ponta_cabelo_x, ponta_cabelo_y),
            (cx - d * (9 + balanco // 3), rect.y + 25),
            (nuca_x + d * 2, nuca_y + 6),
        ])
        pygame.draw.line(
            tela, cor_cabelo_brilho,
            (nuca_x - d * 2, nuca_y + 1),
            (ponta_cabelo_x + d * 3, ponta_cabelo_y - 3),
            2,
        )
        pygame.draw.circle(tela, config.DOURADO, (nuca_x - d * 1, nuca_y + 1), 3)

        # 3. Pernas e botas
        perna_tras_x = cx - 7 - passo
        perna_frente_x = cx + 1 + passo
        for idx, px in enumerate((perna_tras_x, perna_frente_x)):
            desloc_y = (passo if idx == 0 else -passo) if self.escalando else 0
            pygame.draw.rect(tela, cor_pele_sombra if idx == 0 else cor_pele, (px, rect.y + 36 + desloc_y, 6, 8), border_radius=2)
            pygame.draw.rect(tela, (34, 24, 32), (px, rect.y + 42 + desloc_y, 6, 14 - max(0, desloc_y)), border_radius=2)
            pygame.draw.rect(tela, (20, 14, 18), (px - 1, rect.bottom - 3, 8, 3))
            pygame.draw.rect(tela, config.DOURADO, (px - 1, rect.y + 41 + desloc_y, 8, 2))

        # 4. Saiote de guerra espartano
        pygame.draw.polygon(tela, cor_carmesim_escuro, [
            (cx - 7, rect.y + 31),
            (cx + 7, rect.y + 31),
            (cx + 12, rect.y + 41),
            (cx - 12, rect.y + 41),
        ])
        for tx in (cx - 8, cx - 3, cx + 3, cx + 8):
            pygame.draw.line(tela, config.DOURADO, (tx, rect.y + 33), (tx + (1 if tx > cx else -1), rect.y + 40), 1)
        pygame.draw.line(tela, config.DOURADO, (cx - 11, rect.y + 40), (cx + 11, rect.y + 40), 2)

        # 5. Torso e corselete
        pygame.draw.rect(tela, cor_pele_sombra, (cx - 3, rect.y + 14, 6, 4))
        corselete_pts = [
            (cx - 9, rect.y + 17),
            (cx + 9, rect.y + 17),
            (cx + 6, rect.y + 29),
            (cx - 6, rect.y + 29),
        ]
        pygame.draw.polygon(tela, cor_aco, corselete_pts)
        pygame.draw.polygon(tela, cor_aco_escuro, corselete_pts, 1)

        peito_frente_x = cx + d * 4
        pygame.draw.ellipse(tela, (92, 100, 120), (peito_frente_x - 4, rect.y + 18, 8, 6))
        pygame.draw.line(tela, config.DOURADO, (cx - 7, rect.y + 18), (cx, rect.y + 24), 2)
        pygame.draw.line(tela, config.DOURADO, (cx + 7, rect.y + 18), (cx, rect.y + 24), 2)

        pygame.draw.rect(tela, config.DOURADO, (cx - 6, rect.y + 28, 12, 3), border_radius=1)
        pygame.draw.circle(tela, (255, 235, 140), (cx + d * 2, rect.y + 29), 2)

        ombro_frente_x = cx - 2 if d == 1 else cx - 8
        pygame.draw.ellipse(tela, (96, 104, 124), (ombro_frente_x, rect.y + 15, 10, 7))
        pygame.draw.ellipse(tela, config.DOURADO, (ombro_frente_x, rect.y + 15, 10, 7), 1)

        # 6. Rosto e tiara
        cabeca = pygame.Rect(cx - 9, rect.y + 1, 18, 15)
        pygame.draw.ellipse(tela, cor_pele, cabeca)
        pygame.draw.polygon(tela, cor_pele, [
            (cabeca.x + 3, cabeca.bottom - 5),
            (cabeca.right - 3, cabeca.bottom - 5),
            (cx + d * 1, cabeca.bottom + 1),
        ])

        pygame.draw.ellipse(tela, cor_cabelo, (cabeca.x - 1, cabeca.y - 1, cabeca.width + 2, 7))
        mecha_x = cabeca.x + 1 if d == 1 else cabeca.right - 5
        pygame.draw.polygon(tela, cor_cabelo, [
            (mecha_x, cabeca.y + 4),
            (mecha_x + 4, cabeca.y + 4),
            (mecha_x + 2 - d * 2, cabeca.bottom + 3),
        ])

        pygame.draw.line(tela, config.DOURADO, (cabeca.x + 1, cabeca.y + 4), (cabeca.right - 1, cabeca.y + 4), 2)
        testa_x = cabeca.right - 5 if d == 1 else cabeca.left + 5
        pygame.draw.polygon(tela, config.DOURADO, [
            (testa_x - 2, cabeca.y + 4),
            (testa_x + 2, cabeca.y + 4),
            (testa_x, cabeca.y + 7),
        ])

        olho_x = cabeca.right - 7 if d == 1 else cabeca.left + 3
        pygame.draw.rect(tela, config.BRANCO, (olho_x, cabeca.y + 6, 4, 4))
        pygame.draw.rect(tela, (28, 42, 68), (olho_x + (1 if d == 1 else 0), cabeca.y + 6, 3, 4))
        pygame.draw.line(tela, (24, 14, 20), (olho_x - 1, cabeca.y + 6), (olho_x + 4, cabeca.y + 6), 1)
        pygame.draw.line(tela, cor_cabelo, (olho_x - 1, cabeca.y + 4), (olho_x + 4, cabeca.y + 5), 1)
        boca_r_x = cabeca.right - 5 if d == 1 else cabeca.left + 3
        pygame.draw.line(tela, (196, 102, 108), (boca_r_x, cabeca.bottom - 3), (boca_r_x + 2, cabeca.bottom - 3), 2)

        # 7. Escalando cipó ou grudada na parede
        if escalando_ativo:
            lado_agarre = self.na_parede if (self.na_parede != 0 and not self.escalando) else d
            pygame.draw.line(tela, (124, 66, 28), (cx - lado_agarre * 4, rect.y + 32), (cx - lado_agarre * 9, rect.y + 20), 4)
            pygame.draw.line(tela, (46, 52, 64), (cx - lado_agarre * 9, rect.y + 20), (cx - lado_agarre * 15, rect.y + 6), 3)
            mao_y1 = rect.y + 8 - passo
            mao_y2 = rect.y + 14 + passo
            pygame.draw.line(tela, cor_pele, (cx, rect.y + 20), (cx + lado_agarre * 11, mao_y1), 3)
            pygame.draw.line(tela, cor_pele_sombra, (cx, rect.y + 21), (cx + lado_agarre * 10, mao_y2), 3)
            pygame.draw.circle(tela, cor_pele, (cx + lado_agarre * 11, mao_y1), 3)
            pygame.draw.circle(tela, cor_pele_sombra, (cx + lado_agarre * 10, mao_y2), 3)
            return

        # 8. Desenho da Arma: Besta de 3 tiros (Fase 3) ou Espingarda Calibre 12 (Fase 1)
        recuo_arma = -3 * d if self.atacando else 0
        arma_y = rect.centery + 3
        ax = cx + recuo_arma

        if self.modo_arma == "besta":
            self._desenhar_besta(tela, cx, ax, arma_y, d, cor_pele)
            recarga_ref = self.RECARGA_BESTA
        else:
            self._desenhar_espingarda(tela, cx, ax, arma_y, d, cor_pele)
            recarga_ref = self.RECARGA_12

        if self.tempo_recarga > 0:
            larg = 28
            progresso = 1.0 - min(1.0, self.tempo_recarga / recarga_ref)
            bx = cx - larg // 2
            by = rect.y - 10
            pygame.draw.rect(tela, (25, 20, 26), (bx - 1, by - 1, larg + 2, 5), border_radius=2)
            pygame.draw.rect(tela, config.DOURADO, (bx, by, int(larg * progresso), 3), border_radius=1)

    def _desenhar_besta(self, tela, cx, ax, arma_y, d, cor_pele):
        """Desenha a Besta de repetição com arco frontal e 3 virotes."""
        cor_madeira = (118, 62, 28)
        cor_madeira_escura = (76, 38, 16)
        cor_aco = (150, 162, 180)

        if d == 1:
            pygame.draw.polygon(tela, cor_madeira, [
                (ax - 12, arma_y + 6),
                (ax - 12, arma_y - 1),
                (ax + 24, arma_y - 1),
                (ax + 24, arma_y + 3),
                (ax - 2, arma_y + 4),
            ])
            pygame.draw.line(tela, cor_madeira_escura, (ax - 12, arma_y + 2), (ax + 22, arma_y + 2), 1)
            pygame.draw.lines(tela, cor_aco, False, [
                (ax + 15, arma_y - 13),
                (ax + 24, arma_y - 6),
                (ax + 26, arma_y + 1),
                (ax + 24, arma_y + 8),
                (ax + 15, arma_y + 15),
            ], 3)
            ponto_corda = (ax + 21, arma_y + 1) if self.atacando else (ax + 4, arma_y + 1)
            pygame.draw.line(tela, (230, 230, 220), (ax + 15, arma_y - 13), ponto_corda, 1)
            pygame.draw.line(tela, (230, 230, 220), (ax + 15, arma_y + 15), ponto_corda, 1)
            if not self.atacando:
                pygame.draw.line(tela, (220, 235, 245), (ax + 6, arma_y - 2), (ax + 29, arma_y - 2), 2)
            pygame.draw.line(tela, cor_pele, (cx + 2, arma_y - 10), (ax + 13, arma_y + 3), 3)
            pygame.draw.circle(tela, cor_pele, (ax - 1, arma_y + 3), 3)
            pygame.draw.circle(tela, cor_pele, (ax + 14, arma_y + 3), 3)
        else:
            pygame.draw.polygon(tela, cor_madeira, [
                (ax + 12, arma_y + 6),
                (ax + 12, arma_y - 1),
                (ax - 24, arma_y - 1),
                (ax - 24, arma_y + 3),
                (ax + 2, arma_y + 4),
            ])
            pygame.draw.line(tela, cor_madeira_escura, (ax + 12, arma_y + 2), (ax - 22, arma_y + 2), 1)
            pygame.draw.lines(tela, cor_aco, False, [
                (ax - 15, arma_y - 13),
                (ax - 24, arma_y - 6),
                (ax - 26, arma_y + 1),
                (ax - 24, arma_y + 8),
                (ax - 15, arma_y + 15),
            ], 3)
            ponto_corda = (ax - 21, arma_y + 1) if self.atacando else (ax - 4, arma_y + 1)
            pygame.draw.line(tela, (230, 230, 220), (ax - 15, arma_y - 13), ponto_corda, 1)
            pygame.draw.line(tela, (230, 230, 220), (ax - 15, arma_y + 15), ponto_corda, 1)
            if not self.atacando:
                pygame.draw.line(tela, (220, 235, 245), (ax - 6, arma_y - 2), (ax - 29, arma_y - 2), 2)
            pygame.draw.line(tela, cor_pele, (cx - 2, arma_y - 10), (ax - 13, arma_y + 3), 3)
            pygame.draw.circle(tela, cor_pele, (ax + 1, arma_y + 3), 3)
            pygame.draw.circle(tela, cor_pele, (ax - 14, arma_y + 3), 3)

    def _desenhar_espingarda(self, tela, cx, ax, arma_y, d, cor_pele):
        """Desenha a Espingarda Calibre 12."""
        if d == 1:
            pygame.draw.polygon(tela, (124, 66, 28), [
                (ax - 14, arma_y + 7),
                (ax - 14, arma_y - 1),
                (ax - 2, arma_y - 1),
                (ax - 4, arma_y + 5),
            ])
            pygame.draw.line(tela, (40, 22, 12), (ax - 14, arma_y - 1), (ax - 14, arma_y + 7), 2)
            pygame.draw.rect(tela, (56, 62, 74), (ax - 3, arma_y - 2, 13, 6), border_radius=2)
            pygame.draw.rect(tela, (150, 160, 175), (ax + 1, arma_y, 5, 2))
            pygame.draw.rect(tela, (36, 40, 48), (ax + 10, arma_y - 2, 23, 3))
            pygame.draw.rect(tela, (62, 68, 80), (ax + 10, arma_y + 2, 20, 2))
            pygame.draw.rect(tela, (138, 76, 32), (ax + 12, arma_y + 1, 10, 4), border_radius=1)
            for rx in (ax + 14, ax + 17, ax + 20):
                pygame.draw.line(tela, (75, 38, 15), (rx, arma_y + 1), (rx, arma_y + 4), 1)
            pygame.draw.rect(tela, config.DOURADO, (ax + 31, arma_y - 4, 2, 2))
            pygame.draw.line(tela, cor_pele, (cx + 2, arma_y - 10), (ax + 15, arma_y + 3), 3)
            pygame.draw.circle(tela, cor_pele, (ax - 1, arma_y + 3), 3)
            pygame.draw.circle(tela, cor_pele, (ax + 16, arma_y + 3), 3)
            boca_x = ax + 34
        else:
            pygame.draw.polygon(tela, (124, 66, 28), [
                (ax + 14, arma_y + 7),
                (ax + 14, arma_y - 1),
                (ax + 2, arma_y - 1),
                (ax + 4, arma_y + 5),
            ])
            pygame.draw.line(tela, (40, 22, 12), (ax + 14, arma_y - 1), (ax + 14, arma_y + 7), 2)
            pygame.draw.rect(tela, (56, 62, 74), (ax - 10, arma_y - 2, 13, 6), border_radius=2)
            pygame.draw.rect(tela, (150, 160, 175), (ax - 6, arma_y, 5, 2))
            pygame.draw.rect(tela, (36, 40, 48), (ax - 33, arma_y - 2, 23, 3))
            pygame.draw.rect(tela, (62, 68, 80), (ax - 30, arma_y + 2, 20, 2))
            pygame.draw.rect(tela, (138, 76, 32), (ax - 22, arma_y + 1, 10, 4), border_radius=1)
            for rx in (ax - 20, ax - 17, ax - 14):
                pygame.draw.line(tela, (75, 38, 15), (rx, arma_y + 1), (rx, arma_y + 4), 1)
            pygame.draw.rect(tela, config.DOURADO, (ax - 33, arma_y - 4, 2, 2))
            pygame.draw.line(tela, cor_pele, (cx - 2, arma_y - 10), (ax - 15, arma_y + 3), 3)
            pygame.draw.circle(tela, cor_pele, (ax + 1, arma_y + 3), 3)
            pygame.draw.circle(tela, cor_pele, (ax - 16, arma_y + 3), 3)
            boca_x = ax - 34

        if self.atacando:
            by = arma_y
            pygame.draw.polygon(tela, (255, 110, 20), [
                (boca_x, by),
                (boca_x + d * 24, by - 12),
                (boca_x + d * 20, by),
                (boca_x + d * 24, by + 12),
            ])
            pygame.draw.polygon(tela, (255, 215, 70), [
                (boca_x, by),
                (boca_x + d * 15, by - 6),
                (boca_x + d * 15, by + 6),
            ])
            pygame.draw.circle(tela, config.BRANCO, (boca_x + d * 3, by), 4)


class JogadorPlasma:
    """Guerreira da Fase 2: rifle de plasma, escada, dash hitkill, salto duplo e parkour de parede."""

    LARGURA = 40
    ALTURA = 66

    def __init__(self, x, y):
        self.inicio = (x, y)
        self.rect = pygame.Rect(x, y, self.LARGURA, self.ALTURA)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.no_chao = False
        self.direcao = 1
        self.estilo = "padrao"
        self.modo_guerreira = True
        self.anim_t = 0.0
        self.recuo_arma = 0.0

        self.na_parede = 0
        self.trava_wall_jump = 0.0
        self.na_escada = False

        self.tem_salto_duplo = True
        self.pulos_maximos = 2
        self.pulos_restantes = 2

        self.tem_avanco = True
        self.tempo_avanco = 0.0
        self.recarga_avanco = 0.0

        self.vida_max = config.VIDA_JOGADOR
        self.vida = self.vida_max
        self.tempo_ataque = 0.0
        self.tempo_recarga = 0.0
        self.alvos_acertados = set()
        self.invencivel = 0.0
        self.recuo = 0.0

    def reiniciar(self):
        self.pos.update(self.inicio)
        self.rect.topleft = self.inicio
        self.vel.update(0, 0)
        self.tempo_ataque = 0.0
        self.tempo_avanco = 0.0
        self.recuo = 0.0
        self.na_escada = False
        self.na_parede = 0
        self.invencivel = config.TEMPO_INVENCIVEL

    def desbloquear(self, habilidade):
        if habilidade == "salto_duplo" and not self.tem_salto_duplo:
            self.tem_salto_duplo = True
            self.pulos_maximos = 2
            self.pulos_restantes = 2
        elif habilidade == "avanco":
            self.tem_avanco = True

    def pular(self):
        if self.na_parede != 0 and not self.no_chao:
            lado_oposto = -self.na_parede
            self.vel.y = -config.FORCA_PULO * 0.96
            self.vel.x = lado_oposto * (config.VELOCIDADE_JOGADOR * 1.25)
            self.direcao = lado_oposto
            self.trava_wall_jump = 0.16
            self.na_parede = 0
            self.pulos_restantes = max(1, self.pulos_maximos - 1)
            return True

        if self.na_escada:
            self.na_escada = False
            self.vel.y = -config.FORCA_PULO * 0.85
            self.pulos_restantes = max(1, self.pulos_maximos - 1)
            return True

        if self.pulos_restantes > 0:
            self.vel.y = -config.FORCA_PULO
            self.pulos_restantes -= 1
            return True
        return False

    def avancar(self):
        if self.tem_avanco and self.recarga_avanco <= 0 and self.recuo <= 0:
            self.na_escada = False
            self.tempo_avanco = config.AVANCO_DURACAO
            self.recarga_avanco = config.AVANCO_RECARGA
            self.invencivel = max(self.invencivel, config.AVANCO_DURACAO + 0.08)
            return True
        return False

    def atacar(self):
        if self.tempo_recarga <= 0:
            if self.estilo == "guerreira":
                self.tempo_ataque = 0.14
                self.tempo_recarga = 0.24
                self.recuo_arma = 6.0
                return True
            else:
                self.tempo_ataque = config.ATAQUE_DURACAO
                self.tempo_recarga = config.ATAQUE_RECARGA
                self.alvos_acertados.clear()
        return False

    def receber_dano(self, dano, origem_x):
        if self.invencivel > 0 or self.avancando:
            return False
        self.vida -= dano
        self.invencivel = config.TEMPO_INVENCIVEL
        self.na_escada = False
        sentido = 1 if self.rect.centerx >= origem_x else -1
        self.vel.x = sentido * config.RECUO_X
        self.vel.y = -config.RECUO_Y
        self.recuo = 0.2
        return True

    @property
    def escalando(self):
        return self.na_escada

    @property
    def avancando(self):
        return self.tempo_avanco > 0

    @property
    def atacando(self):
        return self.tempo_ataque > 0

    @property
    def hitbox_ataque(self):
        return None

    def atualizar(self, dt, plataformas, largura_mundo, escadas=None):
        escadas = escadas or []
        self.anim_t += dt
        self.tempo_ataque = max(0.0, self.tempo_ataque - dt)
        self.tempo_recarga = max(0.0, self.tempo_recarga - dt)
        self.tempo_avanco = max(0.0, self.tempo_avanco - dt)
        self.recarga_avanco = max(0.0, self.recarga_avanco - dt)
        self.invencivel = max(0.0, self.invencivel - dt)
        self.recuo_arma = max(0.0, self.recuo_arma - 35 * dt)
        self.trava_wall_jump = max(0.0, self.trava_wall_jump - dt)

        teclas = pygame.key.get_pressed()
        dir_x = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dir_x -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dir_x += 1

        dir_y = 0
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dir_y -= 1
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dir_y += 1

        escada_atual = next((esc for esc in escadas if self.rect.colliderect(esc.rect)), None)
        if escada_atual and dir_y != 0 and not self.avancando:
            self.na_escada = True
            self.na_parede = 0
        elif not escada_atual:
            self.na_escada = False

        if self.avancando:
            self.vel.x = self.direcao * config.AVANCO_VELOCIDADE
            self.vel.y = 0
        elif self.recuo > 0:
            self.recuo -= dt
        elif self.trava_wall_jump <= 0:
            velocidade_atual = config.VELOCIDADE_JOGADOR * (0.65 if self.na_escada else 1.0)
            self.vel.x = dir_x * velocidade_atual
            if dir_x != 0:
                self.direcao = dir_x

        if self.na_escada:
            self.vel.y = dir_y * 210
            self.pulos_restantes = self.pulos_maximos
        elif not self.avancando:
            self.vel.y = min(self.vel.y + config.GRAVIDADE * dt, config.VELOCIDADE_QUEDA_MAX)
            if self.na_parede != 0 and not self.no_chao and self.vel.y > 115:
                self.vel.y = 115

        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)
        encostou_parede = 0
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                if self.vel.x > 0:
                    self.rect.right = p.rect.left
                    encostou_parede = 1
                elif self.vel.x < 0:
                    self.rect.left = p.rect.right
                    encostou_parede = -1
                self.pos.x = self.rect.x

        if not self.no_chao and not self.na_escada:
            if encostou_parede != 0 and dir_x == encostou_parede:
                self.na_parede = encostou_parede
            else:
                sonda_dir = self.rect.move(2, 0)
                sonda_esq = self.rect.move(-2, 0)
                if dir_x == 1 and any(sonda_dir.colliderect(p.rect) for p in plataformas):
                    self.na_parede = 1
                elif dir_x == -1 and any(sonda_esq.colliderect(p.rect) for p in plataformas):
                    self.na_parede = -1
                else:
                    self.na_parede = 0
        else:
            self.na_parede = 0

        estava_no_chao = self.no_chao
        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)
        self.no_chao = False
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                if self.vel.y > 0:
                    self.rect.bottom = p.rect.top
                    self.no_chao = True
                    self.na_escada = False
                elif self.vel.y < 0:
                    self.rect.top = p.rect.bottom
                self.vel.y = 0
                self.pos.y = self.rect.y

        if not self.no_chao and self.vel.y >= 0 and not self.na_escada:
            sonda = self.rect.move(0, 1)
            if any(sonda.colliderect(p.rect) for p in plataformas):
                self.no_chao = True

        if self.no_chao:
            self.pulos_restantes = self.pulos_maximos
        elif estava_no_chao and self.vel.y >= 0 and not self.na_escada:
            self.pulos_restantes = min(self.pulos_restantes, max(1, self.pulos_maximos - 1))

        if self.rect.left < 0:
            self.rect.left = 0
            self.pos.x = self.rect.x
        if self.rect.right > largura_mundo:
            self.rect.right = largura_mundo
            self.pos.x = self.rect.x

    def _desenhar_guerreira(self, tela, rect):
        """Corpo da guerreira segurando o rifle de plasma da Fase 2."""
        d = self.direcao
        cx = rect.centerx
        correndo = abs(self.vel.x) > 10
        andando = correndo and self.no_chao
        subindo = self.escalando and abs(self.vel.y) > 5
        escalando_ativo = self.escalando or (self.na_parede != 0 and not self.no_chao)
        passo = int(math.sin(self.anim_t * 15) * 4) if (andando or subindo) else (0 if self.no_chao else 3)
        balanco = int(math.sin(pygame.time.get_ticks() * 0.009) * 3) + (5 if correndo else 0)
        impulso_ar = -3 if not self.no_chao and self.vel.y < 0 else (3 if not self.no_chao else 0)

        cor_pele = (238, 194, 165)
        cor_pele_sombra = (206, 158, 130)
        cor_cabelo = (36, 18, 26)
        cor_cabelo_brilho = (74, 38, 52)
        cor_aco = (72, 78, 96)
        cor_aco_escuro = (42, 46, 58)
        cor_carmesim = (146, 26, 52)
        cor_carmesim_escuro = (96, 16, 36)

        luz = pygame.Surface((110, 110), pygame.SRCALPHA)
        pygame.draw.circle(luz, (0, 190, 255, 24), (55, 55), 50)
        tela.blit(luz, (cx - 55 + d * 12, rect.y + 23 - 55))

        if self.tem_avanco and self.recarga_avanco <= 0 and not self.avancando:
            pulso_dash = int(math.sin(self.anim_t * 8) * 3)
            anel = pygame.Surface((46, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(anel, (0, 235, 255, 130), (2 - pulso_dash // 2, 2, 42 + pulso_dash, 10), 2)
            tela.blit(anel, (cx - 23, rect.bottom - 7))

        if self.na_parede != 0 and not self.no_chao:
            parede_x = rect.right if self.na_parede == 1 else rect.left
            for i in range(3):
                fy = rect.y + 18 + i * 16 + int(math.sin(self.anim_t * 25 + i) * 4)
                pygame.draw.circle(tela, (120, 235, 255), (parede_x, fy), 2)

        if self.avancando:
            for k in (1, 2):
                rastro = pygame.Surface(rect.size, pygame.SRCALPHA)
                rastro.fill((0, 225, 255, 110 // k))
                tela.blit(rastro, (rect.x - d * 22 * k, rect.y))
            ponta_x = rect.right + 16 if d == 1 else rect.left - 16
            onda_dash = [
                (ponta_x, rect.centery),
                (rect.centerx + d * 8, rect.top - 4),
                (rect.centerx + d * 14, rect.centery),
                (rect.centerx + d * 8, rect.bottom + 4),
            ]
            pygame.draw.polygon(tela, (160, 250, 255), onda_dash)

        ombro_tras_x = cx - d * 6
        ponta_capa_x = cx - d * (19 + balanco)
        pygame.draw.polygon(tela, cor_carmesim_escuro, [
            (ombro_tras_x, rect.y + 18),
            (ponta_capa_x, rect.bottom - 6 + impulso_ar),
            (cx - d * 7, rect.bottom - 5),
        ])
        pygame.draw.polygon(tela, cor_carmesim, [
            (ombro_tras_x, rect.y + 18),
            (ponta_capa_x + d * 4, rect.bottom - 11 + impulso_ar),
            (cx - d * 3, rect.y + 37),
        ])

        nuca_x = cx - d * 6
        nuca_y = rect.y + 7
        ponta_cabelo_x = cx - d * (18 + balanco)
        ponta_cabelo_y = rect.y + 27 + impulso_ar
        pygame.draw.polygon(tela, cor_cabelo, [
            (nuca_x, nuca_y - 2),
            (cx - d * (15 + balanco // 2), rect.y + 13),
            (ponta_cabelo_x, ponta_cabelo_y),
            (cx - d * (9 + balanco // 3), rect.y + 25),
            (nuca_x + d * 2, nuca_y + 6),
        ])
        pygame.draw.line(
            tela, cor_cabelo_brilho,
            (nuca_x - d * 2, nuca_y + 1),
            (ponta_cabelo_x + d * 3, ponta_cabelo_y - 3),
            2,
        )
        pygame.draw.circle(tela, config.DOURADO, (nuca_x - d * 1, nuca_y + 1), 3)

        perna_tras_x = cx - 7 - passo
        perna_frente_x = cx + 1 + passo
        for idx, px in enumerate((perna_tras_x, perna_frente_x)):
            desloc_y = (passo if idx == 0 else -passo) if self.escalando else 0
            pygame.draw.rect(tela, cor_pele_sombra if idx == 0 else cor_pele, (px, rect.y + 36 + desloc_y, 6, 8), border_radius=2)
            pygame.draw.rect(tela, (34, 24, 32), (px, rect.y + 42 + desloc_y, 6, 14 - max(0, desloc_y)), border_radius=2)
            pygame.draw.rect(tela, (20, 14, 18), (px - 1, rect.bottom - 3, 8, 3))
            pygame.draw.rect(tela, config.DOURADO, (px - 1, rect.y + 41 + desloc_y, 8, 2))

        pygame.draw.polygon(tela, cor_carmesim_escuro, [
            (cx - 7, rect.y + 31),
            (cx + 7, rect.y + 31),
            (cx + 12, rect.y + 41),
            (cx - 12, rect.y + 41),
        ])
        for tx in (cx - 8, cx - 3, cx + 3, cx + 8):
            pygame.draw.line(tela, config.DOURADO, (tx, rect.y + 33), (tx + (1 if tx > cx else -1), rect.y + 40), 1)
        pygame.draw.line(tela, config.DOURADO, (cx - 11, rect.y + 40), (cx + 11, rect.y + 40), 2)

        pygame.draw.rect(tela, cor_pele_sombra, (cx - 3, rect.y + 14, 6, 4))
        corselete_pts = [
            (cx - 9, rect.y + 17),
            (cx + 9, rect.y + 17),
            (cx + 6, rect.y + 29),
            (cx - 6, rect.y + 29),
        ]
        pygame.draw.polygon(tela, cor_aco, corselete_pts)
        pygame.draw.polygon(tela, cor_aco_escuro, corselete_pts, 1)

        peito_frente_x = cx + d * 4
        pygame.draw.ellipse(tela, (92, 100, 120), (peito_frente_x - 4, rect.y + 18, 8, 6))
        pygame.draw.line(tela, config.DOURADO, (cx - 7, rect.y + 18), (cx, rect.y + 24), 2)
        pygame.draw.line(tela, config.DOURADO, (cx + 7, rect.y + 18), (cx, rect.y + 24), 2)

        pygame.draw.rect(tela, config.DOURADO, (cx - 6, rect.y + 28, 12, 3), border_radius=1)
        pygame.draw.circle(tela, (255, 235, 140), (cx + d * 2, rect.y + 29), 2)

        ombro_frente_x = cx - 2 if d == 1 else cx - 8
        pygame.draw.ellipse(tela, (96, 104, 124), (ombro_frente_x, rect.y + 15, 10, 7))
        pygame.draw.ellipse(tela, config.DOURADO, (ombro_frente_x, rect.y + 15, 10, 7), 1)

        cabeca = pygame.Rect(cx - 9, rect.y + 1, 18, 15)
        pygame.draw.ellipse(tela, cor_pele, cabeca)
        pygame.draw.polygon(tela, cor_pele, [
            (cabeca.x + 3, cabeca.bottom - 5),
            (cabeca.right - 3, cabeca.bottom - 5),
            (cx + d * 1, cabeca.bottom + 1),
        ])

        pygame.draw.ellipse(tela, cor_cabelo, (cabeca.x - 1, cabeca.y - 1, cabeca.width + 2, 7))
        mecha_x = cabeca.x + 1 if d == 1 else cabeca.right - 5
        pygame.draw.polygon(tela, cor_cabelo, [
            (mecha_x, cabeca.y + 4),
            (mecha_x + 4, cabeca.y + 4),
            (mecha_x + 2 - d * 2, cabeca.bottom + 3),
        ])

        pygame.draw.line(tela, config.DOURADO, (cabeca.x + 1, cabeca.y + 4), (cabeca.right - 1, cabeca.y + 4), 2)
        testa_x = cabeca.right - 5 if d == 1 else cabeca.left + 5
        pygame.draw.polygon(tela, config.DOURADO, [
            (testa_x - 2, cabeca.y + 4),
            (testa_x + 2, cabeca.y + 4),
            (testa_x, cabeca.y + 7),
        ])

        olho_x = cabeca.right - 7 if d == 1 else cabeca.left + 3
        pygame.draw.rect(tela, config.BRANCO, (olho_x, cabeca.y + 6, 4, 4))
        pygame.draw.rect(tela, (28, 42, 68), (olho_x + (1 if d == 1 else 0), cabeca.y + 6, 3, 4))
        pygame.draw.line(tela, (24, 14, 20), (olho_x - 1, cabeca.y + 6), (olho_x + 4, cabeca.y + 6), 1)
        pygame.draw.line(tela, cor_cabelo, (olho_x - 1, cabeca.y + 4), (olho_x + 4, cabeca.y + 5), 1)
        boca_r_x = cabeca.right - 5 if d == 1 else cabeca.left + 3
        pygame.draw.line(tela, (196, 102, 108), (boca_r_x, cabeca.bottom - 3), (boca_r_x + 2, cabeca.bottom - 3), 2)

        if escalando_ativo:
            lado_agarre = self.na_parede if (self.na_parede != 0 and not self.escalando) else d
            pygame.draw.line(tela, (28, 34, 46), (cx - lado_agarre * 4, rect.y + 32), (cx - lado_agarre * 9, rect.y + 20), 5)
            pygame.draw.line(tela, (28, 34, 46), (cx - lado_agarre * 9, rect.y + 20), (cx - lado_agarre * 15, rect.y + 6), 4)
            pygame.draw.line(tela, (0, 235, 255), (cx - lado_agarre * 7, rect.y + 25), (cx - lado_agarre * 11, rect.y + 17), 2)
            mao_y1 = rect.y + 8 - passo
            mao_y2 = rect.y + 14 + passo
            pygame.draw.line(tela, cor_pele, (cx, rect.y + 20), (cx + lado_agarre * 11, mao_y1), 3)
            pygame.draw.line(tela, cor_pele_sombra, (cx, rect.y + 21), (cx + lado_agarre * 10, mao_y2), 3)
            pygame.draw.circle(tela, cor_pele, (cx + lado_agarre * 11, mao_y1), 3)
            pygame.draw.circle(tela, cor_pele_sombra, (cx + lado_agarre * 10, mao_y2), 3)
            return

        rec = int(self.recuo_arma) * d
        arma_y = rect.y + 17
        arma_x = (cx - 3 - rec) if d == 1 else (cx - 33 - rec)
        pygame.draw.rect(tela, (28, 34, 46), (arma_x, arma_y, 36, 9), border_radius=3)
        pygame.draw.rect(tela, (145, 160, 185), (arma_x + (4 if d == 1 else 2), arma_y + 1, 28, 4), border_radius=2)
        celula_x = arma_x + (14 if d == 1 else 10)
        pygame.draw.rect(tela, (0, 235, 255), (celula_x, arma_y + 3, 12, 3), border_radius=2)

        mao_tras = (arma_x + (7 if d == 1 else 29), arma_y + 7)
        mao_frente = (arma_x + (25 if d == 1 else 11), arma_y + 7)
        pygame.draw.line(tela, cor_pele, (cx + d * 2, rect.y + 20), mao_frente, 3)
        pygame.draw.circle(tela, cor_pele, mao_tras, 3)
        pygame.draw.circle(tela, cor_pele, mao_frente, 3)

        if self.atacando:
            boca_x = arma_x + 36 if d == 1 else arma_x
            flash = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(flash, (0, 220, 255, 140), (18, 18), 16)
            pygame.draw.circle(flash, (255, 255, 255, 240), (18, 18), 8)
            tela.blit(flash, (boca_x - 18, arma_y + 4 - 18))

    def desenhar(self, tela, camera):
        if self.invencivel > 0 and not self.avancando and int(self.invencivel * 20) % 2 == 0:
            return

        rect = camera.aplicar(self.rect)

        if self.estilo == "guerreira":
            ALTURA_VISUAL = 56
            visual = pygame.Rect(rect.x, rect.bottom - ALTURA_VISUAL, rect.width, ALTURA_VISUAL)
            self._desenhar_guerreira(tela, visual)
        else:
            pygame.draw.rect(tela, config.VERMELHO, rect)
            olho_x = rect.right - 14 if self.direcao == 1 else rect.left + 6
            pygame.draw.rect(tela, config.BRANCO, (olho_x, rect.y + 10, 8, 8))