import math
import pygame
import config
from entidades.inimigo import Inimigo


class GuerreiroCorrompido(Inimigo):
    """Soldado possuído pelas sombras: patrulha devagar, 3 golpes para cair."""

    def __init__(self, x_centro, y_base):
        super().__init__(x_centro, y_base, largura=38, altura=52,
                         vida=3, dano=1, velocidade=90, cor=(110, 60, 150))


class OndaSombria:
    """Onda rasteira de gordura tóxica e lodo derretido lançada pela Abominação."""

    def __init__(self, x, y_base, direcao):
        self.direcao = direcao
        self.rect = pygame.Rect(round(x) - 16, round(y_base) - 34, 32, 34)
        self.pos_x = float(self.rect.x)
        self.vel_x = 345.0 * direcao
        self.distancia = 0.0
        self.alcance_max = 490.0
        self.ativo = True
        self.anim_t = 0.0

    def atualizar(self, dt, plataformas):
        self.anim_t += dt
        passo = self.vel_x * dt
        self.pos_x += passo
        self.distancia += abs(passo)
        self.rect.x = round(self.pos_x)

        if self.distancia >= self.alcance_max:
            self.ativo = False
            return

        for p in plataformas:
            if self.rect.colliderect(p.rect):
                self.ativo = False
                return

        pe_x = self.rect.right + 4 if self.direcao == 1 else self.rect.left - 4
        pe_y = self.rect.bottom + 6
        if not any(p.rect.collidepoint(pe_x, pe_y) for p in plataformas):
            self.ativo = False

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -25 or r.left > config.LARGURA + 25:
            return
        d = self.direcao
        onda_y = int(math.sin(self.anim_t * 18) * 3)
        topo_x = r.right if d == 1 else r.left
        base_tras_x = r.left if d == 1 else r.right

        # Massa principal de gordura e lodo podre
        pygame.draw.polygon(tela, (58, 86, 36), [
            (base_tras_x, r.bottom),
            (base_tras_x + d * 8, r.y + 12 - onda_y),
            (r.centerx + d * 3, r.y + 3 + onda_y),
            (topo_x, r.bottom - 8),
            (topo_x - d * 5, r.bottom),
        ])
        # Crista oleosa amarelada
        pygame.draw.polygon(tela, (152, 186, 68), [
            (base_tras_x + d * 7, r.bottom - 4),
            (r.centerx + d * 2, r.y + 9 + onda_y),
            (topo_x - d * 4, r.bottom - 6),
        ], 2)
        # Bolhas tóxicas saltando
        pygame.draw.circle(tela, (176, 208, 82), (r.centerx - d * 4, r.y + 8 + onda_y), 4)
        pygame.draw.circle(tela, (115, 152, 48), (base_tras_x + d * 6, r.bottom - 10), 5)


