import math
import pygame
import config


class Jogador:
    LARGURA = 40
    ALTURA = 66

    def __init__(self, x, y):
        self.inicio = (x, y)
        self.rect = pygame.Rect(x, y, self.LARGURA, self.ALTURA)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.no_chao = False
        self.direcao = 1
        self.estilo = "padrao"  # "guerreira" na fase 2
        self.anim_t = 0.0
        self.recuo_arma = 0.0

        # Parkour (parede e escada)
        self.na_parede = 0
        self.trava_wall_jump = 0.0
        self.na_escada = False

        self.pulos_maximos = 1
        self.pulos_restantes = 1

        self.tem_salto_duplo = False
        self.tem_avanco = False
        self.tempo_avanco = 0.0
        self.recarga_avanco = 0.0

        self.vida = config.VIDA_JOGADOR
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
    def avancando(self):
        return self.tempo_avanco > 0

    @property
    def atacando(self):
        return self.tempo_ataque > 0

    @property
    def hitbox_ataque(self):
        if self.estilo == "guerreira" or not self.atacando:
            return None
        alcance, altura = config.ATAQUE_ALCANCE, 40
        if self.direcao == 1:
            area = pygame.Rect(self.rect.right, 0, alcance, altura)
        else:
            area = pygame.Rect(self.rect.left - alcance, 0, alcance, altura)
        area.centery = self.rect.centery
        return area

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
        andando = abs(self.vel.x) > 10 and self.no_chao
        escalando = self.na_escada and abs(self.vel.y) > 5
        passo = math.sin(self.anim_t * 14) * 5 if (andando or escalando) else 0
        respirar = math.sin(self.anim_t * 4) * 1.2
        d = self.direcao
        cx = rect.centerx

        # Aura da arma de plasma
        luz = pygame.Surface((110, 110), pygame.SRCALPHA)
        pygame.draw.circle(luz, (0, 190, 255, 24), (55, 55), 50)
        tela.blit(luz, (cx - 55 + d * 12, rect.centery - 55))

        # Indicador visual discreto nos pés quando o Dash Hitkill está carregado
        if self.tem_avanco and self.recarga_avanco <= 0 and not self.avancando:
            pulso_dash = int(math.sin(self.anim_t * 8) * 3)
            anel = pygame.Surface((46, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(anel, (0, 235, 255, 130), (2 - pulso_dash // 2, 2, 42 + pulso_dash, 10), 2)
            tela.blit(anel, (cx - 23, rect.bottom - 7))

        # Faíscas quando está grudada deslizando na parede
        if self.na_parede != 0 and not self.no_chao:
            parede_x = rect.right if self.na_parede == 1 else rect.left
            for i in range(3):
                fy = rect.y + 18 + i * 16 + int(math.sin(self.anim_t * 25 + i) * 4)
                pygame.draw.circle(tela, (120, 235, 255), (parede_x, fy), 2)

        # Rastro cibernético + lâmina frontal de energia durante o Dash Hitkill
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

        # Cabelo longo feminino esvoaçante
        onda = math.sin(self.anim_t * 9) * 4
        pts_cabelo = [
            (cx - d * 2, rect.y + 6),
            (cx - d * 18, rect.y + 12 + onda),
            (cx - d * 26, rect.y + 34 - onda),
            (cx - d * 22, rect.y + 48 + onda),
            (cx - d * 10, rect.y + 42),
            (cx - d * 6, rect.y + 22),
        ]
        pygame.draw.polygon(tela, (145, 28, 48), pts_cabelo)
        pygame.draw.lines(tela, (215, 75, 95), False, pts_cabelo[:4], 2)

        # Pernas e botas altas até o joelho
        perna_esq_x = cx - 6 + int(passo)
        perna_dir_x = cx + 1 - int(passo)
        pygame.draw.rect(tela, (42, 46, 62), (perna_esq_x, rect.y + 40, 6, 12), border_radius=2)
        pygame.draw.rect(tela, (58, 64, 84), (perna_dir_x, rect.y + 40, 6, 12), border_radius=2)
        pygame.draw.rect(tela, (115, 130, 155), (perna_esq_x - 1, rect.y + 50, 8, 16), border_radius=3)
        pygame.draw.rect(tela, (155, 172, 198), (perna_dir_x - 1, rect.y + 50, 8, 16), border_radius=3)

        # Saiote / Capa tática na cintura
        saiote = [
            (cx - 10, rect.y + 37),
            (cx + 10, rect.y + 37),
            (cx + 13 - d * 3, rect.y + 47),
            (cx - 13 - d * 3, rect.y + 47),
        ]
        pygame.draw.polygon(tela, (36, 44, 62), saiote)
        pygame.draw.line(tela, (0, 215, 255), (cx - 10, rect.y + 38), (cx + 10, rect.y + 38), 2)

        # Tronco feminino
        tronco = [
            (cx - 11, rect.y + 20 + int(respirar)),
            (cx + 11, rect.y + 20 + int(respirar)),
            (cx + 8, rect.y + 38 + int(respirar)),
            (cx - 8, rect.y + 38 + int(respirar)),
        ]
        pygame.draw.polygon(tela, (55, 68, 92), tronco)
        peito_x = cx + (1 if d == 1 else -11)
        pygame.draw.ellipse(tela, (165, 185, 215), (peito_x, rect.y + 22 + int(respirar), 11, 10))
        pygame.draw.circle(tela, (0, 235, 255), (cx + d * 4, rect.y + 27 + int(respirar)), 2)

        # Rosto feminino exposto com tiara de batalha
        cabeca = pygame.Rect(cx - 9, rect.y + 2 + int(respirar), 18, 19)
        pygame.draw.ellipse(tela, (238, 198, 176), cabeca)
        franja = [
            (cabeca.left, cabeca.y + 7),
            (cabeca.centerx, cabeca.y),
            (cabeca.right, cabeca.y + 6),
            (cabeca.centerx - d * 2, cabeca.y + 8),
        ]
        pygame.draw.polygon(tela, (155, 32, 52), franja)
        pygame.draw.line(tela, config.DOURADO, (cabeca.left + 1, cabeca.y + 5), (cabeca.right - 1, cabeca.y + 5), 2)
        olho_x = cabeca.right - 7 if d == 1 else cabeca.left + 4
        pygame.draw.rect(tela, (30, 40, 60), (olho_x, cabeca.y + 9, 4, 4), border_radius=1)
        pygame.draw.rect(tela, (0, 220, 255), (olho_x + (1 if d == 1 else 0), cabeca.y + 10, 2, 2))

        ombro_x = cx - 9 if d == 1 else cx - 2
        pygame.draw.ellipse(tela, (185, 200, 225), (ombro_x, rect.y + 19 + int(respirar), 11, 8))

        # Rifle de Plasma Pesado
        rec = int(self.recuo_arma) * d
        arma_y = rect.y + 27 + int(respirar)
        arma_x = (cx - 3 - rec) if d == 1 else (cx - 33 - rec)
        pygame.draw.rect(tela, (28, 34, 46), (arma_x, arma_y, 36, 9), border_radius=3)
        pygame.draw.rect(tela, (145, 160, 185), (arma_x + (4 if d == 1 else 2), arma_y + 1, 28, 4), border_radius=2)
        celula_x = arma_x + (14 if d == 1 else 10)
        pygame.draw.rect(tela, (0, 235, 255), (celula_x, arma_y + 3, 12, 3), border_radius=2)

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
            self._desenhar_guerreira(tela, rect)
        else:
            if self.avancando:
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