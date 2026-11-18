import math
import random
import pygame
import config
from nucleo.cena import Cena
from nucleo.camera import Camera
from entidades.jogador import Jogador
from entidades.inimigos_comuns import GuerreiroCorrompido, Fantasma, MonstroPalido
from entidades.projetil import ProjetilPlasma, ParticulaPlasma
from entidades.reliquia import Reliquia
from entidades.barreira import Barreira
from entidades.saida import Saida
from sistemas.mapa import carregar_mapa, existe_fase
from sistemas.hud import Hud
from sistemas.sons import Sons

FUNDOS = {1: (25, 20, 30), 2: (10, 14, 24)}


class Fase(Cena):
    def __init__(self, jogo, numero=1):
        super().__init__(jogo)
        self.numero = numero
        self.fonte = pygame.font.Font(None, 28)
        self.fonte_msg = pygame.font.Font(None, 40)
        self.fonte_msg2 = pygame.font.Font(None, 28)
        self.fonte_combo = pygame.font.Font(None, 34)
        self.t = 0.0
        self.sons = Sons()

        dados = carregar_mapa(numero)
        self.largura, self.altura = dados.largura, dados.altura
        self.plataformas = dados.plataformas
        self.barreiras = [Barreira(*b) for b in dados.barreiras]
        self.escadas = dados.escadas
        self.solidos = self.plataformas + self.barreiras
        self.saida = Saida(*dados.saida) if dados.saida else None
        if self.saida and self.numero == 2:
            self.saida.bizarro = True

        x, y = dados.inicio
        self.jogador = Jogador(x - Jogador.LARGURA // 2, y - Jogador.ALTURA)
        if self.numero == 2:
            self.jogador.estilo = "guerreira"
            self.jogador.desbloquear("salto_duplo")
            self.jogador.desbloquear("avanco")

        for habilidade in jogo.habilidades:
            self.jogador.desbloquear(habilidade)

        self.chefe = None
        if self.numero == 2:
            self.inimigos = []
            for ix, iy in dados.inimigos:
                f = Fantasma(ix, iy - 28)
                f.alvo = self.jogador
                self.inimigos.append(f)
            if dados.chefe:
                self.chefe = MonstroPalido(*dados.chefe)
                self.chefe.alvo = self.jogador
                self.inimigos.append(self.chefe)
        else:
            self.inimigos = [GuerreiroCorrompido(ix, iy) for ix, iy in dados.inimigos]

        self.projeteis = []
        self.particulas = []
        self.orbes_inimigos = []
        self.curas = [pygame.Rect(cx - 12, cy - 12, 24, 24) for cx, cy in dados.curas]
        self.powerups = [pygame.Rect(px - 14, py - 14, 28, 28) for px, py in dados.powerups]
        self.tempo_tiro_triplo = 0.0

        # Hitstop, Relâmpagos visuais e Combo Aéreo
        self.hitstop = 0.0
        self.proximo_relampago = random.uniform(7.0, 12.0)
        self.flash_relampago = 0.0
        self.combo_dash = 0
        self.textos_flutuantes = []  # [x, y, texto, tempo, cor]

        # Corvos pousados nas lápides e cruzes do cemitério
        self.corvos = []
        if self.numero == 2:
            chao_y = self.altura - (2 * config.TAMANHO_TILE)
            for wx in range(120, self.largura - 100, 280):
                # Corvo na lápide
                self.corvos.append({
                    "x": float(wx + 15),
                    "y": float(chao_y - 44),
                    "vx": 0.0,
                    "vy": 0.0,
                    "voando": False,
                    "fase": random.uniform(0, math.tau),
                })
                # Corvo na cruz ao lado (em alguns pontos)
                if (wx // 280) % 2 == 0:
                    self.corvos.append({
                        "x": float(wx + 72),
                        "y": float(chao_y - 58),
                        "vx": 0.0,
                        "vy": 0.0,
                        "voando": False,
                        "fase": random.uniform(0, math.tau),
                    })

        self.reliquias = [Reliquia(t, rx, ry) for t, rx, ry in dados.reliquias
                          if t not in jogo.habilidades]

        self.esporos = [
            [random.uniform(0, self.largura), random.uniform(80, self.altura - 110),
             random.uniform(0.6, 2.0), random.uniform(0, math.tau)]
            for _ in range(45)
        ]

        self.camera = Camera(self.largura, self.altura)
        self.camera.centralizar(self.jogador.rect)
        self.hud = Hud()
        self.mensagem = None
        self.tempo_mensagem = 0.0
        self.dicas = set()

        if self.numero == 2:
            self.mensagem = (
                "Cemitério das Almas Pálidas",
                "Plasma (J/X) ou Dash Hitkill (K/SHIFT) para eliminar fantasmas e abrir o Portal Dimensional!"
            )
            self.tempo_mensagem = 4.5

    # ---------- eventos ----------
    def eventos(self, eventos):
        for e in eventos:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    from cenas.menu import Menu
                    self.jogo.trocar_cena(Menu(self.jogo))
                elif e.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    if e.key in (pygame.K_w, pygame.K_UP) and any(self.jogador.rect.colliderect(esc.rect) for esc in self.escadas):
                        continue
                    if self.jogador.pular() and self.numero == 2:
                        self.sons.tocar("pulo")
                elif e.key in (pygame.K_j, pygame.K_x):
                    disparou = self.jogador.atacar()
                    if disparou:
                        self.sons.tocar("plasma")
                        self._assustar_corvos(self.jogador.rect.centerx, raio=340)
                        boca_x = self.jogador.rect.centerx + self.jogador.direcao * 34
                        boca_y = self.jogador.rect.y + 31
                        self.projeteis.append(ProjetilPlasma(boca_x, boca_y, self.jogador.direcao, vy=0))
                        if self.tempo_tiro_triplo > 0:
                            self.projeteis.append(ProjetilPlasma(boca_x, boca_y, self.jogador.direcao, vy=-135))
                            self.projeteis.append(ProjetilPlasma(boca_x, boca_y, self.jogador.direcao, vy=135))
                        for _ in range(5):
                            self.particulas.append(ParticulaPlasma(boca_x, boca_y))
                elif e.key in (pygame.K_k, pygame.K_LSHIFT, pygame.K_RSHIFT):
                    if self.jogador.avancar() and self.numero == 2:
                        self.sons.tocar("dash")
                        self.camera.tremer(3, 0.08)

    def _assustar_corvos(self, origem_x, raio=190):
        for corvo in self.corvos:
            if not corvo["voando"] and abs(corvo["x"] - origem_x) < raio:
                corvo["voando"] = True
                lado = 1 if corvo["x"] >= origem_x else -1
                corvo["vx"] = lado * random.uniform(95, 165)
                corvo["vy"] = -random.uniform(130, 210)

    # ---------- lógica ----------
    def atualizar(self, dt):
        self.t += dt

        # Hitstop (micro-congelamento dramático no impacto)
        if self.hitstop > 0:
            self.hitstop = max(0.0, self.hitstop - dt)
            self.camera.seguir(self.jogador.rect, dt)
            return

        # Clima de relâmpagos na Fase 2 (apenas visual, sem som)
        if self.numero == 2:
            self.flash_relampago = max(0.0, self.flash_relampago - dt * 5.5)
            self.proximo_relampago -= dt
            if self.proximo_relampago <= 0:
                self.proximo_relampago = random.uniform(11.0, 18.0)
                self.flash_relampago = 1.0

            # Atualiza corvos do cemitério
            self._assustar_corvos(self.jogador.rect.centerx, raio=175)
            for corvo in self.corvos:
                if corvo["voando"]:
                    corvo["x"] += corvo["vx"] * dt
                    corvo["y"] += corvo["vy"] * dt
                    corvo["vy"] -= 25 * dt  # ganha altitude suave

        self.tempo_tiro_triplo = max(0.0, self.tempo_tiro_triplo - dt)
        self.jogador.atualizar(dt, self.solidos, self.largura, self.escadas)

        if self.jogador.no_chao:
            self.combo_dash = 0

        if self.saida:
            self.saida.selado = bool(self.chefe and self.chefe.vivo)
            self.saida.atualizar(dt)

        novos_fantasmas = []
        fantasmas_vivos = sum(1 for i in self.inimigos if isinstance(i, Fantasma) and i.vivo)
        chefe_estava_vivo = bool(self.chefe and self.chefe.vivo)

        for inimigo in self.inimigos:
            if isinstance(inimigo, MonstroPalido):
                inimigo.fantasmas_ativos_arena = fantasmas_vivos
            inimigo.atualizar(dt, self.solidos)
            if isinstance(inimigo, MonstroPalido):
                if inimigo.fantasmas_invocados:
                    novos_fantasmas.extend(inimigo.fantasmas_invocados)
                    inimigo.fantasmas_invocados.clear()
                    self.sons.tocar("invocar")
                    self.camera.tremer(5, 0.16)
                if inimigo.orbes_lancados:
                    self.orbes_inimigos.extend(inimigo.orbes_lancados)
                    inimigo.orbes_lancados.clear()

        if novos_fantasmas:
            self.inimigos.extend(novos_fantasmas)

        for proj in self.projeteis:
            proj.atualizar(dt, self.solidos, self.largura)
            if not proj.ativo:
                for _ in range(8):
                    self.particulas.append(ParticulaPlasma(proj.pos.x, proj.pos.y))

        for orbe in self.orbes_inimigos:
            orbe.atualizar(dt, self.solidos)
            if orbe.ativo and orbe.rect.colliderect(self.jogador.rect):
                if self.jogador.receber_dano(orbe.dano, orbe.pos.x):
                    self.sons.tocar("dano")
                    self.camera.tremer(8, 0.22)
                orbe.ativo = False
        self.orbes_inimigos = [o for o in self.orbes_inimigos if o.ativo]

        for part in self.particulas:
            part.atualizar(dt)
        self.particulas = [p for p in self.particulas if p.vida > 0]

        for tf in self.textos_flutuantes:
            tf[1] -= 38 * dt
            tf[3] -= dt
        self.textos_flutuantes = [tf for tf in self.textos_flutuantes if tf[3] > 0]

        for reliquia in self.reliquias:
            reliquia.atualizar(dt)
        self.tempo_mensagem = max(0.0, self.tempo_mensagem - dt)

        self._combate()
        self._interacoes()
        self.projeteis = [p for p in self.projeteis if p.ativo]
        self.inimigos = [i for i in self.inimigos if i.vivo]

        # Feedback dramático quando o Monstro Pálido é derrotado
        if chefe_estava_vivo and self.chefe and not self.chefe.vivo:
            self.hitstop = 0.08
            self.camera.tremer(13, 0.45)
            self.sons.tocar("hitkill_fantasma")
            self.mensagem = ("Monstro Pálido Derrotado!", "Entre no Portal Dimensional Vermelho para avançar!")
            self.tempo_mensagem = 4.5

        self.camera.seguir(self.jogador.rect, dt)

        if self.jogador.rect.top > self.altura + 200:
            self.jogador.vida -= 1
            self.sons.tocar("dano")
            self.camera.tremer(8, 0.2)
            if self.jogador.vida > 0:
                self.jogador.reiniciar()
                self.camera.centralizar(self.jogador.rect)

        if self.jogador.vida <= 0:
            from cenas.game_over import GameOver
            self.jogo.trocar_cena(GameOver(self.jogo, self.numero))

    def _combate(self):
        # Golpe físico (Fase 1)
        area = self.jogador.hitbox_ataque
        if area:
            for inimigo in self.inimigos:
                if id(inimigo) not in self.jogador.alvos_acertados and area.colliderect(inimigo.rect):
                    inimigo.receber_dano(config.DANO_ATAQUE, self.jogador.rect.centerx)
                    self.jogador.alvos_acertados.add(id(inimigo))

        # Projéteis de plasma (Fase 2)
        for proj in self.projeteis:
            if not proj.ativo:
                continue
            for inimigo in self.inimigos:
                if inimigo.vivo and proj.rect.colliderect(inimigo.rect):
                    inimigo.receber_dano(proj.dano, proj.pos.x)
                    proj.ativo = False
                    if isinstance(inimigo, MonstroPalido):
                        self.camera.tremer(4, 0.10)
                    for _ in range(14):
                        self.particulas.append(ParticulaPlasma(proj.pos.x, proj.pos.y))
                    break

        # Contato com inimigos: Dash mata Fantasmas com HITKILL e reseta a recarga
        for inimigo in self.inimigos:
            if not inimigo.vivo:
                continue

            if self.jogador.avancando and isinstance(inimigo, Fantasma):
                zona_dash = self.jogador.rect.inflate(26, 14)
                if zona_dash.colliderect(inimigo.rect):
                    inimigo.vivo = False
                    self.jogador.recarga_avanco = 0.0
                    self.jogador.pulos_restantes = self.jogador.pulos_maximos
                    self.combo_dash += 1
                    self.hitstop = 0.045
                    self.camera.tremer(7, 0.16)
                    self.sons.tocar("hitkill_fantasma")

                    label = f"HITKILL {self.combo_dash}x!" if self.combo_dash > 1 else "HITKILL!"
                    self.textos_flutuantes.append([
                        inimigo.rect.centerx, inimigo.rect.top - 10, label, 0.9, (120, 255, 255)
                    ])
                    for _ in range(24):
                        self.particulas.append(
                            ParticulaPlasma(inimigo.rect.centerx, inimigo.rect.centery, (130, 255, 255))
                        )
                    continue

            if self.jogador.rect.colliderect(inimigo.rect):
                if self.jogador.receber_dano(inimigo.dano, inimigo.rect.centerx):
                    self.sons.tocar("dano")
                    self.camera.tremer(9, 0.22)

    def _interacoes(self):
        for reliquia in self.reliquias:
            if self.jogador.rect.colliderect(reliquia.rect):
                reliquia.coletada = True
                self.jogador.desbloquear(reliquia.tipo)
                self.jogo.habilidades.add(reliquia.tipo)
                self.mensagem = reliquia.textos
                self.tempo_mensagem = 5.0
        self.reliquias = [r for r in self.reliquias if not r.coletada]

        for cura in list(self.curas):
            if self.jogador.rect.colliderect(cura):
                self.curas.remove(cura)
                self.jogador.vida = min(config.VIDA_JOGADOR, self.jogador.vida + 2)
                self.sons.tocar("powerup")
                self.mensagem = ("Alma Restauradora!", "+2 pontos de vida recuperados")
                self.tempo_mensagem = 2.5

        for pw in list(self.powerups):
            if self.jogador.rect.colliderect(pw):
                self.powerups.remove(pw)
                self.tempo_tiro_triplo = 14.0
                self.sons.tocar("powerup")
                self.mensagem = ("Sobrecarga de Plasma!", "Disparo triplo ativado por 14 segundos!")
                self.tempo_mensagem = 3.0

        if self.jogador.avancando:
            zona = self.jogador.rect.inflate(72, 0)
            for barreira in list(self.barreiras):
                if zona.colliderect(barreira.rect):
                    self.barreiras.remove(barreira)
                    self.solidos.remove(barreira)
                    self.sons.tocar("hitkill_fantasma")
                    self.camera.tremer(10, 0.24)
                    self.hitstop = 0.04

        if self.barreiras and self.tempo_mensagem <= 0:
            perto = self.jogador.rect.inflate(300, 0)
            if any(perto.colliderect(b.rect) for b in self.barreiras):
                chave = ("barreira", self.jogador.tem_avanco)
                if chave not in self.dicas:
                    self.dicas.add(chave)
                    if self.jogador.tem_avanco:
                        self.mensagem = ("Parede rachada!", "Use o Dash (K ou SHIFT) para quebrar a barreira!")
                    else:
                        self.mensagem = ("Parede rachada...", "Falta uma relíquia para quebrá-la")
                    self.tempo_mensagem = 4.0

        # Portal dimensional vermelho na saída
        if self.saida and self.jogador.rect.colliderect(self.saida.rect):
            if self.chefe and self.chefe.vivo:
                if self.tempo_mensagem <= 0:
                    self.mensagem = ("Fenda Dimensional Selada!", "Derrote o Monstro Pálido para atravessar o portal!")
                    self.tempo_mensagem = 2.5
            else:
                self._proxima_fase()

    def _proxima_fase(self):
        if existe_fase(self.numero + 1):
            self.jogo.trocar_cena(Fase(self.jogo, self.numero + 1))
        else:
            from cenas.final import Final
            self.jogo.trocar_cena(Final(self.jogo))

    # ---------- desenho realista da Fase 2 ----------
    def _desenhar_fundo_cemiterio(self, tela):
        clarao = int(self.flash_relampago * 85)
        for y in range(0, config.ALTURA, 6):
            fator = y / config.ALTURA
            r = min(255, int(8 + 14 * fator) + clarao)
            g = min(255, int(12 + 20 * fator) + clarao)
            b = min(255, int(24 + 26 * fator) + int(clarao * 1.3))
            pygame.draw.rect(tela, (r, g, b), (0, y, config.LARGURA, 6))

        lua_x = int(760 - self.camera.x * 0.06) + self.camera.offset_x
        lua_y = 115 + self.camera.offset_y
        halo_lua = pygame.Surface((260, 260), pygame.SRCALPHA)
        pygame.draw.circle(halo_lua, (180, 200, 230, 18), (130, 130), 125)
        pygame.draw.circle(halo_lua, (210, 225, 245, 32), (130, 130), 85)
        tela.blit(halo_lua, (lua_x - 130, lua_y - 130))
        pygame.draw.circle(tela, (238, 240, 228), (lua_x, lua_y), 48)
        pygame.draw.circle(tela, (205, 208, 198), (lua_x - 14, lua_y - 10), 11)
        pygame.draw.circle(tela, (215, 218, 208), (lua_x + 12, lua_y + 14), 8)

        for i in range(-1, 6):
            cx = int(i * 340 - (self.camera.x * 0.18) % 340) + self.camera.offset_x
            pts = [(cx - 80, config.ALTURA), (cx + 90, 270), (cx + 260, 320), (cx + 420, config.ALTURA)]
            pygame.draw.polygon(tela, (15, 20, 32), pts)

        chao_y = self.altura - (2 * config.TAMANHO_TILE)
        for wx in range(120, self.largura - 100, 280):
            sx = int(wx - self.camera.x) + self.camera.offset_x
            sy = int(chao_y - self.camera.y) + self.camera.offset_y
            if -180 <= sx <= config.LARGURA + 180:
                pygame.draw.line(tela, (26, 30, 42), (sx - 60, sy - 58), (sx + 160, sy - 58), 3)
                pygame.draw.line(tela, (26, 30, 42), (sx - 60, sy - 16), (sx + 160, sy - 16), 3)
                for gx in range(sx - 50, sx + 160, 22):
                    pygame.draw.line(tela, (30, 35, 48), (gx, sy - 68), (gx, sy), 2)
                    pygame.draw.polygon(tela, (40, 46, 62), [(gx - 3, sy - 68), (gx, sy - 76), (gx + 3, sy - 68)])

                tronco_x = sx + 125
                pygame.draw.lines(tela, (18, 21, 30), False, [
                    (tronco_x, sy), (tronco_x - 6, sy - 65), (tronco_x + 8, sy - 125), (tronco_x - 14, sy - 175)
                ], 7)
                pygame.draw.lines(tela, (18, 21, 30), False, [
                    (tronco_x - 3, sy - 85), (tronco_x - 42, sy - 120), (tronco_x - 62, sy - 145)
                ], 4)
                pygame.draw.lines(tela, (18, 21, 30), False, [
                    (tronco_x + 4, sy - 105), (tronco_x + 45, sy - 140), (tronco_x + 68, sy - 155)
                ], 4)

                pygame.draw.rect(tela, (48, 54, 68), (sx - 4, sy - 8, 38, 8))
                pygame.draw.rect(tela, (62, 68, 84), (sx, sy - 44, 30, 36), border_top_left_radius=14, border_top_right_radius=14)
                pygame.draw.line(tela, (35, 40, 50), (sx + 8, sy - 34), (sx + 16, sy - 22), 2)

                pygame.draw.rect(tela, (52, 58, 74), (sx + 68, sy - 58, 8, 58))
                pygame.draw.rect(tela, (52, 58, 74), (sx + 55, sy - 42, 34, 8))

                chama = int(math.sin(self.t * 12 + wx) * 2)
                pygame.draw.rect(tela, (215, 205, 185), (sx + 38, sy - 10, 5, 10))
                luz_vela = pygame.Surface((46, 46), pygame.SRCALPHA)
                pygame.draw.circle(luz_vela, (255, 180, 70, 45), (23, 23), 20 + chama)
                tela.blit(luz_vela, (sx + 17, sy - 34))
                pygame.draw.circle(tela, (255, 220, 110), (sx + 40, sy - 13), 3)

        # Desenho dos corvos (pousados nas lápides/cruzes ou batendo asas no céu)
        for corvo in self.corvos:
            cx = int(corvo["x"] - self.camera.x) + self.camera.offset_x
            cy = int(corvo["y"] - self.camera.y) + self.camera.offset_y
            if -60 <= cx <= config.LARGURA + 60 and -60 <= cy <= config.ALTURA + 60:
                if corvo["voando"]:
                    asa = int(math.sin(self.t * 22 + corvo["fase"]) * 8)
                    pygame.draw.lines(tela, (12, 14, 20), False, [
                        (cx - 12, cy - asa), (cx - 4, cy), (cx, cy - 2), (cx + 4, cy), (cx + 12, cy - asa)
                    ], 3)
                    pygame.draw.circle(tela, (220, 45, 65), (cx + (3 if corvo["vx"] >= 0 else -3), cy - 2), 1)
                else:
                    # Silhueta pousada com cabeça e bico
                    pygame.draw.ellipse(tela, (14, 16, 22), (cx - 6, cy - 10, 12, 10))
                    pygame.draw.circle(tela, (14, 16, 22), (cx + 3, cy - 12), 4)
                    pygame.draw.polygon(tela, (70, 75, 85), [(cx + 6, cy - 13), (cx + 11, cy - 12), (cx + 6, cy - 10)])
                    pygame.draw.circle(tela, (220, 50, 70), (cx + 4, cy - 13), 1)

    def _desenhar_plataformas_cemiterio(self, tela):
        for p in self.plataformas:
            r = self.camera.aplicar(p.rect)
            if r.right < 0 or r.left > config.LARGURA:
                continue
            pygame.draw.rect(tela, (36, 42, 54), r)
            for bx in range(r.x, r.right, 32):
                pygame.draw.rect(tela, (28, 33, 44), (bx, r.y + 4, 30, r.height - 4), 1)
            pygame.draw.rect(tela, (48, 68, 62), (r.x, r.y, r.width, 6))
            pygame.draw.line(tela, (75, 102, 92), (r.x, r.y), (r.right, r.y), 2)

    def _desenhar_atmosfera_frente(self, tela):
        desloc = int((self.t * 28) % 240)
        nevoa = pygame.Surface((config.LARGURA + 240, 95), pygame.SRCALPHA)
        for nx in range(0, config.LARGURA + 240, 120):
            pygame.draw.ellipse(nevoa, (130, 155, 175, 26), (nx - 40, 18, 220, 75))
        tela.blit(nevoa, (-desloc + self.camera.offset_x, config.ALTURA - 85 + self.camera.offset_y))

        for esp in self.esporos:
            ex = int((esp[0] + math.sin(self.t * esp[2] + esp[3]) * 18) - self.camera.x) + self.camera.offset_x
            ey = int((esp[1] + math.cos(self.t * esp[2] * 0.8 + esp[3]) * 12) - self.camera.y) + self.camera.offset_y
            if 0 <= ex <= config.LARGURA and 0 <= ey <= config.ALTURA:
                pygame.draw.circle(tela, (150, 230, 235), (ex, ey), 2)

    def desenhar(self, tela):
        tela.fill(FUNDOS.get(self.numero, (25, 20, 30)))

        if self.numero == 2:
            self._desenhar_fundo_cemiterio(tela)
            self._desenhar_plataformas_cemiterio(tela)
        else:
            for p in self.plataformas:
                p.desenhar(tela, self.camera)

        for b in self.barreiras:
            b.desenhar(tela, self.camera)
        for escada in self.escadas:
            escada.desenhar(tela, self.camera)

        if self.saida:
            self.saida.desenhar(tela, self.camera)

        for r in self.reliquias:
            r.desenhar(tela, self.camera)

        # Orbes de cura (H)
        for cura in self.curas:
            rc = self.camera.aplicar(cura)
            pulso = int(math.sin(self.t * 6) * 3)
            pygame.draw.circle(tela, (60, 235, 140), rc.center, 10 + pulso)
            pygame.draw.circle(tela, (220, 255, 235), rc.center, 5)

        # Cristais de Tiro Triplo (T)
        for pw in self.powerups:
            rp = self.camera.aplicar(pw)
            flutuar = int(math.sin(self.t * 5) * 4)
            cx, cy = rp.centerx, rp.centery + flutuar
            losango = [(cx, cy - 16), (cx + 12, cy), (cx, cy + 16), (cx - 12, cy)]
            pygame.draw.polygon(tela, (0, 220, 255), losango)
            pygame.draw.polygon(tela, config.BRANCO, losango, 2)

        for inimigo in self.inimigos:
            inimigo.desenhar(tela, self.camera)

        self.jogador.desenhar(tela, self.camera)

        for proj in self.projeteis:
            proj.desenhar(tela, self.camera)
        for orbe in self.orbes_inimigos:
            orbe.desenhar(tela, self.camera)
        for part in self.particulas:
            part.desenhar(tela, self.camera)

        # Textos flutuantes de HITKILL / Combo
        for tf in self.textos_flutuantes:
            pos = self.camera.aplicar(pygame.Rect(round(tf[0]), round(tf[1]), 1, 1)).topleft
            img = self.fonte_combo.render(tf[2], True, tf[4])
            tela.blit(img, img.get_rect(center=pos))

        if self.numero == 2:
            self._desenhar_atmosfera_frente(tela)

        self.hud.desenhar(tela, self.jogador)

        if self.tempo_tiro_triplo > 0:
            txt_pw = self.fonte.render(f"Plasma Triplo: {self.tempo_tiro_triplo:.1f}s", True, (80, 240, 255))
            tela.blit(txt_pw, (16, 120))

        # Barra de vida do Monstro Pálido
        if self.chefe and self.chefe.vivo and abs(self.jogador.rect.centerx - self.chefe.rect.centerx) < 750:
            larg_barra = 420
            bx = config.LARGURA // 2 - larg_barra // 2
            by = 48
            nome = self.fonte.render("MONSTRO PÁLIDO - SENHOR DO CEMITÉRIO", True, (235, 225, 240))
            tela.blit(nome, nome.get_rect(center=(config.LARGURA // 2, by - 14)))
            pygame.draw.rect(tela, (25, 15, 25), (bx - 2, by - 2, larg_barra + 4, 16), border_radius=4)
            atual = int(larg_barra * max(0, self.chefe.vida) / self.chefe.vida_max)
            pygame.draw.rect(tela, (190, 35, 65), (bx, by, atual, 12), border_radius=3)

        ajuda = (
            f"Fase {self.numero} | A-D: andar | W/S: escada | ESPAÇO: pular | K/SHIFT: dash hitkill | J/X: plasma"
            if self.numero == 2
            else f"Fase {self.numero} | A-D: andar | ESPAÇO: pular | J/X: atacar | ESC: menu"
        )
        tela.blit(self.fonte.render(ajuda, True, config.CINZA), (12, 10))

        if self.mensagem and self.tempo_mensagem > 0:
            titulo, descricao = self.mensagem
            for texto, fonte, cor, y in ((titulo, self.fonte_msg, config.DOURADO, 130),
                                         (descricao, self.fonte_msg2, config.BRANCO, 168)):
                sombra = fonte.render(texto, True, (0, 0, 0))
                img = fonte.render(texto, True, cor)
                pos = img.get_rect(center=(config.LARGURA // 2, y))
                tela.blit(sombra, pos.move(2, 2))
                tela.blit(img, pos)