class _IAZumbiPerseguidor(Inimigo):
    """Base de perseguição inteligente para zumbis: escala cipós, salta para cima e desce atrás do alvo."""

    def _inicializar_ia_zumbi(self, vel_patrulha, vel_perseguicao, vel_escalada, altura_salto_max):
        self.vel_patrulha = vel_patrulha
        self.vel_perseguicao = vel_perseguicao
        self.vel_escalada = vel_escalada
        self.altura_salto_max = altura_salto_max
        self.perseguindo = False
        self.escalando = False
        self.cipo_atual = None
        self.anim_t = 0.0
        self.recarga_bote = 0.0
        self.trava_direcao = 0.0
        self.tempo_contorno = 0.0
        self.dir_patrulha_alta = self.direcao

    def _tem_chao_frente(self, plataformas, direcao):
        pe_x = self.rect.right + 6 if direcao == 1 else self.rect.left - 6
        pe_y = self.rect.bottom + 6
        return any(p.rect.collidepoint(pe_x, pe_y) for p in plataformas)

    def _tem_chao_abaixo(self, plataformas, direcao, queda_max=420):
        """Verifica se existe chão seguro abaixo ao descer de uma plataforma elevada."""
        teste_x = self.rect.right + 14 if direcao == 1 else self.rect.left - 14
        for dy in range(12, queda_max, 18):
            if any(p.rect.collidepoint(teste_x, self.rect.bottom + dy) for p in plataformas):
                return True
        return False

    def _pode_pular_obstaculo(self, plataformas):
        destino_x = self.rect.centerx + self.direcao * 68
        pe_y = self.rect.bottom + 10
        return any(p.rect.collidepoint(destino_x, pe_y) for p in plataformas)

    def _encontrar_plataforma_superior(self, plataformas, alvo):
        """Busca a plataforma alcançável mais útil para subir na direção da guerreira."""
        melhor_x = None
        melhor_topo = None
        melhor_score = 1e9
        cx = self.rect.centerx
        base_y = self.rect.bottom

        for p in plataformas:
            subida = base_y - p.rect.top
            if subida < 24 or subida > self.altura_salto_max:
                continue

            # Ponto mais próximo do zumbi no topo dessa plataforma
            margem = min(22, p.rect.width // 3)
            px = max(p.rect.left + margem, min(p.rect.right - margem, cx))
            dist_zumbi = abs(px - cx)
            if dist_zumbi > 420:
                continue

            # Garante espaço livre acima da plataforma para não bater a cabeça no teto
            espaco_cabeca = pygame.Rect(px - 16, p.rect.top - 56, 32, 48)
            if any(q is not p and q.rect.colliderect(espaco_cabeca) for q in plataformas):
                continue

            dist_alvo = abs(px - alvo.rect.centerx) + abs(p.rect.top - alvo.rect.bottom) * 0.7
            score = dist_zumbi * 1.15 + dist_alvo * 0.85
            if score < melhor_score:
                melhor_score = score
                melhor_x = px
                melhor_topo = p.rect.top

        return melhor_x, melhor_topo

    def _encontrar_cipo_subida(self, cipos, alvo):
        """Busca um cipó de escalada que leve para cima na direção da guerreira."""
        melhor_cipo = None
        melhor_score = 1e9
        cx = self.rect.centerx
        base_y = self.rect.bottom

        for c in cipos:
            # Cipó precisa chegar mais alto que o zumbi e ter base alcançável
            if c.rect.top >= self.rect.top - 26:
                continue
            if c.rect.bottom < base_y - self.altura_salto_max:
                continue
            dist_zumbi = abs(c.rect.centerx - cx)
            if dist_zumbi > 560:
                continue

            dist_alvo = abs(c.rect.centerx - alvo.rect.centerx)
            score = dist_zumbi * 1.1 + dist_alvo * 0.75
            if score < melhor_score:
                melhor_score = score
                melhor_cipo = c

        return melhor_cipo

    def _saltar_para_altura(self, altura_subir, sentido_x):
        altura_efetiva = max(48.0, min(float(self.altura_salto_max + 20), float(altura_subir) + 52.0))
        vel_salto = math.sqrt(2.0 * config.GRAVIDADE * altura_efetiva)
        self.vel.y = -min(680.0, vel_salto)
        self.direcao = sentido_x
        self.vel.x = sentido_x * max(self.vel_perseguicao, 165)
        self.no_chao = False
        self.recarga_bote = 0.85

    def _atualizar_ia_zumbi(self, dt, plataformas, alvo=None, cipos=()):
        self.anim_t += dt
        self.tempo_dano = max(0.0, self.tempo_dano - dt)
        self.recarga_bote = max(0.0, self.recarga_bote - dt)
        self.trava_direcao = max(0.0, self.trava_direcao - dt)
        self.tempo_contorno = max(0.0, self.tempo_contorno - dt)

        if getattr(self, "tempo_nascendo", 0.0) > 0:
            self.tempo_nascendo = max(0.0, self.tempo_nascendo - dt)
            self.vel.x = 0
            if alvo is not None:
                self.direcao = 1 if alvo.rect.centerx >= self.rect.centerx else -1
            return

        # 1. Lógica de escalada ativa em cipó
        if self.escalando:
            cipo_tocado = None
            for c in cipos:
                if self.rect.colliderect(c.rect.inflate(10, 8)):
                    cipo_tocado = c
                    break

            quer_subir = (
                alvo is not None
                and cipo_tocado is not None
                and alvo.rect.bottom < self.rect.bottom - 10
                and self.rect.bottom > cipo_tocado.rect.top + 14
            )

            if quer_subir:
                self.cipo_atual = cipo_tocado
                self.perseguindo = True
                self.direcao = 1 if alvo.rect.centerx >= self.rect.centerx else -1
                erro_x = cipo_tocado.rect.centerx - self.rect.centerx
                self.vel.x = max(-90.0, min(90.0, erro_x * 5.0))
                self.vel.y = -self.vel_escalada
                self.pos.x += self.vel.x * dt
                self.rect.x = round(self.pos.x)
                self.pos.y += self.vel.y * dt
                self.rect.y = round(self.pos.y)
                return
            else:
                # Chegou no topo do cipó ou na altura da guerreira: salta para a plataforma ao lado
                self.escalando = False
                self.cipo_atual = None
                if alvo is not None:
                    self.direcao = 1 if alvo.rect.centerx >= self.rect.centerx else -1
                self.vel.y = -270.0
                self.vel.x = self.direcao * self.vel_perseguicao
                self.trava_direcao = 0.45

        # 2. Definição de objetivo de perseguição
        self.perseguindo = False
        alvo_acima = False
        alvo_abaixo = False
        destino_x = None
        plat_topo_y = None
        cipo_alvo = None

        if alvo is not None and self.recuo <= 0:
            dx = alvo.rect.centerx - self.rect.centerx
            dy_signed = alvo.rect.centery - self.rect.centery
            if abs(dx) < 920 and abs(dy_signed) < 540:
                self.perseguindo = True
                alvo_acima = alvo.rect.bottom < self.rect.top - 20
                alvo_abaixo = alvo.rect.top > self.rect.bottom + 24

                if alvo_acima:
                    cipo_alvo = self._encontrar_cipo_subida(cipos, alvo)
                    plat_x, plat_topo_y = self._encontrar_plataforma_superior(plataformas, alvo)

                    # Escolhe entre o cipó e a plataforma saltável mais próximos
                    dist_cipo = abs(cipo_alvo.rect.centerx - self.rect.centerx) if cipo_alvo else 1e9
                    dist_plat = abs(plat_x - self.rect.centerx) if plat_x is not None else 1e9

                    if cipo_alvo is not None and dist_cipo <= dist_plat + 70:
                        destino_x = cipo_alvo.rect.centerx
                    elif plat_x is not None:
                        destino_x = plat_x
                    else:
                        # Plataforma inalcançável diretamente: faz varredura larga sem tremer no lugar
                        if self.trava_direcao <= 0:
                            self.direcao = self.dir_patrulha_alta
                            self.trava_direcao = 0.55
                else:
                    destino_x = alvo.rect.centerx

                if destino_x is not None and self.tempo_contorno <= 0:
                    diff_x = destino_x - self.rect.centerx
                    zona_morta = 10 if (alvo_acima and cipo_alvo is not None) else 22
                    if abs(diff_x) > zona_morta and self.trava_direcao <= 0:
                        nova_dir = 1 if diff_x > 0 else -1
                        if nova_dir != self.direcao:
                            self.direcao = nova_dir
                            self.trava_direcao = 0.22

                # Agarra no cipó se encostar nele enquanto sobe
                if alvo_acima:
                    for c in cipos:
                        if self.rect.colliderect(c.rect.inflate(10, 6)) and c.rect.top < self.rect.top - 22:
                            self.escalando = True
                            self.cipo_atual = c
                            self.vel.x = 0
                            self.vel.y = -self.vel_escalada
                            return

                # Salta para a plataforma superior quando estiver na distância ideal de impulso
                if (
                    alvo_acima
                    and self.no_chao
                    and self.recarga_bote <= 0
                    and plat_topo_y is not None
                    and destino_x is not None
                ):
                    dist_borda = abs(destino_x - self.rect.centerx)
                    altura_subir = self.rect.bottom - plat_topo_y
                    if 18 <= dist_borda <= 135 and 24 <= altura_subir <= self.altura_salto_max:
                        sentido_salto = 1 if destino_x >= self.rect.centerx else -1
                        self._saltar_para_altura(altura_subir, sentido_salto)

                # Bote horizontal normal no mesmo nível
                if (
                    not alvo_acima
                    and not alvo_abaixo
                    and self.no_chao
                    and self.recarga_bote <= 0
                    and 80 < abs(dx) < 165
                    and abs(dy_signed) < 55
                ):
                    if self._pode_pular_obstaculo(plataformas):
                        self.vel.y = -360
                        self.no_chao = False
                        self.recarga_bote = 2.1

        vel_atual = self.vel_perseguicao if self.perseguindo else self.vel_patrulha

        if self.recuo > 0:
            self.recuo -= dt
        else:
            self.vel.x = self.direcao * vel_atual

        # Controle de bordas: nunca cai em buraco sem fundo, mas desce plataformas se a guerreira estiver abaixo
        if self.no_chao and abs(self.vel.x) > 0:
            sentido_mov = 1 if self.vel.x > 0 else -1
            if not self._tem_chao_frente(plataformas, sentido_mov):
                pode_descer = alvo_abaixo and self._tem_chao_abaixo(plataformas, sentido_mov)
                if not pode_descer:
                    self.vel.x = 0
                    if self.recuo <= 0:
                        self.direcao *= -1
                        self.dir_patrulha_alta = self.direcao
                        self.trava_direcao = 0.45

        self.vel.y = min(self.vel.y + config.GRAVIDADE * dt, config.VELOCIDADE_QUEDA_MAX)

        # Movimento horizontal e colisão com degraus/paredes
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)
        bateu = False
        parede_tocada = None
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                # Assistência de subida de borda quando o zumbi quase alcança o topo no salto
                if not self.no_chao and 0 < (self.rect.bottom - p.rect.top) <= 22:
                    self.rect.bottom = p.rect.top
                    self.pos.y = self.rect.y
                    self.vel.y = 0
                    self.no_chao = True
                    continue

                if self.vel.x > 0:
                    self.rect.right = p.rect.left
                elif self.vel.x < 0:
                    self.rect.left = p.rect.right
                self.pos.x = self.rect.x
                bateu = True
                parede_tocada = p

        if bateu and self.recuo <= 0:
            # Se houver um cipó encostado na parede, escala imediatamente
            cipo_parede = next(
                (c for c in cipos if self.rect.colliderect(c.rect.inflate(18, 8)) and c.rect.top < self.rect.top - 20),
                None,
            )
            if cipo_parede is not None:
                self.escalando = True
                self.cipo_atual = cipo_parede
                self.vel.x = 0
                self.vel.y = -self.vel_escalada
                return

            # Se a parede bloqueando for escalável por salto, pula nela!
            if (
                self.perseguindo
                and self.no_chao
                and self.recarga_bote <= 0
                and parede_tocada is not None
            ):
                altura_parede = self.rect.bottom - parede_tocada.rect.top
                if 20 <= altura_parede <= self.altura_salto_max:
                    self._saltar_para_altura(altura_parede, self.direcao)
                elif self._pode_pular_obstaculo(plataformas):
                    self.vel.y = -480
                    self.no_chao = False
                    self.recarga_bote = 1.0
                else:
                    self.direcao *= -1
                    self.dir_patrulha_alta = self.direcao
                    self.tempo_contorno = 0.95
            else:
                self.direcao *= -1
                self.dir_patrulha_alta = self.direcao
                self.tempo_contorno = 0.75

        # Movimento vertical
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


