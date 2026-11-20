import math
import os
import random
import pygame
import config
from nucleo.cena import Cena
from nucleo.camera import Camera
from entidades.jogador import Jogador, JogadorPlasma
from entidades.inimigos_comuns import (
    GuerreiroCorrompido,
    ZumbiTsunami,
    ZumbiAnciao,
    GuardiaoFloresta,
    Fantasma,
    MonstroPalido
)
from entidades.obstaculos import OrbeChama
from entidades.projetil import ProjetilPlasma, ParticulaPlasma
from entidades.reliquia import Reliquia
from entidades.barreira import Barreira
from entidades.saida import Saida
from entidades.tocha import Tocha
from sistemas.mapa import carregar_mapa, existe_fase
from sistemas.hud import Hud
from sistemas.sons import Sons

FUNDOS = {1: (25, 20, 30), 2: (10, 14, 24), 3: (2, 4, 6)}


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
        eh_fase_2 = (numero == 2)
        eh_fase_3 = (numero == 3)

        nomes_fundos = {
            1: "fundo_fase1.png",
            2: "fundo_fase2.jpeg",
            3: "fundo_fase3.jpeg",
        }
        raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_fundo = os.path.join(
            raiz_projeto, "assets", nomes_fundos[numero]
        )
        self.imagem_fundo = pygame.transform.smoothscale(
            pygame.image.load(caminho_fundo).convert(),
            (config.LARGURA, config.ALTURA),
        )

        self.habilidades_entrada = set(jogo.habilidades)
        self.fonte = pygame.font.Font(None, 28)
        self.fonte_msg = pygame.font.Font(None, 40)
        self.fonte_msg2 = pygame.font.Font(None, 28)
        self.fonte_combo = pygame.font.Font(None, 34)
        self.t = 0.0
        self.sons = Sons()
        self._trocando = False

        dados = carregar_mapa(numero)
        self.largura, self.altura = dados.largura, dados.altura
        self.plataformas = dados.plataformas
        self.barreiras = [Barreira(*b) for b in dados.barreiras]
        self.escadas = dados.escadas
        self.troncos = dados.troncos
        self.espinhos = dados.espinhos
        self.vinhas = dados.vinhas
        self.cipos = dados.cipos
        self.armadilhas = dados.armadilhas
        self.lapides = dados.lapides
        self.solidos = self.plataformas + self.barreiras + self.troncos
        self.saida = Saida(*dados.saida) if dados.saida else None
        if self.saida:
            self.saida.design_fase1 = (numero == 1)
        if self.saida and eh_fase_2:
            self.saida.bizarro = True

        self.tochas = [Tocha(x, y) for x, y in dados.tochas]
        self.reliquias = [Reliquia(t, x, y) for t, x, y in dados.reliquias
                          if t not in jogo.habilidades]

        # ---------- jogador (criado uma única vez) ----------
        # Fase 2: JogadorPlasma (rifle de plasma, escada, dash hitkill).
        # Fase 3: Jogador em modo guerreira (calibre 12, cipós, parede).
        # Demais fases: Jogador com golpe corpo a corpo.
        x, y = dados.inicio
        if eh_fase_2:
            self.jogador = JogadorPlasma(x - JogadorPlasma.LARGURA // 2, y - JogadorPlasma.ALTURA)
            self.jogador.estilo = "guerreira"
            self.jogador.desbloquear("salto_duplo")
            self.jogador.desbloquear("avanco")
        else:
            self.jogador = Jogador(
                x - Jogador.LARGURA // 2,
                y - Jogador.ALTURA,
                modo_guerreira=eh_fase_3,
                aparencia_guerreira=(numero == 1),
            )
        for habilidade in jogo.habilidades:
            self.jogador.desbloquear(habilidade)

        # ---------- inimigos ----------
        self.chefe = None
        if eh_fase_2:
            self.inimigos = []
            for ix, iy in dados.inimigos:
                f = Fantasma(ix, iy - 28)
                f.alvo = self.jogador
                self.inimigos.append(f)
            pos_chefe = getattr(dados, "chefe", None)
            if pos_chefe:
                self.chefe = MonstroPalido(*pos_chefe)
                self.chefe.alvo = self.jogador
                self.inimigos.append(self.chefe)
        else:
            self.inimigos = [GuerreiroCorrompido(ix, iy) for ix, iy in dados.inimigos]
            self.inimigos += [ZumbiTsunami(ix, iy) for ix, iy in getattr(dados, "zumbis", [])]
            self.inimigos += [ZumbiAnciao(ix, iy) for ix, iy in getattr(dados, "zumbis_brutos", [])]
            self.inimigos += [GuardiaoFloresta(ix, iy) for ix, iy in getattr(dados, "chefes", [])]

        # ---------- listas de efeitos / objetos ----------
        self.projeteis = []
        self.ondas_sombrias = []
        self.particulas = []
        self.orbes_cura = []
        self.orbes_inimigos = []
        self.vagalumes = []
        self.morcegos = []
        self.olhos_fundo = []
        self.arvores_fundo = []
        self.arvores_medias = []
        self.arbustos_solo = []

        self.curas = [pygame.Rect(cx - 12, cy - 12, 24, 24) for cx, cy in dados.curas]
        self.powerups = [pygame.Rect(px - 14, py - 14, 28, 28) for px, py in dados.powerups]
        self.tempo_tiro_triplo = 0.0

        # Controle da horda dinâmica de zumbis na Fase 3
        self.zumbis_derrotados = 0
        self.zumbis_nascidos_extra = 0
        self.max_zumbis_extra = 38
        self.fila_spawns = []
        self.timer_pressao_horda = 4.0

        self.shake_tempo = 0.0
        self.shake_forca = 0
        self.aviso_portal_cooldown = 0.0

        # Hitstop, relâmpagos visuais e combo aéreo (Fase 2)
        self.hitstop = 0.0
        self.proximo_relampago = random.uniform(7.0, 12.0)
        self.flash_relampago = 0.0
        self.combo_dash = 0
        self.textos_flutuantes = []  # [x, y, texto, tempo, cor]

        # Corvos pousados nas lápides e cruzes do cemitério (Fase 2)
        self.corvos = []
        if eh_fase_2:
            chao_y = self.altura - (2 * config.TAMANHO_TILE)
            for wx in range(120, self.largura - 100, 280):
                self.corvos.append({
                    "x": float(wx + 15),
                    "y": float(chao_y - 44),
                    "vx": 0.0,
                    "vy": 0.0,
                    "voando": False,
                    "fase": random.uniform(0, math.tau),
                })
                if (wx // 280) % 2 == 0:
                    self.corvos.append({
                        "x": float(wx + 72),
                        "y": float(chao_y - 58),
                        "vx": 0.0,
                        "vy": 0.0,
                        "voando": False,
                        "fase": random.uniform(0, math.tau),
                    })

        self.esporos = [
            [random.uniform(0, self.largura), random.uniform(80, self.altura - 110),
             random.uniform(0.6, 2.0), random.uniform(0, math.tau)]
            for _ in range(45)
        ]

        self.almas = []
        self.luzes_cemiterio = []
        self.fantasmas_floresta = []
        self.macas_flutuantes = []
        self.esporos_verdes = []
        rng_visual = random.Random(505 + numero)
        limite_y_visual = min(480, self.altura - 40)
        if eh_fase_2:
            for _ in range(26):
                self.almas.append((
                    rng_visual.uniform(0, self.largura),
                    rng_visual.uniform(160, limite_y_visual),
                    rng_visual.uniform(0, math.tau),
                    rng_visual.uniform(0.6, 1.5),
                    rng_visual.randint(8, 15),
                ))
            for wx in range(380, self.largura, 650):
                self.luzes_cemiterio.append((
                    float(wx),
                    rng_visual.uniform(250, limite_y_visual),
                ))
        elif eh_fase_3:
            for _ in range(17):
                self.fantasmas_floresta.append((
                    rng_visual.uniform(0, self.largura),
                    rng_visual.uniform(160, limite_y_visual),
                    rng_visual.uniform(0, math.tau),
                    rng_visual.uniform(0.6, 1.7),
                    rng_visual.randint(9, 15),
                ))
            for _ in range(19):
                self.macas_flutuantes.append((
                    rng_visual.uniform(120, self.largura - 100),
                    rng_visual.uniform(160, limite_y_visual),
                    rng_visual.uniform(0, math.tau),
                    rng_visual.randint(8, 13),
                    rng_visual.choice(("vermelha", "verde")),
                ))
            for _ in range(42):
                self.esporos_verdes.append((
                    rng_visual.uniform(0, self.largura),
                    rng_visual.uniform(160, limite_y_visual),
                    rng_visual.uniform(0, math.tau),
                    rng_visual.uniform(0.6, 1.7),
                    rng_visual.randint(2, 4),
                ))

        self.camera = Camera(self.largura, self.altura)
        self.camera.centralizar(self.jogador.rect)
        self.hud = Hud()
        self.mensagem = None
        self.tempo_mensagem = 0.0
        self.dicas = set()

        if eh_fase_2:
            self.mensagem = (
                "Cemitério das Almas Pálidas",
                "Plasma (J/X) ou Dash Hitkill (K/SHIFT) para eliminar fantasmas e abrir o Portal Dimensional!"
            )
            self.tempo_mensagem = 4.5

        if eh_fase_3:
            self._gerar_floresta_sombria()
            self.mensagem = (
                "Fase 3 - As Profundezas da Floresta Sombria",
                "Os zumbis escalam atrás de você! Derrote a Abominação Derretida no final!",
            )
            self.tempo_mensagem = 4.5

    # ---------- utilidades ----------
    def _som(self, nome):
        """Os sons só existem na Fase 2; nas demais a chamada é ignorada."""
        if self.numero == 2:
            self.sons.tocar(nome)

    def _chefe_ativo(self):
        if self.chefe and self.chefe.vivo:
            return self.chefe
        for inimigo in self.inimigos:
            if getattr(inimigo, "eh_chefe", False) and inimigo.vivo:
                return inimigo
        return None

    def _tremer_camera(self, duracao, forca):
        self.shake_tempo = max(self.shake_tempo, duracao)
        self.shake_forca = max(self.shake_forca, forca)

    def _tremer(self, forca, duracao):
        """Tremor único para as duas fases (a Fase 2 usa o tremor da Camera; as demais, o da Fase)."""
        if self.numero == 2 and hasattr(self.camera, "tremer"):
            self.camera.tremer(forca, duracao)
        else:
            self._tremer_camera(duracao, forca)

    def _trepaveis(self):
        """Objetos que o jogador pode escalar: escadas na Fase 2; cipós/escadas nas demais."""
        if self.numero == 2:
            return self.escadas
        return list(self.cipos) + list(self.escadas)

    def _tocando_trepavel(self):
        return any(self.jogador.rect.colliderect(o.rect) for o in self._trepaveis())

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
            if e.type != pygame.KEYDOWN:
                continue
            if e.key == pygame.K_ESCAPE:
                from cenas.menu import Menu
                self.jogo.trocar_cena(Menu(self.jogo))
            elif e.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                # W/↑ perto de escada ou cipó serve para escalar, não para pular
                if e.key in (pygame.K_w, pygame.K_UP) and self._tocando_trepavel():
                    continue
                if self.jogador.pular() and self.numero == 2:
                    self.sons.tocar("pulo")
            elif e.key in (pygame.K_j, pygame.K_x):
                self._atirar()
            elif e.key in (pygame.K_k, pygame.K_LSHIFT, pygame.K_RSHIFT):
                if self.jogador.avancar() and self.numero == 2:
                    self.sons.tocar("dash")
                    self._tremer(3, 0.08)

    def _atirar(self):
        j = self.jogador
        d = j.direcao

        if self.numero == 2:
            # JogadorPlasma.atacar() devolve True/False; o projétil é criado aqui
            if not j.atacar():
                return
            self.sons.tocar("plasma")
            self._assustar_corvos(j.rect.centerx, raio=340)
            boca_x = j.rect.centerx + d * 34
            boca_y = j.rect.y + 31
            self.projeteis.append(ProjetilPlasma(boca_x, boca_y, d, vy=0))
            if self.tempo_tiro_triplo > 0:
                self.projeteis.append(ProjetilPlasma(boca_x, boca_y, d, vy=-135))
                self.projeteis.append(ProjetilPlasma(boca_x, boca_y, d, vy=135))
            for _ in range(5):
                self.particulas.append(ParticulaPlasma(boca_x, boca_y))
            return

        # Jogador.atacar() devolve uma lista de Tiro12 (modo guerreira) ou [] (golpe corpo a corpo)
        novos_tiros = j.atacar()
        if novos_tiros:
            self.projeteis.extend(novos_tiros)
            self._tremer_camera(0.11, 5)
            boca_x = j.rect.centerx + 30 * d
            boca_y = j.rect.centery + 3
            self._emitir_particulas(
                boca_x, boca_y, 7, (175, 180, 175),
                vel_x=(30 * d, 140 * d) if d > 0 else (140 * d, 30 * d),
                vel_y=(-45, 25), raio=4, vida=0.45, grav=-25.0
            )
            self.particulas.append(Particula(
                j.rect.centerx, boca_y - 2,
                -d * random.uniform(55, 95), random.uniform(-170, -120),
                config.DOURADO, vida=0.65, gravidade=480.0, eh_cartucho=True
            ))

    def _assustar_corvos(self, origem_x, raio=190):
        for corvo in self.corvos:
            if not corvo["voando"] and abs(corvo["x"] - origem_x) < raio:
                corvo["voando"] = True
                lado = 1 if corvo["x"] >= origem_x else -1
                corvo["vx"] = lado * random.uniform(95, 165)
                corvo["vy"] = -random.uniform(130, 210)

    # ---------- horda da Fase 3 ----------
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

    # ---------- lógica ----------
    def _atualizar_inimigos(self, dt):
        novos_fantasmas = []
        fantasmas_vivos = sum(1 for i in self.inimigos if isinstance(i, Fantasma) and i.vivo)

        for inimigo in self.inimigos:
            if isinstance(inimigo, MonstroPalido):
                inimigo.fantasmas_ativos_arena = fantasmas_vivos
                inimigo.atualizar(dt, self.solidos)
                if inimigo.fantasmas_invocados:
                    novos_fantasmas.extend(inimigo.fantasmas_invocados)
                    inimigo.fantasmas_invocados.clear()
                    self._som("invocar")
                    self._tremer(5, 0.16)
                if inimigo.orbes_lancados:
                    self.orbes_inimigos.extend(inimigo.orbes_lancados)
                    inimigo.orbes_lancados.clear()
            elif isinstance(inimigo, Fantasma):
                inimigo.atualizar(dt, self.solidos)
            elif isinstance(inimigo, (ZumbiTsunami, ZumbiAnciao, GuardiaoFloresta)):
                inimigo.atualizar(dt, self.solidos, self.jogador, self.cipos)
            else:
                inimigo.atualizar(dt, self.solidos, self.jogador)

            # Chefe da Fase 3 (ondas sombrias e tremor)
            ondas = getattr(inimigo, "ondas_pendentes", None)
            if ondas:
                self.ondas_sombrias.extend(ondas)
                ondas.clear()
            if getattr(inimigo, "tremor_pendente", False):
                inimigo.tremor_pendente = False
                self._tremer_camera(0.22, 8)

        if novos_fantasmas:
            self.inimigos.extend(novos_fantasmas)

    def _atualizar_projeteis(self, dt):
        for proj in self.projeteis:
            if isinstance(proj, ProjetilPlasma):
                proj.atualizar(dt, self.solidos, self.largura)
                if not proj.ativo:
                    for _ in range(8):
                        self.particulas.append(ParticulaPlasma(proj.pos.x, proj.pos.y))
            else:
                proj.atualizar(dt, self.solidos)
                if not proj.ativo and getattr(proj, "atingiu_parede", False):
                    self._emitir_particulas(
                        proj.pos.x, proj.pos.y, 4, (255, 210, 100),
                        vel_x=(-90, 90), vel_y=(-110, 40), raio=2, vida=0.22
                    )

    def atualizar(self, dt):
        self.t += dt

        # Hitstop (micro-congelamento dramático no impacto)
        if self.hitstop > 0:
            self.hitstop = max(0.0, self.hitstop - dt)
            self.camera.seguir(self.jogador.rect, dt)
            return

        # Clima de relâmpagos e corvos na Fase 2 (apenas visual)
        if self.numero == 2:
            self.flash_relampago = max(0.0, self.flash_relampago - dt * 5.5)
            self.proximo_relampago -= dt
            if self.proximo_relampago <= 0:
                self.proximo_relampago = random.uniform(11.0, 18.0)
                self.flash_relampago = 1.0

            self._assustar_corvos(self.jogador.rect.centerx, raio=175)
            for corvo in self.corvos:
                if corvo["voando"]:
                    corvo["x"] += corvo["vx"] * dt
                    corvo["y"] += corvo["vy"] * dt
                    corvo["vy"] -= 25 * dt  # ganha altitude suave

        self.tempo_tiro_triplo = max(0.0, self.tempo_tiro_triplo - dt)

        # Uma única atualização do jogador por frame
        self.jogador.atualizar(dt, self.solidos, self.largura, self._trepaveis())

        if self.jogador.no_chao:
            self.combo_dash = 0

        chefe_estava_vivo = bool(self.chefe and self.chefe.vivo)

        if self.saida:
            self.saida.selado = self._chefe_ativo() is not None
            self.saida.atualizar(dt)

        self._atualizar_inimigos(dt)

        for onda in self.ondas_sombrias:
            onda.atualizar(dt, self.solidos)
        self._atualizar_projeteis(dt)
        for arm in self.armadilhas:
            arm.atualizar(dt)
        for tocha in self.tochas:
            tocha.atualizar(dt)

        for orbe in self.orbes_inimigos:
            orbe.atualizar(dt, self.solidos)
            if orbe.ativo and orbe.rect.colliderect(self.jogador.rect):
                if self.jogador.receber_dano(orbe.dano, orbe.pos.x):
                    self._som("dano")
                    self._tremer(8, 0.22)
                orbe.ativo = False
        self.orbes_inimigos = [o for o in self.orbes_inimigos if o.ativo]

        for part in self.particulas:
            part.atualizar(dt)

        for tf in self.textos_flutuantes:
            tf[1] -= 38 * dt
            tf[3] -= dt
        self.textos_flutuantes = [tf for tf in self.textos_flutuantes if tf[3] > 0]

        for reliquia in self.reliquias:
            reliquia.atualizar(dt)
        for orbe in self.orbes_cura:
            orbe.atualizar(dt, self.solidos)

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

        # Feedback dramático quando o Monstro Pálido é derrotado
        if chefe_estava_vivo and self.chefe and not self.chefe.vivo:
            self.hitstop = 0.08
            self._tremer(13, 0.45)
            self._som("hitkill_fantasma")
            self.mensagem = ("Monstro Pálido Derrotado!", "Entre no Portal Dimensional Vermelho para avançar!")
            self.tempo_mensagem = 4.5

        self.camera.seguir(self.jogador.rect, dt)

        if self.jogador.rect.top > self.altura + 200:
            self.jogador.vida -= 1
            self._som("dano")
            self._tremer(8, 0.2)
            if self.jogador.vida > 0:
                self.jogador.reiniciar()
                self.camera.centralizar(self.jogador.rect)

        if self.jogador.vida <= 0:
            from cenas.game_over import GameOver
            self.jogo.habilidades = set(self.habilidades_entrada)
            self.jogo.trocar_cena(GameOver(self.jogo, self.numero))

    def _ao_derrotar_inimigo(self, inimigo):
        """Efeitos de morte para as fases com Jogador (1 e 3). A Fase 2 tem feedback próprio."""
        if self.numero == 2:
            return
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
        # Golpe corpo a corpo (Fase 1; nas fases 2 e 3 hitbox_ataque é None)
        area = self.jogador.hitbox_ataque
        if area:
            for inimigo in self.inimigos:
                if inimigo.vivo and id(inimigo) not in self.jogador.alvos_acertados and area.colliderect(inimigo.rect):
                    inimigo.receber_dano(config.DANO_ATAQUE, self.jogador.rect.centerx)
                    self.jogador.alvos_acertados.add(id(inimigo))
                    if not inimigo.vivo:
                        self._ao_derrotar_inimigo(inimigo)

        # Projéteis: plasma (Fase 2) e chumbinho calibre 12 (Fase 3)
        for proj in self.projeteis:
            if not proj.ativo:
                continue
            eh_plasma = isinstance(proj, ProjetilPlasma)
            for inimigo in self.inimigos:
                if not (inimigo.vivo and proj.rect.colliderect(inimigo.rect)):
                    continue
                if eh_plasma:
                    inimigo.receber_dano(proj.dano, proj.pos.x)
                    proj.ativo = False
                    if isinstance(inimigo, MonstroPalido):
                        self._tremer(4, 0.10)
                    for _ in range(14):
                        self.particulas.append(ParticulaPlasma(proj.pos.x, proj.pos.y))
                else:
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

        # Galhos com espinhos no chão (G)
        for esp in self.espinhos:
            if self.jogador.rect.colliderect(esp.rect):
                if self.jogador.receber_dano(1, esp.rect.centerx):
                    self._tremer_camera(0.14, 5)

        # Vinhas espinhosas suspensas (V)
        for vinha in self.vinhas:
            if self.jogador.rect.colliderect(vinha.rect):
                if self.jogador.receber_dano(1, vinha.rect.centerx):
                    self._tremer_camera(0.14, 5)

        # Armadilhas de caçador (M)
        for arm in self.armadilhas:
            if arm.fechada:
                continue
            if self.jogador.rect.colliderect(arm.rect):
                if self.jogador.receber_dano(1, arm.rect.centerx):
                    arm.acionar()
                    self._tremer_camera(0.16, 6)
                    self._emitir_particulas(arm.rect.centerx, arm.rect.top, 6, (210, 195, 160), raio=2, vida=0.25)

        # Contato com inimigos. Na Fase 2 o Dash mata Fantasmas com HITKILL e reseta a recarga.
        for inimigo in self.inimigos:
            if not inimigo.vivo:
                continue

            if self.numero == 2 and self.jogador.avancando and isinstance(inimigo, Fantasma):
                zona_dash = self.jogador.rect.inflate(26, 14)
                if zona_dash.colliderect(inimigo.rect):
                    inimigo.vivo = False
                    self.jogador.recarga_avanco = 0.0
                    self.jogador.pulos_restantes = self.jogador.pulos_maximos
                    self.combo_dash += 1
                    self.hitstop = 0.045
                    self._tremer(7, 0.16)
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
                    if self.numero == 2:
                        self.sons.tocar("dano")
                        self._tremer(9, 0.22)
                    else:
                        self._tremer_camera(0.16, 6)

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

        for cura in list(self.curas):
            if self.jogador.rect.colliderect(cura):
                self.curas.remove(cura)
                self.jogador.vida = min(self.jogador.vida_max, self.jogador.vida + 2)
                self._som("powerup")
                self.mensagem = ("Alma Restauradora!", "+2 pontos de vida recuperados")
                self.tempo_mensagem = 2.5

        for pw in list(self.powerups):
            if self.jogador.rect.colliderect(pw):
                self.powerups.remove(pw)
                self.tempo_tiro_triplo = 14.0
                self._som("powerup")
                self.mensagem = ("Sobrecarga de Plasma!", "Disparo triplo ativado por 14 segundos!")
                self.tempo_mensagem = 3.0

        if self.jogador.avancando:
            zona = self.jogador.rect.inflate(72, 0)
            for barreira in list(self.barreiras):
                if zona.colliderect(barreira.rect):
                    self.barreiras.remove(barreira)
                    if barreira in self.solidos:
                        self.solidos.remove(barreira)
                    self._som("hitkill_fantasma")
                    self._tremer(10, 0.24)
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

        # Portal dimensional na saída (selado enquanto houver chefe vivo)
        if self.saida and self.jogador.rect.colliderect(self.saida.rect):
            if self._chefe_ativo() is not None:
                if self.aviso_portal_cooldown <= 0:
                    if self.numero == 2:
                        self.mensagem = ("Fenda Dimensional Selada!", "Derrote o Monstro Pálido para atravessar o portal!")
                    else:
                        self.mensagem = (
                            "Portal Selado pelas Trevas!",
                            "Mate a Abominação Derretida para liberar a passagem!",
                        )
                    self.tempo_mensagem = 3.2
                    self.aviso_portal_cooldown = 2.5
            else:
                self._proxima_fase()

    def _proxima_fase(self):
        # Evita trocar de cena duas vezes no mesmo frame (2 -> 3 automaticamente)
        if self._trocando:
            return
        self._trocando = True
        if existe_fase(self.numero + 1):
            self.jogo.trocar_cena(Fase(self.jogo, self.numero + 1))
        else:
            from cenas.final import Final
            self.jogo.trocar_cena(Final(self.jogo))

    # ---------- desenho: Fase 3 (floresta) ----------
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
        """Desenha correntes sombrias sobre o portal enquanto o chefe da Fase 3 estiver vivo."""
        if self.numero == 2 or not self.saida or self._chefe_ativo() is None:
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
        if self.numero == 2:
            # Barra do Monstro Pálido (Fase 2)
            if self.chefe and self.chefe.vivo and abs(self.jogador.rect.centerx - self.chefe.rect.centerx) < 750:
                larg_barra = 420
                bx = config.LARGURA // 2 - larg_barra // 2
                by = 48
                nome = self.fonte.render("MONSTRO PÁLIDO - SENHOR DO CEMITÉRIO", True, (235, 225, 240))
                tela.blit(nome, nome.get_rect(center=(config.LARGURA // 2, by - 14)))
                pygame.draw.rect(tela, (25, 15, 25), (bx - 2, by - 2, larg_barra + 4, 16), border_radius=4)
                atual = int(larg_barra * max(0, self.chefe.vida) / self.chefe.vida_max)
                pygame.draw.rect(tela, (190, 35, 65), (bx, by, atual, 12), border_radius=3)
            return

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

    # ---------- desenho: Fase 2 (cemitério) ----------
    def _desenhar_fundo_cemiterio(self, tela, apenas_decoracoes=False):
        ox = getattr(self.camera, "offset_x", 0)
        oy = getattr(self.camera, "offset_y", 0)

        if not apenas_decoracoes:
            clarao = int(self.flash_relampago * 85)
            for y in range(0, config.ALTURA, 6):
                fator = y / config.ALTURA
                r = min(255, int(8 + 14 * fator) + clarao)
                g = min(255, int(12 + 20 * fator) + clarao)
                b = min(255, int(24 + 26 * fator) + int(clarao * 1.3))
                pygame.draw.rect(tela, (r, g, b), (0, y, config.LARGURA, 6))

            lua_x = int(760 - self.camera.x * 0.06) + ox
            lua_y = 115 + oy
            halo_lua = pygame.Surface((260, 260), pygame.SRCALPHA)
            pygame.draw.circle(halo_lua, (180, 200, 230, 18), (130, 130), 125)
            pygame.draw.circle(halo_lua, (210, 225, 245, 32), (130, 130), 85)
            tela.blit(halo_lua, (lua_x - 130, lua_y - 130))
            pygame.draw.circle(tela, (238, 240, 228), (lua_x, lua_y), 48)
            pygame.draw.circle(tela, (205, 208, 198), (lua_x - 14, lua_y - 10), 11)
            pygame.draw.circle(tela, (215, 218, 208), (lua_x + 12, lua_y + 14), 8)

            for i in range(-1, 6):
                cx = int(i * 340 - (self.camera.x * 0.18) % 340) + ox
                pts = [(cx - 80, config.ALTURA), (cx + 90, 270), (cx + 260, 320), (cx + 420, config.ALTURA)]
                pygame.draw.polygon(tela, (15, 20, 32), pts)

        chao_y = self.altura - (2 * config.TAMANHO_TILE)
        for wx in range(120, self.largura - 100, 280):
            sx = int(wx - self.camera.x) + ox
            sy = int(chao_y - self.camera.y) + oy
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

        # Corvos (pousados nas lápides/cruzes ou batendo asas no céu)
        for corvo in self.corvos:
            cx = int(corvo["x"] - self.camera.x) + ox
            cy = int(corvo["y"] - self.camera.y) + oy
            if -60 <= cx <= config.LARGURA + 60 and -60 <= cy <= config.ALTURA + 60:
                if corvo["voando"]:
                    asa = int(math.sin(self.t * 22 + corvo["fase"]) * 8)
                    pygame.draw.lines(tela, (12, 14, 20), False, [
                        (cx - 12, cy - asa), (cx - 4, cy), (cx, cy - 2), (cx + 4, cy), (cx + 12, cy - asa)
                    ], 3)
                    pygame.draw.circle(tela, (220, 45, 65), (cx + (3 if corvo["vx"] >= 0 else -3), cy - 2), 1)
                else:
                    pygame.draw.ellipse(tela, (14, 16, 22), (cx - 6, cy - 10, 12, 10))
                    pygame.draw.circle(tela, (14, 16, 22), (cx + 3, cy - 12), 4)
                    pygame.draw.polygon(tela, (70, 75, 85), [(cx + 6, cy - 13), (cx + 11, cy - 12), (cx + 6, cy - 10)])
                    pygame.draw.circle(tela, (220, 50, 70), (cx + 4, cy - 13), 1)

    def _desenhar_fantasmas_decorativos(self, tela, fantasmas, parallax_y):
        tempo = self.t
        camada = pygame.Surface((config.LARGURA, config.ALTURA), pygame.SRCALPHA)

        for mundo_x, mundo_y, fase, velocidade, tamanho in fantasmas:
            x = int(
                mundo_x - self.camera.x * 0.88
                + math.sin(tempo * 0.45 + fase) * 10
            )
            y = int(
                mundo_y - self.camera.y * parallax_y
                + math.sin(tempo * velocidade + fase) * 13
            )
            if x < -35 or x > config.LARGURA + 35:
                continue

            alpha = int(90 + (math.sin(tempo * 2 + fase) + 1) * 32)
            pygame.draw.circle(camada, (159, 191, 194, 24), (x, y), tamanho + 10)
            pygame.draw.circle(
                camada, (183, 211, 228, alpha), (x, y - tamanho // 2), tamanho // 2
            )
            pygame.draw.ellipse(
                camada,
                (155, 190, 210, alpha),
                (x - tamanho // 2, y - tamanho // 2, tamanho, tamanho),
            )
            pygame.draw.polygon(
                camada,
                (145, 183, 207, alpha),
                [
                    (x - tamanho // 2, y),
                    (x - tamanho // 3, y + tamanho),
                    (x, y + tamanho // 2),
                    (x + tamanho // 3, y + tamanho),
                    (x + tamanho // 2, y),
                ],
            )

        tela.blit(camada, (0, 0))

    def _desenhar_decoracoes_floresta(self, tela):
        tempo = self.t
        camada = pygame.Surface((config.LARGURA, config.ALTURA), pygame.SRCALPHA)

        for mundo_x, mundo_y, fase, tamanho, tipo in self.macas_flutuantes:
            x = int(
                mundo_x - self.camera.x * 0.86
                + math.sin(tempo * 0.6 + fase) * 7
            )
            y = int(
                mundo_y - self.camera.y * 0.20
                + math.sin(tempo * 1.3 + fase) * 12
            )
            if x < -30 or x > config.LARGURA + 30:
                continue

            cor = (174, 47, 48, 225) if tipo == "vermelha" else (101, 164, 54, 225)
            pygame.draw.circle(camada, (113, 205, 63, 30), (x, y), tamanho + 12)
            pygame.draw.circle(camada, cor, (x - 4, y), tamanho)
            pygame.draw.circle(camada, cor, (x + 4, y), tamanho)
            pygame.draw.ellipse(camada, cor, (x - tamanho, y - 2, tamanho * 2, tamanho + 7))
            pygame.draw.line(
                camada, (71, 51, 31, 255), (x, y - tamanho + 2), (x + 2, y - tamanho - 5), 2
            )
            pygame.draw.ellipse(
                camada, (91, 174, 60, 245), (x + 2, y - tamanho - 7, 9, 5)
            )

        for mundo_x, mundo_y, fase, velocidade, tamanho in self.esporos_verdes:
            x = int(mundo_x - self.camera.x * 0.76 + math.sin(tempo * 0.5 + fase) * 5)
            y = int(
                mundo_y - self.camera.y * 0.28
                + math.sin(tempo * velocidade + fase) * 13
            )
            if x < -10 or x > config.LARGURA + 10:
                continue

            pulsacao = (math.sin(tempo * 3 + fase) + 1) / 2
            alpha = int(85 + pulsacao * 105)
            pygame.draw.circle(camada, (111, 211, 82, 30), (x, y), tamanho + 6)
            pygame.draw.circle(camada, (151, 219, 97, alpha), (x, y), tamanho)

        tela.blit(camada, (0, 0))

    def _desenhar_luzes_cemiterio(self, tela):
        camada = pygame.Surface((config.LARGURA, config.ALTURA), pygame.SRCALPHA)
        for i, (mundo_x, mundo_y) in enumerate(self.luzes_cemiterio):
            x = int(mundo_x - self.camera.x)
            y = int(mundo_y - self.camera.y + math.sin(self.t * 1.7 + i) * 5)
            if x < -40 or x > config.LARGURA + 40:
                continue
            pygame.draw.circle(camada, (98, 177, 226, 45), (x, y), 27)
            pygame.draw.circle(camada, (220, 238, 247, 215), (x, y), 3)
        tela.blit(camada, (0, 0))

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
        ox = getattr(self.camera, "offset_x", 0)
        oy = getattr(self.camera, "offset_y", 0)

        desloc = int((self.t * 28) % 240)
        nevoa = pygame.Surface((config.LARGURA + 240, 95), pygame.SRCALPHA)
        for nx in range(0, config.LARGURA + 240, 120):
            pygame.draw.ellipse(nevoa, (130, 155, 175, 26), (nx - 40, 18, 220, 75))
        tela.blit(nevoa, (-desloc + ox, config.ALTURA - 85 + oy))

        for esp in self.esporos:
            ex = int((esp[0] + math.sin(self.t * esp[2] + esp[3]) * 18) - self.camera.x) + ox
            ey = int((esp[1] + math.cos(self.t * esp[2] * 0.8 + esp[3]) * 12) - self.camera.y) + oy
            if 0 <= ex <= config.LARGURA and 0 <= ey <= config.ALTURA:
                pygame.draw.circle(tela, (150, 230, 235), (ex, ey), 2)

    # ---------- desenho: cena ----------
    def _desenhar_efeitos_fase1(self, tela):
        nevoa = pygame.Surface((config.LARGURA, 110), pygame.SRCALPHA)
        deslocamento = int(self.t * 14 + self.camera.x * 0.12) % 320
        for i in range(5):
            x = (i * 250 - deslocamento) % (config.LARGURA + 280) - 140
            y = 30 + int(math.sin(self.t * 0.5 + i) * 12)
            pygame.draw.ellipse(
                nevoa,
                (157, 136, 190, 22),
                (x, y, 210, 45),
            )
        tela.blit(nevoa, (0, config.ALTURA - 112))

        particulas = pygame.Surface(
            (config.LARGURA, config.ALTURA), pygame.SRCALPHA
        )
        for mundo_x, mundo_y, velocidade, fase in self.esporos:
            x = int(mundo_x - self.camera.x * 0.8)
            y = int(
                mundo_y - self.camera.y * 0.35
                + math.sin(self.t * velocidade + fase) * 8
            )
            if -12 <= x <= config.LARGURA + 12 and 0 <= y <= config.ALTURA:
                pygame.draw.circle(particulas, (183, 151, 226, 75), (x, y), 3)
                pygame.draw.circle(particulas, (228, 213, 250, 170), (x, y), 1)
        tela.blit(particulas, (0, 0))

    def _desenhar_inimigo_fase1(self, tela, inimigo):
        r = self.camera.aplicar(inimigo.rect)
        if r.right < -30 or r.left > config.LARGURA + 30:
            return

        pulinho = int((math.sin(self.t * 7 + inimigo.rect.x) + 1) * 1.5)
        topo = r.y - pulinho
        cx = r.centerx
        corpo = (238, 238, 240) if inimigo.tempo_dano > 0 else (164, 49, 62)
        sombra = (120, 35, 48) if inimigo.tempo_dano <= 0 else (205, 205, 210)
        pygame.draw.ellipse(tela, (24, 19, 34), (r.x + 5, r.bottom - 5, r.width - 10, 8))
        pygame.draw.ellipse(tela, sombra, (r.x + 3, topo + 14, r.width - 6, r.height - 15))
        pygame.draw.ellipse(tela, corpo, (r.x + 5, topo + 10, r.width - 10, r.height - 17))

        olho_y = topo + 15
        for olho_x in (cx - 9, cx + 9):
            pygame.draw.circle(tela, (201, 88, 85), (olho_x, olho_y), 7)
            pygame.draw.circle(tela, (241, 220, 163), (olho_x, olho_y), 4)
            pupila_x = olho_x + inimigo.direcao
            pygame.draw.circle(tela, (35, 25, 30), (pupila_x, olho_y), 2)

        pygame.draw.ellipse(
            tela,
            (201, 93, 100) if inimigo.tempo_dano <= 0 else (245, 245, 245),
            (cx - 8, topo + 29, 16, 10),
        )
        pygame.draw.line(tela, (63, 23, 36), (cx - 8, topo + 27), (cx - 2, topo + 29), 2)
        pygame.draw.line(tela, (63, 23, 36), (cx + 8, topo + 27), (cx + 2, topo + 29), 2)

        if inimigo.vida < inimigo.vida_max:
            pygame.draw.rect(tela, (55, 20, 30), (r.x, topo - 7, r.width, 4))
            largura_vida = int(r.width * max(inimigo.vida, 0) / inimigo.vida_max)
            pygame.draw.rect(tela, config.VERMELHO, (r.x, topo - 7, largura_vida, 4))

    def _desenhar_mundo(self, tela):
        tela.blit(self.imagem_fundo, (0, 0))
        if self.numero == 1:
            self._desenhar_efeitos_fase1(tela)
        elif self.numero == 2:
            self._desenhar_fundo_cemiterio(tela, apenas_decoracoes=True)
            self._desenhar_fantasmas_decorativos(tela, self.almas, 0.30)
            self._desenhar_luzes_cemiterio(tela)
        elif self.numero == 3:
            self._desenhar_fantasmas_decorativos(
                tela, self.fantasmas_floresta, 0.25
            )
            self._desenhar_decoracoes_floresta(tela)

        for lap in self.lapides:
            lap.desenhar(tela, self.camera)
        for tocha in self.tochas:
            tocha.desenhar(tela, self.camera)

        if self.numero == 2:
            self._desenhar_plataformas_cemiterio(tela)
        elif self.numero == 3:
            self._desenhar_solo_floresta(tela)
        else:
            for p in self.plataformas:
                p.desenhar(tela, self.camera, tema=self.numero)

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
            b.desenhar(tela, self.camera, tema=self.numero)
        for escada in self.escadas:
            escada.desenhar(tela, self.camera)

        if self.saida:
            self.saida.desenhar(tela, self.camera)
            self._desenhar_selo_portal(tela)

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

        for orbe in self.orbes_cura:
            orbe.desenhar(tela, self.camera)
        for inimigo in self.inimigos:
            if self.numero == 1:
                self._desenhar_inimigo_fase1(tela, inimigo)
            else:
                inimigo.desenhar(tela, self.camera)
        for onda in self.ondas_sombrias:
            onda.desenhar(tela, self.camera)

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

    def desenhar(self, tela):
        # Tremor de tela da Fase (a câmera é restaurada ao fim do desenho do mundo)
        cam_orig = (self.camera.x, self.camera.y)
        if self.shake_tempo > 0 and self.shake_forca > 0:
            self.camera.x += random.randint(-self.shake_forca, self.shake_forca)
            self.camera.y += random.randint(-self.shake_forca, self.shake_forca)
        try:
            self._desenhar_mundo(tela)
        finally:
            self.camera.x, self.camera.y = cam_orig

        # ---------- interface (sem tremor) ----------
        self.hud.desenhar(tela, self.jogador, self.numero)
        self._desenhar_barra_chefe(tela)

        if self.tempo_tiro_triplo > 0:
            txt_pw = self.fonte.render(f"Plasma Triplo: {self.tempo_tiro_triplo:.1f}s", True, (80, 240, 255))
            tela.blit(txt_pw, (16, 120))

        if self.numero == 2:
            ajuda = f"Fase {self.numero} | A-D: andar | W/S: escada | ESPAÇO: pular | K/SHIFT: dash hitkill | J/X: plasma"
        elif self.numero == 3:
            ajuda = f"Fase {self.numero} | A-D: andar | W/S: escalar | ESPAÇO: pular | J/X: atirar | ESC: menu"
        else:
            ajuda = f"Fase {self.numero} | A-D: andar | ESPAÇO: pular | J/X: atacar | ESC: menu"
        self.hud.desenhar_comandos(tela, ajuda)

        if self.mensagem and self.tempo_mensagem > 0:
            titulo, descricao = self.mensagem
            for texto, fonte, cor, y in ((titulo, self.fonte_msg, config.DOURADO, 130),
                                         (descricao, self.fonte_msg2, config.BRANCO, 168)):
                sombra = fonte.render(texto, True, (0, 0, 0))
                img = fonte.render(texto, True, cor)
                pos = img.get_rect(center=(config.LARGURA // 2, y))
                tela.blit(sombra, pos.move(2, 2))
                tela.blit(img, pos)