import math
import random
import pygame
import config
from nucleo.cena import Cena
from nucleo.camera import Camera
from entidades.jogador import Jogador
from entidades.inimigos_comuns import (
    GuerreiroCorrompido,
    ZumbiTsunami,
    ZumbiAnciao,
    GuardiaoFloresta,
)
from entidades.obstaculos import OrbeChama
from entidades.reliquia import Reliquia
from entidades.barreira import Barreira
from entidades.saida import Saida
from entidades.tocha import Tocha
from sistemas.mapa import carregar_mapa, existe_fase
from sistemas.hud import Hud

FUNDOS = {1: (25, 20, 30), 2: (18, 26, 38), 3: (2, 4, 6)}


class Particula:
    """Partícula leve para fumaça, sangue, faíscas, terra e cartuchos ejetados."""

    def __init__(self, x, y, vx, vy, cor, raio=3, vida=0.35, gravidade=220.0, eh_cartucho=False):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.cor = cor
        self.raio = raio
        self.vida = vida
        self.vida_max = vida
        self.gravidade = gravidade
        self.eh_cartucho = eh_cartucho

    def atualizar(self, dt):
        self.vida -= dt
        self.vy += self.gravidade * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def desenhar(self, tela, camera):
        if self.vida <= 0:
            return
        sx = round(self.x - camera.x)
        sy = round(self.y - camera.y)
        if sx < -20 or sx > config.LARGURA + 20:
            return
        if self.eh_cartucho:
            pygame.draw.rect(tela, (215, 45, 45), (sx - 3, sy - 2, 4, 3))
            pygame.draw.rect(tela, config.DOURADO, (sx + 1, sy - 2, 2, 3))
        else:
            fator = max(0.25, self.vida / self.vida_max)
            raio = max(1, round(self.raio * fator))
            pygame.draw.circle(tela, self.cor, (sx, sy), raio)