class ZumbiTsunami(_IAZumbiPerseguidor):
    """Zumbi caçador rápido e ágil: escala cipós e salta para terras mais altas atrás da guerreira."""

    def __init__(self, x_centro, y_base, nascendo=False):
        super().__init__(x_centro, y_base, largura=40, altura=52,
                         vida=4, dano=1, velocidade=205, cor=(72, 138, 56))
        self._inicializar_ia_zumbi(
            vel_patrulha=95,
            vel_perseguicao=218,
            vel_escalada=185,
            altura_salto_max=190,
        )
        self.tempo_nascendo = 0.65 if nascendo else 0.0

    def atualizar(self, dt, plataformas, alvo=None, cipos=()):
        self._atualizar_ia_zumbi(dt, plataformas, alvo, cipos)

    def _posicoes_olhos(self, cabeca):
        if self.direcao == 1:
            return (cabeca.right - 16, cabeca.y + 11), (cabeca.right - 7, cabeca.y + 12)
        return (cabeca.left + 7, cabeca.y + 12), (cabeca.left + 16, cabeca.y + 11)

    def desenhar_olhos_brilhantes(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -20 or r.left > config.LARGURA + 20:
            return
        afundado = int((self.tempo_nascendo / 0.65) * 32) if self.tempo_nascendo > 0 else 0
        balanco = int(math.sin(self.anim_t * (16 if self.perseguindo else 7)) * 2)
        cabeca = pygame.Rect(r.x + 2, r.y + 1 + balanco + afundado, r.width - 4, 28)
        olho1, olho2 = self._posicoes_olhos(cabeca)
        for ox, oy in (olho1, olho2):
            pygame.draw.circle(tela, (255, 60, 30), (ox, oy), 3)
            pygame.draw.circle(tela, (255, 225, 90), (ox, oy), 1)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -25 or r.left > config.LARGURA + 25:
            return

        afundado = int((self.tempo_nascendo / 0.65) * 32) if self.tempo_nascendo > 0 else 0
        r_desenho = r.move(0, afundado)

        d = self.direcao
        atingido = self.tempo_dano > 0
        cor_pele = config.BRANCO if atingido else (72, 138, 56)
        cor_podre = config.BRANCO if atingido else (46, 94, 38)
        cor_mancha = config.BRANCO if atingido else (62, 44, 74)
        balanco = int(math.sin(self.anim_t * (16 if self.perseguindo else 7)) * 2)
        passo = int(math.sin(self.anim_t * 14) * 3)

        if afundado == 0:
            desloc_perna = passo if self.escalando else 0
            pygame.draw.rect(tela, (34, 26, 42), (r_desenho.x + 9 + passo, r_desenho.bottom - 12 + desloc_perna, 8, 12))
            pygame.draw.rect(tela, (28, 22, 34), (r_desenho.right - 17 - passo, r_desenho.bottom - 12 - desloc_perna, 8, 12))

        corpo = pygame.Rect(r_desenho.x + 6, r_desenho.y + 25 + balanco, r_desenho.width - 12, 17)
        pygame.draw.rect(tela, (44, 30, 52), corpo, border_radius=4)
        ferida_x = corpo.right - 11 if d == 1 else corpo.left + 3
        pygame.draw.rect(tela, (125, 22, 28), (ferida_x, corpo.y + 4, 8, 7), border_radius=2)
        pygame.draw.line(tela, (205, 195, 175), (ferida_x + 1, corpo.y + 6), (ferida_x + 7, corpo.y + 6), 1)
        pygame.draw.line(tela, (205, 195, 175), (ferida_x + 1, corpo.y + 9), (ferida_x + 7, corpo.y + 9), 1)

        braco_y = r_desenho.y + 27 + balanco
        if self.escalando:
            # Braços agarrando e puxando o cipó para cima
            mao1_y = r_desenho.y + 6 - passo * 2
            mao2_y = r_desenho.y + 16 + passo * 2
            pygame.draw.line(tela, cor_podre, (r_desenho.centerx - 4, braco_y), (r_desenho.centerx - 6, mao1_y), 4)
            pygame.draw.line(tela, cor_pele, (r_desenho.centerx + 4, braco_y), (r_desenho.centerx + 6, mao2_y), 4)
        elif d == 1:
            pygame.draw.rect(tela, cor_podre, (r_desenho.right - 9, braco_y + 3, 16, 5), border_radius=2)
            pygame.draw.rect(tela, cor_pele, (r_desenho.right - 7, braco_y - 1, 18, 6), border_radius=2)
            ponta_x = r_desenho.right + 11
            for gy in (braco_y - 1, braco_y + 2, braco_y + 5):
                pygame.draw.line(tela, (215, 205, 185), (ponta_x, gy), (ponta_x + 5, gy + 1), 2)
        else:
            pygame.draw.rect(tela, cor_podre, (r_desenho.left - 7, braco_y + 3, 16, 5), border_radius=2)
            pygame.draw.rect(tela, cor_pele, (r_desenho.left - 11, braco_y - 1, 18, 6), border_radius=2)
            ponta_x = r_desenho.left - 11
            for gy in (braco_y - 1, braco_y + 2, braco_y + 5):
                pygame.draw.line(tela, (215, 205, 185), (ponta_x, gy), (ponta_x - 5, gy + 1), 2)

        cabeca = pygame.Rect(r_desenho.x + 2, r_desenho.y + 1 + balanco, r_desenho.width - 4, 28)
        pygame.draw.rect(tela, cor_pele, cabeca, border_radius=8)
        pygame.draw.rect(tela, (26, 54, 24), cabeca, 2, border_radius=8)

        cranio_x = cabeca.x + 6 if d == 1 else cabeca.right - 16
        pygame.draw.ellipse(tela, (185, 182, 160), (cranio_x, cabeca.y + 1, 10, 5))
        pygame.draw.circle(tela, cor_mancha, (cabeca.centerx - d * 8, cabeca.y + 16), 4)

        cic_x = cabeca.centerx - d * 5
        pygame.draw.line(tela, (35, 18, 22), (cic_x - 4, cabeca.y + 6), (cic_x + 4, cabeca.y + 8), 2)
        pygame.draw.line(tela, (20, 15, 18), (cic_x - 2, cabeca.y + 4), (cic_x - 2, cabeca.y + 10), 1)
        pygame.draw.line(tela, (20, 15, 18), (cic_x + 2, cabeca.y + 5), (cic_x + 2, cabeca.y + 11), 1)

        for fx in (cabeca.x + 7, cabeca.centerx, cabeca.right - 8):
            pygame.draw.line(tela, (24, 28, 22), (fx, cabeca.y + 1), (fx - d * 2, cabeca.y - 6), 2)

        olho1, olho2 = self._posicoes_olhos(cabeca)
        pygame.draw.circle(tela, (26, 18, 32), olho1, 6)
        pygame.draw.circle(tela, (255, 50, 25), olho1, 4)
        pygame.draw.circle(tela, (255, 220, 80), (olho1[0] + d, olho1[1]), 2)

        pygame.draw.circle(tela, (26, 18, 32), olho2, 5)
        pygame.draw.circle(tela, (255, 50, 25), olho2, 3)
        pygame.draw.circle(tela, (255, 220, 80), (olho2[0] + d, olho2[1]), 1)

        boca_x = cabeca.right - 19 if d == 1 else cabeca.left + 3
        boca = pygame.Rect(boca_x, cabeca.y + 17, 16, 10)
        pygame.draw.rect(tela, (75, 10, 18), boca, border_radius=3)
        pygame.draw.rect(tela, (25, 5, 10), boca, 1, border_radius=3)
        pygame.draw.polygon(tela, (225, 215, 185), [(boca.x + 2, boca.y), (boca.x + 5, boca.y), (boca.x + 3, boca.y + 5)])
        pygame.draw.polygon(tela, (225, 215, 185), [(boca.right - 5, boca.y), (boca.right - 2, boca.y), (boca.right - 3, boca.y + 5)])
        pygame.draw.polygon(tela, (225, 215, 185), [(boca.x + 6, boca.bottom), (boca.x + 9, boca.bottom), (boca.x + 7, boca.bottom - 4)])
        canto_x = boca.left + 2 if d == 1 else boca.right - 3
        pygame.draw.line(tela, (155, 18, 25), (canto_x, boca.bottom - 1), (canto_x, boca.bottom + 4), 2)

        if afundado > 0:
            pygame.draw.ellipse(tela, (36, 26, 20), (r.x - 4, r.bottom - 10, r.width + 8, 14))

        if self.vida < self.vida_max:
            pygame.draw.rect(tela, (60, 20, 20), (r.x, r.y - 12, r.width, 5))
            largura = int(r.width * max(self.vida, 0) / self.vida_max)
            pygame.draw.rect(tela, config.VERMELHO, (r.x, r.y - 12, largura, 5))


class ZumbiAnciao(_IAZumbiPerseguidor):
    """Colosso morto-vivo coberto de musgo e correntes (W): escala cipós e salta atrás do alvo."""

    def __init__(self, x_centro, y_base):
        super().__init__(x_centro, y_base, largura=48, altura=62,
                         vida=8, dano=1, velocidade=92, cor=(52, 86, 56))
        self._inicializar_ia_zumbi(
            vel_patrulha=76,
            vel_perseguicao=116,
            vel_escalada=125,
            altura_salto_max=165,
        )

    def receber_dano(self, dano, origem_x):
        super().receber_dano(dano, origem_x)
        self.vel.x *= 0.35
        self.vel.y = -95

    def atualizar(self, dt, plataformas, alvo=None, cipos=()):
        self._atualizar_ia_zumbi(dt, plataformas, alvo, cipos)

    def desenhar_olhos_brilhantes(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -20 or r.left > config.LARGURA + 20:
            return
        ox = r.right - 14 if self.direcao == 1 else r.left + 14
        oy = r.y + 15
        pygame.draw.circle(tela, (180, 255, 70), (ox, oy), 4)
        pygame.draw.circle(tela, config.BRANCO, (ox, oy), 2)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -30 or r.left > config.LARGURA + 30:
            return

        d = self.direcao
        atingido = self.tempo_dano > 0
        cor_pele = config.BRANCO if atingido else (56, 88, 58)
        cor_musgo = config.BRANCO if atingido else (34, 62, 34)
        passo = int(math.sin(self.anim_t * 8) * 3)

        pygame.draw.rect(tela, (30, 26, 36), (r.x + 8 + passo, r.bottom - 16, 12, 16))
        pygame.draw.rect(tela, (26, 22, 32), (r.right - 20 - passo, r.bottom - 16, 12, 16))

        corpo = pygame.Rect(r.x + 4, r.y + 18, r.width - 8, 30)
        pygame.draw.rect(tela, cor_pele, corpo, border_radius=8)
        pygame.draw.rect(tela, (26, 42, 28), corpo, 2, border_radius=8)
        pygame.draw.ellipse(tela, cor_musgo, (r.x + 4, r.y + 14, r.width - 8, 12))

        pygame.draw.line(tela, (95, 78, 68), (r.x + 8, r.y + 22), (r.right - 8, r.y + 42), 3)
        pygame.draw.line(tela, (95, 78, 68), (r.right - 8, r.y + 22), (r.x + 8, r.y + 42), 3)

        cab_x = r.right - 26 if d == 1 else r.x + 4
        cabeca = pygame.Rect(cab_x, r.y + 6, 22, 20)
        pygame.draw.rect(tela, cor_pele, cabeca, border_radius=6)
        olho_x = cabeca.right - 7 if d == 1 else cabeca.left + 7
        pygame.draw.circle(tela, (195, 255, 80), (olho_x, cabeca.y + 9), 3)

        if self.escalando:
            pygame.draw.line(tela, cor_pele, (r.centerx - 6, r.y + 24), (r.centerx - 8, r.y + 4 - passo), 6)
            pygame.draw.line(tela, cor_pele, (r.centerx + 6, r.y + 24), (r.centerx + 8, r.y + 10 + passo), 6)
        else:
            braco_x = r.right - 10 if d == 1 else r.left - 8
            pygame.draw.rect(tela, cor_pele, (braco_x, r.y + 26, 18, 9), border_radius=3)

        if self.vida < self.vida_max:
            pygame.draw.rect(tela, (60, 20, 20), (r.x, r.y - 12, r.width, 6))
            largura = int(r.width * max(self.vida, 0) / self.vida_max)
            pygame.draw.rect(tela, config.VERMELHO, (r.x, r.y - 12, largura, 6))


class GuardiaoFloresta(Inimigo):
    """Chefe final (C): Abominação Zumbi gigante, grotesca, toda gordurenta e derretida."""

    eh_chefe = True

    def __init__(self, x_centro, y_base):
        super().__init__(x_centro, y_base, largura=106, altura=128,
                         vida=36, dano=1, velocidade=98, cor=(68, 98, 46))
        self.nome = "ABOMINAÇÃO ZUMBI DERRETIDA"
        self.anim_t = 0.0
        self.estado = "patrulha"
        self.timer_estado = 0.0
        self.recarga_habilidade = 2.1
        self.ondas_pendentes = []
        self.tremor_pendente = False
        self.trava_direcao = 0.0

    def receber_dano(self, dano, origem_x):
        super().receber_dano(dano, origem_x)
        self.vel.x *= 0.12
        self.vel.y = 0
        self.recuo = 0.03

    def _tem_chao_frente(self, plataformas, direcao):
        pe_x = self.rect.right + 10 if direcao == 1 else self.rect.left - 10
        pe_y = self.rect.bottom + 8
        return any(p.rect.collidepoint(pe_x, pe_y) for p in plataformas)

    def atualizar(self, dt, plataformas, alvo=None, cipos=()):
        self.anim_t += dt
        self.tempo_dano = max(0.0, self.tempo_dano - dt)
        self.recarga_habilidade = max(0.0, self.recarga_habilidade - dt)
        self.trava_direcao = max(0.0, self.trava_direcao - dt)

        distancia_x = 9999
        distancia_y = 9999
        dx = 0
        if alvo is not None:
            dx = alvo.rect.centerx - self.rect.centerx
            distancia_x = abs(dx)
            distancia_y = abs(alvo.rect.centery - self.rect.centery)

        if self.estado == "preparando":
            self.vel.x = 0
            self.timer_estado -= dt
            if self.timer_estado <= 0:
                self.estado = "investindo"
                self.timer_estado = 0.90
                self.tremor_pendente = True
                boca_onda = self.rect.right + 10 if self.direcao == 1 else self.rect.left - 10
                self.ondas_pendentes.append(OndaSombria(boca_onda, self.rect.bottom, self.direcao))

        elif self.estado == "investindo":
            self.vel.x = self.direcao * 285
            self.timer_estado -= dt
            if self.timer_estado <= 0:
                self.estado = "perseguindo"
                self.recarga_habilidade = 2.4

        else:
            if alvo is not None and distancia_x < 760 and distancia_y < 340:
                self.estado = "perseguindo"
                if abs(dx) > 24 and self.trava_direcao <= 0:
                    nova_dir = 1 if dx > 0 else -1
                    if nova_dir != self.direcao:
                        self.direcao = nova_dir
                        self.trava_direcao = 0.30

                if self.no_chao and self.recarga_habilidade <= 0 and distancia_x < 500:
                    self.estado = "preparando"
                    self.timer_estado = 0.55
                    self.vel.x = 0
                else:
                    self.vel.x = self.direcao * 116
            else:
                self.estado = "patrulha"
                self.vel.x = self.direcao * 68

        if self.no_chao and abs(self.vel.x) > 0:
            sentido_mov = 1 if self.vel.x > 0 else -1
            if not self._tem_chao_frente(plataformas, sentido_mov):
                self.vel.x = 0
                if self.estado == "investindo":
                    self.estado = "perseguindo"
                    self.recarga_habilidade = 2.0
                elif self.estado == "patrulha":
                    self.direcao *= -1

        self.vel.y = min(self.vel.y + config.GRAVIDADE * dt, config.VELOCIDADE_QUEDA_MAX)

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

        if bateu:
            if self.estado == "investindo":
                self.estado = "perseguindo"
                self.recarga_habilidade = 2.1
                self.tremor_pendente = True
            elif self.estado == "patrulha":
                self.direcao *= -1

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

    def _posicoes_olhos(self, r, agachar=0):
        d = self.direcao
        cx = r.centerx + d * 20
        cy = r.y + 24 + agachar
        # Olhos deformados e assimétricos: um esbugalhado e outro derretendo para baixo
        return (cx - d * 9, cy - 2, 5), (cx + d * 8, cy + 5, 3)

    def desenhar_olhos_brilhantes(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -50 or r.left > config.LARGURA + 50:
            return
        agachar = 8 if self.estado == "preparando" else 0
        cor_brilho = (255, 225, 80) if self.estado == "preparando" else (255, 45, 28)
        for ox, oy, raio in self._posicoes_olhos(r, agachar):
            pygame.draw.circle(tela, cor_brilho, (ox, oy), raio)
            pygame.draw.circle(tela, config.BRANCO, (ox, oy), 1)
        # Núcleo de gordura ácida brilhando na barriga rasgada
        bx = r.centerx + self.direcao * 10
        by = r.y + 68 + agachar // 2
        pygame.draw.circle(tela, (175, 215, 65), (bx, by), 6)

    def desenhar(self, tela, camera):
        r = camera.aplicar(self.rect)
        if r.right < -60 or r.left > config.LARGURA + 60:
            return

        d = self.direcao
        atingido = self.tempo_dano > 0
        t = self.anim_t

        cor_pele = config.BRANCO if atingido else (74, 106, 48)
        cor_pele_escura = config.BRANCO if atingido else (46, 70, 32)
        cor_gordura = config.BRANCO if atingido else (126, 158, 58)
        cor_brilho_oleo = config.BRANCO if atingido else (182, 212, 98)
        cor_gosma = config.BRANCO if atingido else (142, 182, 54)

        passo = int(math.sin(t * (14 if self.estado == "investindo" else 6)) * 5)
        agachar = 8 if self.estado == "preparando" else 0
        onda_derreter = int(math.sin(t * 4.5) * 4)

        # 1. Poças gordurentas e rastro viscoso no chão
        pygame.draw.ellipse(tela, (42, 62, 26), (r.x - 18, r.bottom - 7, r.width + 36, 12))
        pygame.draw.ellipse(tela, (112, 146, 48), (r.x - 6, r.bottom - 5, r.width + 12, 6))

        # 2. Pernas grossas, inchadas e derretendo sobre os pés
        perna_esq = pygame.Rect(r.x + 14 + passo, r.bottom - 30, 26, 30)
        perna_dir = pygame.Rect(r.right - 40 - passo, r.bottom - 30, 26, 30)
        for pr in (perna_esq, perna_dir):
            pygame.draw.rect(tela, cor_pele_escura, pr, border_radius=8)
            # Dobra de gordura derretida escorrendo pela perna
            pygame.draw.ellipse(tela, cor_pele, (pr.x - 3, pr.y + 4, pr.width + 6, 14))
            pygame.draw.ellipse(tela, cor_gordura, (pr.x - 4, pr.bottom - 8, pr.width + 8, 8))

        # 3. Corpo colossal, obeso, corcunda e derretido
        # Corcunda inchada nas costas
        corcunda_x = r.x + 6 if d == 1 else r.x + 26
        pygame.draw.ellipse(tela, cor_pele_escura, (corcunda_x, r.y + 8 + agachar, 66, 56))
        pygame.draw.arc(tela, cor_brilho_oleo, (corcunda_x + 8, r.y + 12 + agachar, 48, 34), 0.4, 2.5, 3)

        # Tronco principal flácido
        torso = pygame.Rect(r.x + 8, r.y + 24 + agachar, r.width - 16, 74 - agachar)
        pygame.draw.rect(tela, cor_pele, torso, border_radius=24)
        pygame.draw.rect(tela, (28, 44, 20), torso, 3, border_radius=24)

        # Barriga gigantesca caída por cima da cintura
        barriga = pygame.Rect(r.x + 2 + d * 6, r.y + 54 + agachar, r.width - 10, 48 - agachar // 2)
        pygame.draw.ellipse(tela, cor_pele, barriga)
        pygame.draw.ellipse(tela, cor_pele_escura, barriga, 2)
        # Brilho gordurento na pança
        pygame.draw.arc(tela, cor_brilho_oleo, (barriga.x + 12, barriga.y + 6, barriga.width - 24, 24), 0.3, 2.7, 3)

        # Rasgo necrótico na barriga mostrando costelas e pus
        rasgo_x = r.centerx + d * 4
        rasgo_y = r.y + 68 + agachar // 2
        pygame.draw.ellipse(tela, (96, 16, 24), (rasgo_x - 16, rasgo_y - 12, 32, 24))
        for cost_y in (rasgo_y - 6, rasgo_y, rasgo_y + 6):
            pygame.draw.line(tela, (206, 198, 162), (rasgo_x - 12, cost_y), (rasgo_x - 2, cost_y + 2), 3)
            pygame.draw.line(tela, (206, 198, 162), (rasgo_x + 12, cost_y), (rasgo_x + 2, cost_y + 2), 3)
        pygame.draw.circle(tela, cor_gosma, (rasgo_x, rasgo_y + 3), 5)

        # Pústulas e bolhas de gordura pelo corpo
        for px, py, pr in (
            (r.x + 22, r.y + 42 + agachar, 6),
            (r.right - 24, r.y + 46 + agachar, 5),
            (r.centerx - d * 18, r.y + 74 + agachar, 7),
        ):
            pygame.draw.circle(tela, cor_gordura, (px, py), pr)
            pygame.draw.circle(tela, cor_brilho_oleo, (px - 1, py - 1), max(2, pr // 2))

        # 4. Fios de carne derretida e gordura pingando do corpo
        fios_derretidos = [
            (barriga.x + 14, barriga.bottom - 4, 16 + onda_derreter),
            (barriga.centerx, barriga.bottom - 2, 22 - onda_derreter),
            (barriga.right - 16, barriga.bottom - 5, 14 + onda_derreter),
            (r.centerx - d * 28, r.y + 62 + agachar, 18 + onda_derreter),
        ]
        for fx, fy, comp in fios_derretidos:
            pygame.draw.polygon(tela, cor_gosma, [
                (fx - 4, fy),
                (fx + 4, fy),
                (fx + 1, fy + comp),
                (fx - 1, fy + comp),
            ])
            gota_y = fy + comp + int((t * 45 + fx) % 16)
            if gota_y < r.bottom:
                pygame.draw.circle(tela, cor_brilho_oleo, (fx, gota_y), 3)

        # 5. Cabeça medonha, deformada e derretida fundida ao tronco
        cab_x = r.centerx + d * 14
        cab_y = r.y + 24 + agachar
        # Crânio assimétrico com lado esquerdo/direito escorrendo
        pygame.draw.ellipse(tela, cor_pele, (cab_x - 24, cab_y - 18, 46, 36))
        pygame.draw.ellipse(tela, cor_pele_escura, (cab_x - 24, cab_y - 18, 46, 36), 2)
        # Aba de pele derretida pendurada na bochecha
        bochecha_x = cab_x + d * 12
        pygame.draw.polygon(tela, cor_pele, [
            (bochecha_x - 6, cab_y + 4),
            (bochecha_x + 8, cab_y + 2),
            (bochecha_x + 4, cab_y + 24 + onda_derreter),
            (bochecha_x - 4, cab_y + 20),
        ])
        # Brilho oleoso no topo da careca podre
        pygame.draw.arc(tela, cor_brilho_oleo, (cab_x - 16, cab_y - 15, 30, 14), 0.2, 2.8, 3)

        # Olhos grotescos assimétricos
        for ox, oy, raio in self._posicoes_olhos(r, agachar):
            pygame.draw.circle(tela, (28, 12, 16), (ox, oy), raio + 3)
            pygame.draw.circle(tela, (255, 48, 28), (ox, oy), raio)
            pygame.draw.circle(tela, (255, 225, 95), (ox + d, oy), max(1, raio // 2))

        # Bocão rasgado com mandíbula caída, dentes podres e baba gordurenta
        boca_x = cab_x - 14 if d == 1 else cab_x - 20
        boca = pygame.Rect(boca_x, cab_y + 8, 34, 17)
        pygame.draw.rect(tela, (64, 10, 18), boca, border_radius=6)
        pygame.draw.rect(tela, (24, 6, 10), boca, 2, border_radius=6)
        for dx_dente in range(boca.x + 4, boca.right - 4, 7):
            pygame.draw.polygon(tela, (218, 206, 158), [
                (dx_dente, boca.y),
                (dx_dente + 4, boca.y),
                (dx_dente + 2, boca.y + 6),
            ])
            pygame.draw.polygon(tela, (218, 206, 158), [
                (dx_dente + 1, boca.bottom),
                (dx_dente + 5, boca.bottom),
                (dx_dente + 3, boca.bottom - 5),
            ])
        # Fios de baba viscosa esticados na boca e pingando do queixo
        pygame.draw.line(tela, cor_brilho_oleo, (boca.centerx - 4, boca.y + 2), (boca.centerx - 2, boca.bottom - 2), 2)
        pygame.draw.line(tela, cor_gosma, (boca.centerx + 5, boca.bottom), (boca.centerx + 5, boca.bottom + 14 + onda_derreter), 3)

        # 6. Braço gigantesco gordurento com garras e fio de lodo
        braco_x = r.right - 18 if d == 1 else r.left - 22
        braco_y = r.y + 44 + agachar
        pygame.draw.rect(tela, cor_pele_escura, (braco_x, braco_y, 40, 22), border_radius=10)
        pygame.draw.rect(tela, cor_pele, (braco_x + 2, braco_y + 2, 36, 16), border_radius=8)
        pygame.draw.line(tela, cor_brilho_oleo, (braco_x + 6, braco_y + 4), (braco_x + 30, braco_y + 4), 2)

        ponta_garra = braco_x + 40 if d == 1 else braco_x
        for gy in (braco_y + 3, braco_y + 10, braco_y + 17):
            pygame.draw.line(tela, (205, 194, 156), (ponta_garra, gy), (ponta_garra + d * 11, gy + 4), 3)
        # Gota de gordura pendurada na garra
        pygame.draw.line(tela, cor_gosma, (ponta_garra + d * 4, braco_y + 18), (ponta_garra + d * 4, braco_y + 32 + onda_derreter), 3)