class Fase(Cena):
    def __init__(self, jogo, numero=1):
        super().__init__(jogo)
        self.numero = numero
        self.habilidades_entrada = set(jogo.habilidades)
        self.fonte = pygame.font.Font(None, 28)
        self.fonte_msg = pygame.font.Font(None, 40)
        self.fonte_msg2 = pygame.font.Font(None, 28)

        dados = carregar_mapa(numero)
        self.largura, self.altura = dados.largura, dados.altura
        self.plataformas = dados.plataformas
        self.barreiras = [Barreira(*b) for b in dados.barreiras]
        self.troncos = dados.troncos
        self.espinhos = dados.espinhos
        self.vinhas = dados.vinhas
        self.cipos = dados.cipos
        self.armadilhas = dados.armadilhas
        self.lapides = dados.lapides
        self.solidos = self.plataformas + self.barreiras + self.troncos
        self.saida = Saida(*dados.saida) if dados.saida else None

        self.inimigos = [GuerreiroCorrompido(x, y) for x, y in dados.inimigos]
        self.inimigos += [ZumbiTsunami(x, y) for x, y in dados.zumbis]
        self.inimigos += [ZumbiAnciao(x, y) for x, y in dados.zumbis_brutos]
        self.inimigos += [GuardiaoFloresta(x, y) for x, y in dados.chefes]

        self.tochas = [Tocha(x, y) for x, y in dados.tochas]
        self.reliquias = [Reliquia(t, x, y) for t, x, y in dados.reliquias
                          if t not in jogo.habilidades]

        x, y = dados.inicio
        eh_fase_3 = (numero == 3)
        self.jogador = Jogador(x - Jogador.LARGURA // 2, y - Jogador.ALTURA, modo_guerreira=eh_fase_3)
        for habilidade in jogo.habilidades:
            self.jogador.desbloquear(habilidade)

        self.projeteis = []
        self.ondas_sombrias = []
        self.particulas = []
        self.orbes_cura = []
        self.vagalumes = []
        self.morcegos = []
        self.olhos_fundo = []
        self.arvores_fundo = []
        self.arvores_medias = []
        self.arbustos_solo = []

        # Controle da horda dinâmica de zumbis na Fase 3
        self.zumbis_derrotados = 0
        self.zumbis_nascidos_extra = 0
        self.max_zumbis_extra = 38
        self.fila_spawns = []
        self.timer_pressao_horda = 4.0

        self.shake_tempo = 0.0
        self.shake_forca = 0
        self.aviso_portal_cooldown = 0.0

        self.camera = Camera(self.largura, self.altura)
        self.camera.centralizar(self.jogador.rect)
        self.hud = Hud()
        self.mensagem = None
        self.tempo_mensagem = 0.0
        self.dicas = set()

        if eh_fase_3:
            self._gerar_floresta_sombria()
            self.mensagem = (
                "Fase 3 - As Profundezas da Floresta Sombria",
                "Os zumbis escalam atrás de você! Derrote a Abominação Derretida no final!",
            )
            self.tempo_mensagem = 4.5

    def _chefe_ativo(self):
        for inimigo in self.inimigos:
            if getattr(inimigo, "eh_chefe", False) and inimigo.vivo:
                return inimigo
        return None

    def _tremer_camera(self, duracao, forca):
        self.shake_tempo = max(self.shake_tempo, duracao)
        self.shake_forca = max(self.shake_forca, forca)

    def _emitir_particulas(self, x, y, qtd, cor, vel_x=(-130, 130), vel_y=(-180, -30), raio=3, vida=0.35, grav=280.0):
        for _ in range(qtd):
            self.particulas.append(Particula(
                x, y,
                random.uniform(*vel_x),
                random.uniform(*vel_y),
                cor,
                raio=raio,
                vida=random.uniform(vida * 0.65, vida * 1.25),
                gravidade=grav,
            ))

    def _gerar_floresta_sombria(self):
        """Gera árvores sombrias, arbustos, morcegos, olhos vermelhos no fundo e vaga-lumes."""
        rng = random.Random(303)
        solo_y = self.altura - config.TAMANHO_TILE * 2

        x = -80
        while x < self.largura + 200:
            tipo = rng.choice(["pinheiro", "copa_densa", "copa_densa", "seca"])
            altura = rng.randint(290, 450)
            largura = rng.randint(26, 44)
            self.arvores_fundo.append({
                "x": x,
                "solo_y": solo_y + 12,
                "tipo": tipo,
                "altura": altura,
                "largura": largura,
            })
            x += rng.randint(44, 72)

        x = 20
        while x < self.largura + 120:
            tipo = rng.choices(
                ["grande_densa", "pinheiro", "galhos_secos", "pequena"],
                weights=[34, 24, 26, 16],
            )[0]
            if tipo == "grande_densa":
                altura = rng.randint(340, 455)
                largura = rng.randint(36, 50)
            elif tipo == "pinheiro":
                altura = rng.randint(320, 430)
                largura = rng.randint(24, 34)
            elif tipo == "galhos_secos":
                altura = rng.randint(250, 365)
                largura = rng.randint(20, 30)
            else:
                altura = rng.randint(155, 225)
                largura = rng.randint(14, 22)

            self.arvores_medias.append({
                "x": x,
                "solo_y": solo_y,
                "tipo": tipo,
                "altura": altura,
                "largura": largura,
            })
            x += rng.randint(62, 105)

        x = 0
        while x < self.largura + 80:
            self.arbustos_solo.append({
                "x": x,
                "y": solo_y,
                "raio": rng.randint(20, 36),
                "tom": rng.choice([(6, 14, 10), (9, 19, 13), (5, 11, 8)]),
            })
            x += rng.randint(30, 58)

        for _ in range(38):
            self.vagalumes.append({
                "x": rng.uniform(40, self.largura - 40),
                "y": rng.uniform(150, solo_y - 24),
                "fase": rng.uniform(0, math.tau),
                "vel": rng.uniform(1.3, 2.6),
                "amp_x": rng.uniform(10, 26),
                "amp_y": rng.uniform(6, 16),
            })

        for _ in range(28):
            dir_voo = rng.choice([-1, 1])
            self.morcegos.append({
                "x": rng.uniform(0, self.largura),
                "y": rng.uniform(75, solo_y - 120),
                "vx": dir_voo * rng.uniform(75, 145),
                "dir": dir_voo,
                "fase": rng.uniform(0, math.tau),
                "vel_onda": rng.uniform(2.2, 4.2),
                "amp_y": rng.uniform(10, 24),
                "escala": rng.uniform(0.85, 1.35),
                "distante": rng.random() < 0.45,
            })

        for _ in range(42):
            distante = rng.random() < 0.55
            self.olhos_fundo.append({
                "x": rng.uniform(80, self.largura - 80),
                "y": rng.uniform(solo_y - 250, solo_y - 18) if distante else rng.uniform(solo_y - 180, solo_y - 14),
                "parallax": 0.32 if distante else 0.62,
                "espaco": 5 if distante else 7,
                "raio": 2 if distante else 3,
                "fase": rng.uniform(0, math.tau),
                "vel_piscar": rng.uniform(0.75, 1.45),
            })

    # ---------- eventos ----------
    def eventos(self, eventos):
        for e in eventos:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    from cenas.menu import Menu
                    self.jogo.trocar_cena(Menu(self.jogo))
                elif e.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    self.jogador.pular()
                elif e.key in (pygame.K_j, pygame.K_x):
                    novos_tiros = self.jogador.atacar()
                    if novos_tiros:
                        self.projeteis.extend(novos_tiros)
                        self._tremer_camera(0.11, 5)
                        d = self.jogador.direcao
                        boca_x = self.jogador.rect.centerx + 30 * d
                        boca_y = self.jogador.rect.centery + 3
                        self._emitir_particulas(
                            boca_x, boca_y, 7, (175, 180, 175),
                            vel_x=(30 * d, 140 * d), vel_y=(-45, 25), raio=4, vida=0.45, grav=-25.0
                        )
                        self.particulas.append(Particula(
                            self.jogador.rect.centerx, boca_y - 2,
                            -d * random.uniform(55, 95), random.uniform(-170, -120),
                            config.DOURADO, vida=0.65, gravidade=480.0, eh_cartucho=True
                        ))
                elif e.key in (pygame.K_k, pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.jogador.avancar()

    # ---------- lógica ----------
    def _encontrar_ponto_spawn_zumbi(self):
        """Encontra um trecho seguro de terra firme perto da guerreira para um zumbi emergir."""
        t = config.TAMANHO_TILE
        jx = self.jogador.rect.centerx
        jy = self.jogador.rect.centery
        candidatos = []

        for p in self.plataformas:
            if any(q is not p and q.rect.collidepoint(p.rect.centerx, p.rect.top - 8) for q in self.plataformas):
                continue
            for x in range(p.rect.left + t, p.rect.right - t, t):
                dist_x = abs(x - jx)
                dist_y = abs(p.rect.top - jy)
                if 230 <= dist_x <= 640 and dist_y <= 340:
                    zona = pygame.Rect(x - 22, p.rect.top - 60, 44, 58)
                    if any(s.rect.colliderect(zona) for s in self.solidos):
                        continue
                    if any(esp.rect.colliderect(zona) for esp in self.espinhos):
                        continue
                    if any(arm.rect.colliderect(zona) for arm in self.armadilhas):
                        continue
                    candidatos.append((x, p.rect.top))

        if not candidatos:
            return None
        return random.choice(candidatos)

    def _spawnar_zumbi_horda(self):
        if self.zumbis_nascidos_extra >= self.max_zumbis_extra:
            return False
        zumbis_vivos = sum(1 for i in self.inimigos if i.vivo and not getattr(i, "eh_chefe", False))
        if zumbis_vivos >= 18:
            return False

        ponto = self._encontrar_ponto_spawn_zumbi()
        if ponto is None:
            return False

        sx, sy = ponto
        self.zumbis_nascidos_extra += 1
        if self.zumbis_nascidos_extra % 5 == 0:
            novo = ZumbiAnciao(sx, sy)
        else:
            novo = ZumbiTsunami(sx, sy, nascendo=True)
        self.inimigos.append(novo)

        self._emitir_particulas(
            sx, sy - 6, 12, (48, 36, 28),
            vel_x=(-95, 95), vel_y=(-190, -50), raio=4, vida=0.55
        )
        self._emitir_particulas(
            sx, sy - 14, 7, (65, 130, 55),
            vel_x=(-50, 50), vel_y=(-90, -20), raio=3, vida=0.5, grav=-20.0
        )
        return True

    def _atualizar_horda_zumbis(self, dt):
        if self.numero != 3:
            return

        novos_pendentes = []
        for tempo in self.fila_spawns:
            tempo -= dt
            if tempo <= 0:
                self._spawnar_zumbi_horda()
            else:
                novos_pendentes.append(tempo)
        self.fila_spawns = novos_pendentes

        self.timer_pressao_horda -= dt
        if self.timer_pressao_horda <= 0:
            self.timer_pressao_horda = 4.5
            jx = self.jogador.rect.centerx
            proximos = sum(
                1 for i in self.inimigos
                if i.vivo and not getattr(i, "eh_chefe", False) and abs(i.rect.centerx - jx) < 680
            )
            if proximos < 3 and self.zumbis_nascidos_extra < self.max_zumbis_extra:
                self.fila_spawns.append(0.8)

    def _atualizar_morcegos(self, dt):
        for m in self.morcegos:
            m["x"] += m["vx"] * dt
            if m["dir"] == 1 and m["x"] > self.largura + 120:
                m["x"] = -120
            elif m["dir"] == -1 and m["x"] < -120:
                m["x"] = self.largura + 120

    def atualizar(self, dt):
        self.jogador.atualizar(dt, self.solidos, self.largura, self.cipos)
        for inimigo in self.inimigos:
            if isinstance(inimigo, (ZumbiTsunami, ZumbiAnciao, GuardiaoFloresta)):
                inimigo.atualizar(dt, self.solidos, self.jogador, self.cipos)
            else:
                inimigo.atualizar(dt, self.solidos, self.jogador)
            if getattr(inimigo, "eh_chefe", False):
                if inimigo.ondas_pendentes:
                    self.ondas_sombrias.extend(inimigo.ondas_pendentes)
                    inimigo.ondas_pendentes.clear()
                if inimigo.tremor_pendente:
                    inimigo.tremor_pendente = False
                    self._tremer_camera(0.22, 8)

        for onda in self.ondas_sombrias:
            onda.atualizar(dt, self.solidos)
        for proj in self.projeteis:
            proj.atualizar(dt, self.solidos)
            if not proj.ativo and proj.atingiu_parede:
                self._emitir_particulas(
                    proj.pos.x, proj.pos.y, 4, (255, 210, 100),
                    vel_x=(-90, 90), vel_y=(-110, 40), raio=2, vida=0.22
                )
        for arm in self.armadilhas:
            arm.atualizar(dt)
        for tocha in self.tochas:
            tocha.atualizar(dt)
        for reliquia in self.reliquias:
            reliquia.atualizar(dt)
        for orbe in self.orbes_cura:
            orbe.atualizar(dt, self.solidos)
        for part in self.particulas:
            part.atualizar(dt)

        if self.numero == 3:
            self._atualizar_morcegos(dt)
            self._atualizar_horda_zumbis(dt)

        self.tempo_mensagem = max(0.0, self.tempo_mensagem - dt)
        self.aviso_portal_cooldown = max(0.0, self.aviso_portal_cooldown - dt)
        if self.shake_tempo > 0:
            self.shake_tempo = max(0.0, self.shake_tempo - dt)
            if self.shake_tempo == 0:
                self.shake_forca = 0

        self._combate()
        self._interacoes()
        self.ondas_sombrias = [o for o in self.ondas_sombrias if o.ativo]
        self.projeteis = [p for p in self.projeteis if p.ativo]
        self.particulas = [p for p in self.particulas if p.vida > 0]
        self.orbes_cura = [o for o in self.orbes_cura if not o.coletado]
        self.inimigos = [i for i in self.inimigos if i.vivo]
        self.camera.seguir(self.jogador.rect, dt)

        if self.jogador.rect.top > self.altura + 200:
            self.jogador.vida -= 1
            if self.jogador.vida > 0:
                self.jogador.reiniciar()
                self.camera.centralizar(self.jogador.rect)

        if self.jogador.vida <= 0:
            from cenas.game_over import GameOver
            self.jogo.habilidades = set(self.habilidades_entrada)
            self.jogo.trocar_cena(GameOver(self.jogo, self.numero))

    def _ao_derrotar_inimigo(self, inimigo):
        eh_chefe = getattr(inimigo, "eh_chefe", False)
        qtd_particulas = 42 if eh_chefe else 14
        cor_explosao = (126, 162, 52) if eh_chefe else (130, 22, 30)
        self._emitir_particulas(
            inimigo.rect.centerx, inimigo.rect.centery, qtd_particulas, cor_explosao,
            vel_x=(-230, 230), vel_y=(-270, -40), raio=6 if eh_chefe else 4, vida=0.75 if eh_chefe else 0.5
        )
        if eh_chefe:
            self._tremer_camera(0.48, 10)
            self.ondas_sombrias.clear()
            self.fila_spawns.clear()
            self.mensagem = (
                "A Abominação Derretida Tombou!",
                "O selo sombrio se desfez — o portal para a saída está aberto!",
            )
            self.tempo_mensagem = 5.0
            if self.saida:
                self._emitir_particulas(
                    self.saida.rect.centerx, self.saida.rect.centery, 26, config.DOURADO,
                    vel_x=(-160, 160), vel_y=(-200, 60), raio=4, vida=0.65, grav=60.0
                )
        elif self.numero == 3:
            self.zumbis_derrotados += 1
            if self.zumbis_nascidos_extra < self.max_zumbis_extra:
                self.fila_spawns.append(random.uniform(1.1, 2.0))
                if self.zumbis_derrotados % 2 == 0:
                    self.fila_spawns.append(random.uniform(2.1, 3.3))

        eh_anciao = isinstance(inimigo, ZumbiAnciao)
        if self.numero == 3 and (eh_chefe or eh_anciao or random.random() < 0.16):
            self.orbes_cura.append(OrbeChama(inimigo.rect.centerx, inimigo.rect.centery))

    def _combate(self):
        area = self.jogador.hitbox_ataque
        if area:
            for inimigo in self.inimigos:
                if inimigo.vivo and id(inimigo) not in self.jogador.alvos_acertados and area.colliderect(inimigo.rect):
                    inimigo.receber_dano(config.DANO_ATAQUE, self.jogador.rect.centerx)
                    self.jogador.alvos_acertados.add(id(inimigo))
                    if not inimigo.vivo:
                        self._ao_derrotar_inimigo(inimigo)

        for proj in self.projeteis:
            if not proj.ativo:
                continue
            for inimigo in self.inimigos:
                if inimigo.vivo and proj.rect.colliderect(inimigo.rect):
                    inimigo.receber_dano(config.DANO_ATAQUE, self.jogador.rect.centerx)
                    proj.ativo = False
                    cor_sangue = (132, 168, 56) if getattr(inimigo, "eh_chefe", False) else (165, 24, 32)
                    self._emitir_particulas(
                        proj.pos.x, proj.pos.y, 5, cor_sangue,
                        vel_x=(-110, 110), vel_y=(-140, 20), raio=3, vida=0.3
                    )
                    if not inimigo.vivo:
                        self._ao_derrotar_inimigo(inimigo)
                    break

        for onda in self.ondas_sombrias:
            if onda.ativo and self.jogador.rect.colliderect(onda.rect):
                if self.jogador.receber_dano(1, onda.rect.centerx):
                    self._tremer_camera(0.18, 7)
                onda.ativo = False

        for inimigo in self.inimigos:
            if inimigo.vivo and self.jogador.rect.colliderect(inimigo.rect):
                if self.jogador.receber_dano(inimigo.dano, inimigo.rect.centerx):
                    self._tremer_camera(0.16, 6)

        # Galhos com espinhos no chão (G) causam dano apenas na guerreira
        for esp in self.espinhos:
            if self.jogador.rect.colliderect(esp.rect):
                if self.jogador.receber_dano(1, esp.rect.centerx):
                    self._tremer_camera(0.14, 5)

        # Vinhas espinhosas suspensas (V) causam dano apenas na guerreira
        for vinha in self.vinhas:
            if self.jogador.rect.colliderect(vinha.rect):
                if self.jogador.receber_dano(1, vinha.rect.centerx):
                    self._tremer_camera(0.14, 5)

        # Armadilhas de caçador (M) fecham e ferem apenas a guerreira
        for arm in self.armadilhas:
            if arm.fechada:
                continue
            if self.jogador.rect.colliderect(arm.rect):
                if self.jogador.receber_dano(1, arm.rect.centerx):
                    arm.acionar()
                    self._tremer_camera(0.16, 6)
                    self._emitir_particulas(arm.rect.centerx, arm.rect.top, 6, (210, 195, 160), raio=2, vida=0.25)

    def _interacoes(self):
        for reliquia in self.reliquias:
            if self.jogador.rect.colliderect(reliquia.rect):
                reliquia.coletada = True
                self.jogador.desbloquear(reliquia.tipo)
                self.jogo.habilidades.add(reliquia.tipo)
                self.mensagem = reliquia.textos
                self.tempo_mensagem = 5.0
        self.reliquias = [r for r in self.reliquias if not r.coletada]

        for orbe in self.orbes_cura:
            if not orbe.coletado and self.jogador.rect.colliderect(orbe.rect):
                orbe.coletado = True
                if self.jogador.vida < self.jogador.vida_max:
                    self.jogador.vida += 1
                self._emitir_particulas(
                    orbe.rect.centerx, orbe.rect.centery, 10, (255, 195, 70),
                    vel_x=(-90, 90), vel_y=(-140, -20), raio=3, vida=0.4, grav=80.0
                )

        if self.jogador.avancando:
            zona = self.jogador.rect.inflate(72, 0)
            for barreira in list(self.barreiras):
                if zona.colliderect(barreira.rect):
                    self.barreiras.remove(barreira)
                    self.solidos.remove(barreira)

        if self.barreiras and self.tempo_mensagem <= 0:
            perto = self.jogador.rect.inflate(300, 0)
            if any(perto.colliderect(b.rect) for b in self.barreiras):
                chave = ("barreira", self.jogador.tem_avanco)
                if chave not in self.dicas:
                    self.dicas.add(chave)
                    if self.jogador.tem_avanco:
                        self.mensagem = ("Parede rachada!", "Chegue perto e avance contra ela (K ou SHIFT)")
                    else:
                        self.mensagem = ("Parede rachada...", "Falta uma relíquia para quebrá-la")
                    self.tempo_mensagem = 4.0

        if self.saida and self.jogador.rect.colliderect(self.saida.rect):
            chefe = self._chefe_ativo()
            if chefe is not None:
                if self.aviso_portal_cooldown <= 0:
                    self.mensagem = (
                        "Portal Selado pelas Trevas!",
                        "Mate a Abominação Derretida para liberar a passagem!",
                    )
                    self.tempo_mensagem = 3.2
                    self.aviso_portal_cooldown = 2.5
            else:
                self._proxima_fase()

    def _proxima_fase(self):
        if existe_fase(self.numero + 1):
            self.jogo.trocar_cena(Fase(self.jogo, self.numero + 1))
        else:
            from cenas.final import Final
            self.jogo.trocar_cena(Final(self.jogo))

    # ---------- desenho ----------
    def _posicao_lua(self):
        lua_x = int(config.LARGURA * 0.76 - self.camera.x * 0.03)
        lua_y = 104
        return lua_x, lua_y

    def _desenhar_lua_cheia(self, tela):
        lx, ly = self._posicao_lua()
        halo = pygame.Surface((320, 320), pygame.SRCALPHA)
        for raio, alpha in ((150, 10), (118, 18), (88, 28), (64, 42)):
            pygame.draw.circle(halo, (165, 190, 175, alpha), (160, 160), raio)
        tela.blit(halo, (lx - 160, ly - 160))

        pygame.draw.circle(tela, (195, 205, 190), (lx, ly), 44)
        pygame.draw.circle(tela, (218, 225, 212), (lx - 6, ly - 6), 36)

        pygame.draw.circle(tela, (162, 172, 158), (lx - 15, ly - 10), 10)
        pygame.draw.circle(tela, (154, 164, 150), (lx + 14, ly + 8), 12)
        pygame.draw.circle(tela, (168, 178, 164), (lx + 4, ly - 20), 6)

        t = pygame.time.get_ticks() * 0.018
        nuvens = pygame.Surface((260, 130), pygame.SRCALPHA)
        for idx, (oy, larg, vel) in enumerate(((22, 150, 1.0), (50, 175, -0.7), (78, 140, 0.85))):
            nx = int((t * vel + idx * 70) % 240) - 60
            pygame.draw.ellipse(nuvens, (3, 6, 8, 175), (nx, oy, larg, 22))
        tela.blit(nuvens, (lx - 130, ly - 60))

    def _desenhar_arvore(self, tela, arvore, parallax, distante=False):
        sx = int(arvore["x"] - self.camera.x * parallax)
        if sx < -180 or sx > config.LARGURA + 180:
            return

        sy = arvore["solo_y"]
        h = arvore["altura"]
        w = arvore["largura"]
        topo_y = sy - h
        tipo = arvore["tipo"]

        if distante:
            cor_tronco = (4, 8, 7)
            cor_folha_1 = (5, 10, 9)
            cor_folha_2 = (7, 13, 11)
        else:
            cor_tronco = (9, 8, 11)
            cor_casca = (15, 14, 18)
            cor_folha_1 = (6, 13, 9)
            cor_folha_2 = (9, 19, 13)
            cor_folha_3 = (12, 24, 17)

        pygame.draw.polygon(tela, cor_tronco, [
            (sx - w // 2 - 6, sy),
            (sx - w // 4, topo_y + h // 4),
            (sx + w // 4, topo_y + h // 4),
            (sx + w // 2 + 6, sy),
        ])
        if not distante:
            pygame.draw.line(tela, cor_casca, (sx - 2, sy - 6), (sx - 1, topo_y + h // 3), 2)

        if tipo == "pinheiro":
            niveis = 6
            for i in range(niveis):
                prog = i / niveis
                ny = int(topo_y + prog * (h * 0.72))
                meia_larg = int(18 + prog * (w * 2.3))
                alt_cone = int(h * 0.22)
                cor = cor_folha_1 if i % 2 == 0 else (cor_folha_1 if distante else cor_folha_2)
                pygame.draw.polygon(tela, cor, [
                    (sx, ny - 14),
                    (sx - meia_larg, ny + alt_cone),
                    (sx + meia_larg, ny + alt_cone),
                ])

        elif tipo in ("galhos_secos", "seca"):
            pygame.draw.line(tela, cor_tronco, (sx, sy - h // 4), (sx - 6, topo_y + 18), max(4, w // 4))
            galhos = [
                ((sx - 2, topo_y + int(h * 0.45)), (sx - 46, topo_y + int(h * 0.26)), (sx - 68, topo_y + int(h * 0.14))),
                ((sx + 2, topo_y + int(h * 0.38)), (sx + 48, topo_y + int(h * 0.20)), (sx + 72, topo_y + int(h * 0.08))),
                ((sx - 4, topo_y + int(h * 0.24)), (sx - 34, topo_y + 12), (sx - 46, topo_y - 10)),
                ((sx - 3, topo_y + int(h * 0.18)), (sx + 26, topo_y + 4), (sx + 38, topo_y - 14)),
            ]
            esp = 2 if distante else 4
            for p1, p2, p3 in galhos:
                pygame.draw.line(tela, cor_tronco, p1, p2, esp)
                pygame.draw.line(tela, cor_tronco, p2, p3, max(1, esp - 2))
                pygame.draw.line(tela, cor_tronco, p2, (p2[0] + (14 if p2[0] > sx else -14), p2[1] - 18), max(1, esp - 2))

        elif tipo in ("grande_densa", "copa_densa"):
            if not distante:
                pygame.draw.line(tela, cor_tronco, (sx, topo_y + 95), (sx - 48, topo_y + 42), 7)
                pygame.draw.line(tela, cor_tronco, (sx, topo_y + 85), (sx + 52, topo_y + 38), 7)

            copas = [
                (sx - 56, topo_y + 46, 52, cor_folha_1),
                (sx + 56, topo_y + 48, 50, cor_folha_1),
                (sx - 32, topo_y + 18, 58, cor_folha_1 if distante else cor_folha_2),
                (sx + 34, topo_y + 20, 56, cor_folha_1 if distante else cor_folha_2),
                (sx, topo_y + 2, 64, cor_folha_2 if distante else cor_folha_3),
            ]
            for cx, cy, r_copa, cor_c in copas:
                pygame.draw.circle(tela, cor_c, (cx, cy), r_copa)

        else:
            pygame.draw.circle(tela, cor_folha_1, (sx - 20, topo_y + 26), 28)
            pygame.draw.circle(tela, cor_folha_1, (sx + 20, topo_y + 28), 26)
            pygame.draw.circle(tela, cor_folha_2 if not distante else cor_folha_1, (sx, topo_y + 12), 34)

    def _desenhar_fundo_floresta(self, tela):
        pygame.draw.rect(tela, (4, 7, 10), (0, 0, config.LARGURA, 240))
        self._desenhar_lua_cheia(tela)

        for arv in self.arvores_fundo:
            self._desenhar_arvore(tela, arv, parallax=0.25, distante=True)

        self._desenhar_morcegos(tela, apenas_distantes=True)

        for arv in self.arvores_medias:
            self._desenhar_arvore(tela, arv, parallax=0.62, distante=False)

        for arb in self.arbustos_solo:
            ax = int(arb["x"] - self.camera.x * 0.85)
            if -60 <= ax <= config.LARGURA + 60:
                pygame.draw.circle(tela, arb["tom"], (ax, arb["y"] + 4), arb["raio"])

    def _desenhar_solo_floresta(self, tela):
        t = config.TAMANHO_TILE
        for p in self.plataformas:
            r = self.camera.aplicar(p.rect)
            if r.right < 0 or r.left > config.LARGURA:
                continue
            pygame.draw.rect(tela, (20, 16, 15), r)
            for tx in range(p.rect.x, p.rect.right, t):
                sx = round(tx - self.camera.x)
                pygame.draw.line(tela, (14, 11, 10), (sx + 6, r.y + 18), (sx + 22, r.y + 22), 2)
                pygame.draw.circle(tela, (30, 25, 23), (sx + 34, r.y + 32), 3)

                sonda_topo = pygame.Rect(tx + 8, p.rect.y - 8, t - 16, 6)
                coberto = any(q is not p and q.rect.colliderect(sonda_topo) for q in self.plataformas)
                if not coberto:
                    pygame.draw.rect(tela, (16, 36, 20), (sx, r.y, t, 7))
                    pygame.draw.line(tela, (28, 54, 30), (sx, r.y), (sx + t, r.y), 2)

    def _desenhar_morcegos(self, tela, apenas_distantes=False):
        t = pygame.time.get_ticks() * 0.001
        for m in self.morcegos:
            if apenas_distantes != m["distante"]:
                continue
            parallax = 0.45 if m["distante"] else 0.92
            sx = round(m["x"] - self.camera.x * parallax)
            sy = round(m["y"] + math.sin(t * m["vel_onda"] + m["fase"]) * m["amp_y"] - self.camera.y * 0.4)
            if sx < -40 or sx > config.LARGURA + 40:
                continue

            esc = m["escala"] * (0.75 if m["distante"] else 1.05)
            asa = math.sin(t * 17.0 + m["fase"]) * (9 * esc)
            env = round(14 * esc)
            cor_corpo = (10, 8, 14) if m["distante"] else (18, 14, 24)

            asa_esq = [
                (sx, sy),
                (sx - env // 2, round(sy - 5 * esc + asa * 0.4)),
                (sx - env, round(sy + asa)),
                (sx - env // 2, round(sy + 3 * esc)),
            ]
            asa_dir = [
                (sx, sy),
                (sx + env // 2, round(sy - 5 * esc + asa * 0.4)),
                (sx + env, round(sy + asa)),
                (sx + env // 2, round(sy + 3 * esc)),
            ]
            pygame.draw.polygon(tela, cor_corpo, asa_esq)
            pygame.draw.polygon(tela, cor_corpo, asa_dir)

            pygame.draw.ellipse(tela, cor_corpo, (sx - round(3 * esc), sy - round(3 * esc), round(6 * esc), round(7 * esc)))
            pygame.draw.polygon(tela, cor_corpo, [(sx - 2, sy - 2), (sx - 3, round(sy - 7 * esc)), (sx, sy - 3)])
            pygame.draw.polygon(tela, cor_corpo, [(sx + 2, sy - 2), (sx + 3, round(sy - 7 * esc)), (sx, sy - 3)])

            if not m["distante"]:
                pygame.draw.circle(tela, (255, 55, 45), (sx - 1, sy - 1), 1)
                pygame.draw.circle(tela, (255, 55, 45), (sx + 2, sy - 1), 1)

    def _desenhar_olhos_fundo(self, tela):
        """Desenha pares de olhos vermelhos piscando na escuridão entre as árvores."""
        t = pygame.time.get_ticks() * 0.001
        for olho in self.olhos_fundo:
            sx = round(olho["x"] - self.camera.x * olho["parallax"])
            sy = round(olho["y"] - self.camera.y * 0.35 + math.sin(t * 1.6 + olho["fase"]) * 2)
            if sx < -20 or sx > config.LARGURA + 20:
                continue

            ciclo = math.sin(t * olho["vel_piscar"] + olho["fase"])
            if ciclo < -0.55:
                continue

            esp = olho["espaco"]
            r = olho["raio"]
            for ox in (sx - esp, sx + esp):
                pygame.draw.circle(tela, (190, 18, 24), (ox, sy), r)
                if ciclo > 0.25 and r >= 3:
                    pygame.draw.circle(tela, (255, 110, 95), (ox, sy), 1)

    def _desenhar_vagalumes(self, tela):
        t = pygame.time.get_ticks() * 0.001
        for vg in self.vagalumes:
            wx = vg["x"] + math.sin(t * vg["vel"] + vg["fase"]) * vg["amp_x"]
            wy = vg["y"] + math.cos(t * (vg["vel"] * 0.8) + vg["fase"]) * vg["amp_y"]
            sx = round(wx - self.camera.x)
            sy = round(wy - self.camera.y)
            if sx < -15 or sx > config.LARGURA + 15:
                continue
            pulso = 0.5 + 0.5 * math.sin(t * 3.5 + vg["fase"] * 2.0)
            if pulso > 0.35:
                pygame.draw.circle(tela, (95, 175, 75), (sx, sy), 2)
                if pulso > 0.78:
                    pygame.draw.circle(tela, (205, 245, 165), (sx, sy), 1)

    def _desenhar_selo_portal(self, tela):
        """Desenha correntes sombrias sobre o portal enquanto o chefe estiver vivo."""
        if not self.saida or self._chefe_ativo() is None:
            return
        r = self.camera.aplicar(self.saida.rect)
        if r.right < -30 or r.left > config.LARGURA + 30:
            return
        selo = pygame.Surface((r.width + 16, r.height + 16), pygame.SRCALPHA)
        selo.fill((140, 15, 25, 85))
        tela.blit(selo, (r.x - 8, r.y - 8))
        pygame.draw.rect(tela, (215, 35, 45), r.inflate(8, 8), 2, border_radius=6)
        pygame.draw.line(tela, (190, 40, 50), (r.left - 4, r.top + 8), (r.right + 4, r.bottom - 8), 4)
        pygame.draw.line(tela, (190, 40, 50), (r.right + 4, r.top + 8), (r.left - 4, r.bottom - 8), 4)
        pygame.draw.circle(tela, (255, 65, 65), r.center, 8)
        pygame.draw.circle(tela, (40, 8, 12), r.center, 4)

    def _desenhar_iluminacao(self, tela):
        progresso = min(1.0, max(0.0, self.jogador.rect.centerx / max(1, self.largura)))
        alpha_trevas = int(230 + progresso * 15)

        escuridao = pygame.Surface((config.LARGURA, config.ALTURA), pygame.SRCALPHA)
        escuridao.fill((1, 2, 3, alpha_trevas))

        def abrir_luz(centro_tela, raio, intensidade_max=alpha_trevas):
            for passo in range(6, 0, -1):
                r = int(raio * (passo / 6))
                alpha = int(intensidade_max * (1 - (passo - 1) / 6))
                pygame.draw.circle(escuridao, (0, 0, 0, alpha), centro_tela, r)

        abrir_luz(self._posicao_lua(), 145, int(alpha_trevas * 0.72))

        for tocha in self.tochas:
            pos_tela = self.camera.aplicar(tocha.rect).center
            if -250 <= pos_tela[0] <= config.LARGURA + 250:
                abrir_luz(pos_tela, int(tocha.raio_luz() * 0.88), alpha_trevas)

        for orbe in self.orbes_cura:
            pos_orbe = self.camera.aplicar(orbe.rect).center
            if -120 <= pos_orbe[0] <= config.LARGURA + 120:
                abrir_luz(pos_orbe, 72, int(alpha_trevas * 0.85))

        pos_jog = self.camera.aplicar(self.jogador.rect).center
        raio_base = int(94 - progresso * 16)
        raio_jog = 185 if self.jogador.atacando else raio_base
        abrir_luz(pos_jog, raio_jog, int(alpha_trevas * 0.92))

        if self.saida:
            pos_saida = self.camera.aplicar(self.saida.rect).center
            if -200 <= pos_saida[0] <= config.LARGURA + 200:
                abrir_luz(pos_saida, 125, int(alpha_trevas * 0.82))

        tela.blit(escuridao, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        nevoa1 = pygame.Surface((config.LARGURA, 115), pygame.SRCALPHA)
        nevoa1.fill((12, 20, 19, 52))
        tela.blit(nevoa1, (0, config.ALTURA - 175))

        nevoa2 = pygame.Surface((config.LARGURA, 65), pygame.SRCALPHA)
        nevoa2.fill((16, 26, 24, 44))
        tela.blit(nevoa2, (0, config.ALTURA - 115))

        self._desenhar_olhos_fundo(tela)
        self._desenhar_morcegos(tela, apenas_distantes=False)
        self._desenhar_vagalumes(tela)

        for inimigo in self.inimigos:
            if hasattr(inimigo, "desenhar_olhos_brilhantes"):
                inimigo.desenhar_olhos_brilhantes(tela, self.camera)

    def _desenhar_barra_chefe(self, tela):
        chefe = self._chefe_ativo()
        if chefe is None:
            return
        if abs(chefe.rect.centerx - self.jogador.rect.centerx) > 760:
            return

        larg = 440
        alt = 16
        bx = (config.LARGURA - larg) // 2
        by = config.ALTURA - 42

        titulo = self.fonte.render(chefe.nome, True, (235, 85, 85))
        sombra = self.fonte.render(chefe.nome, True, (0, 0, 0))
        tpos = titulo.get_rect(center=(config.LARGURA // 2, by - 14))
        tela.blit(sombra, tpos.move(2, 2))
        tela.blit(titulo, tpos)

        pygame.draw.rect(tela, (18, 12, 16), (bx - 3, by - 3, larg + 6, alt + 6), border_radius=5)
        pygame.draw.rect(tela, (120, 30, 35), (bx - 3, by - 3, larg + 6, alt + 6), 2, border_radius=5)
        proporcao = max(0.0, chefe.vida / chefe.vida_max)
        pygame.draw.rect(tela, (185, 28, 38), (bx, by, int(larg * proporcao), alt), border_radius=3)

    def desenhar(self, tela):
        cam_orig = (self.camera.x, self.camera.y)
        if self.shake_tempo > 0 and self.shake_forca > 0:
            self.camera.x += random.randint(-self.shake_forca, self.shake_forca)
            self.camera.y += random.randint(-self.shake_forca, self.shake_forca)

        try:
            tela.fill(FUNDOS.get(self.numero, (25, 20, 30)))

            if self.numero == 3:
                self._desenhar_fundo_floresta(tela)

            for lap in self.lapides:
                lap.desenhar(tela, self.camera)
            for tocha in self.tochas:
                tocha.desenhar(tela, self.camera)

            if self.numero == 3:
                self._desenhar_solo_floresta(tela)
            else:
                for p in self.plataformas:
                    p.desenhar(tela, self.camera)

            for cipo in self.cipos:
                cipo.desenhar(tela, self.camera)
            for tronco in self.troncos:
                tronco.desenhar(tela, self.camera)
            for esp in self.espinhos:
                esp.desenhar(tela, self.camera)
            for vinha in self.vinhas:
                vinha.desenhar(tela, self.camera)
            for arm in self.armadilhas:
                arm.desenhar(tela, self.camera)
            for b in self.barreiras:
                b.desenhar(tela, self.camera)
            if self.saida:
                self.saida.desenhar(tela, self.camera)
                self._desenhar_selo_portal(tela)
            for r in self.reliquias:
                r.desenhar(tela, self.camera)
            for orbe in self.orbes_cura:
                orbe.desenhar(tela, self.camera)
            for inimigo in self.inimigos:
                inimigo.desenhar(tela, self.camera)
            for onda in self.ondas_sombrias:
                onda.desenhar(tela, self.camera)
            for proj in self.projeteis:
                proj.desenhar(tela, self.camera)
            for part in self.particulas:
                part.desenhar(tela, self.camera)
            self.jogador.desenhar(tela, self.camera)

            if self.numero == 3:
                self._desenhar_iluminacao(tela)
        finally:
            self.camera.x, self.camera.y = cam_orig

        self.hud.desenhar(tela, self.jogador)
        self._desenhar_barra_chefe(tela)

        acao = "atirar (12)" if self.numero == 3 else "atacar"
        ajuda = f"Fase {self.numero} | A-D: andar | W/ESPAÇO: pular/escalar | J/X: {acao} | ESC: menu"
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