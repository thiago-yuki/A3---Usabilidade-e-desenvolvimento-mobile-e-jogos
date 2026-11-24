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
from entidades.dragao_vermelho import DragaoVermelho, VIDAS as VIDAS_DRAGAO, TIROS_POR_VIDA
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


class PedacoOrgao:
    """Pedaço visceral (coração, olho, costela, carne) lançado na explosão do chefe da Fase 2."""

    def __init__(self, x, y, vx, vy, tipo):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.tipo = tipo  # "coracao", "olho", "costela", "carne"
        self.angulo = random.uniform(0, math.tau)
        self.vel_ang = random.uniform(-11.0, 11.0)
        self.vida = random.uniform(2.6, 3.8)
        self.rastro_timer = 0.0

    def atualizar(self, dt, solidos, particulas):
        self.vida -= dt
        self.vy += 680.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angulo += self.vel_ang * dt

        # Rastro de sangue enquanto voa
        self.rastro_timer -= dt
        if self.rastro_timer <= 0 and abs(self.vy) + abs(self.vx) > 90:
            self.rastro_timer = 0.045
            particulas.append(Particula(
                self.x, self.y,
                random.uniform(-25, 25), random.uniform(-20, 20),
                (165, 18, 32), raio=3, vida=0.45, gravidade=260.0
            ))

        # Colisão e quique no chão
        rect = pygame.Rect(round(self.x) - 6, round(self.y) - 6, 12, 12)
        for s in solidos:
            if rect.colliderect(s.rect):
                if self.vy > 0 and self.y - self.vy * dt <= s.rect.top + 8:
                    self.y = float(s.rect.top - 6)
                    self.vy = -self.vy * 0.42
                    self.vx *= 0.68
                    self.vel_ang *= 0.55
                    if abs(self.vy) < 45:
                        self.vy = 0.0
                        self.vx *= 0.4
                        self.vel_ang = 0.0
                else:
                    self.vx = -self.vx * 0.5
                break

    def desenhar(self, tela, camera):
        if self.vida <= 0:
            return
        sx = round(self.x - camera.x)
        sy = round(self.y - camera.y)
        if sx < -40 or sx > config.LARGURA + 40:
            return

        if self.tipo == "coracao":
            pygame.draw.circle(tela, (150, 18, 36), (sx - 3, sy - 2), 6)
            pygame.draw.circle(tela, (175, 24, 44), (sx + 3, sy - 2), 6)
            pygame.draw.polygon(tela, (135, 14, 30), [(sx - 8, sy), (sx + 8, sy), (sx, sy + 9)])
            pygame.draw.line(tela, (215, 70, 85), (sx - 2, sy - 7), (sx - 4, sy - 12), 2)
        elif self.tipo == "olho":
            pygame.draw.circle(tela, (235, 232, 225), (sx, sy), 7)
            pygame.draw.circle(tela, (190, 25, 35), (sx + 2, sy), 3)
            pygame.draw.circle(tela, (15, 10, 15), (sx + 2, sy), 1)
            pygame.draw.line(tela, (165, 22, 34), (sx - 6, sy), (sx - 13, sy + 3), 2)
        elif self.tipo == "costela":
            dx = round(math.cos(self.angulo) * 9)
            dy = round(math.sin(self.angulo) * 9)
            pygame.draw.line(tela, (225, 218, 198), (sx - dx, sy - dy), (sx + dx, sy + dy), 4)
            pygame.draw.circle(tela, (160, 22, 34), (sx - dx, sy - dy), 3)
        else:  # carne / víscera
            pygame.draw.ellipse(tela, (138, 22, 36), (sx - 8, sy - 5, 16, 10))
            pygame.draw.ellipse(tela, (185, 48, 62), (sx - 5, sy - 3, 9, 5))


class GosmaDerretida:
    """Animação de derretimento do chefe da Fase 3 como uma poça de gosma tóxica."""

    def __init__(self, x, bottom_y, largura):
        self.x = float(x)
        self.bottom_y = float(bottom_y)
        self.largura_ini = float(largura)
        self.altura_ini = 92.0
        self.t = 0.0
        self.duracao = 2.8
        self.ativo = True
        self.bolhas = [
            [random.uniform(-0.42, 0.42), random.uniform(0, math.tau), random.uniform(3.5, 6.5)]
            for _ in range(9)
        ]

    def atualizar(self, dt, particulas):
        self.t += dt
        if self.t >= self.duracao:
            self.ativo = False
            return

        prog = min(1.0, self.t / (self.duracao * 0.72))
        larg_atual = self.largura_ini * (1.0 + prog * 1.45)

        if random.random() < 0.35:
            gx = self.x + random.uniform(-larg_atual * 0.45, larg_atual * 0.45)
            particulas.append(Particula(
                gx, self.bottom_y - 6,
                random.uniform(-35, 35), random.uniform(-95, -35),
                (118, 195, 48), raio=3, vida=0.45, gravidade=220.0
            ))

    def desenhar(self, tela, camera):
        if not self.ativo:
            return
        prog = min(1.0, self.t / (self.duracao * 0.72))
        fade = 1.0 if self.t < self.duracao * 0.72 else max(0.0, 1.0 - (self.t - self.duracao * 0.72) / (self.duracao * 0.28))

        larg = round(self.largura_ini * (1.0 + prog * 1.45))
        alt = max(10, round(self.altura_ini * (1.0 - prog * 0.88)))

        sx = round(self.x - camera.x)
        sy = round(self.bottom_y - camera.y)
        if sx + larg < -60 or sx - larg > config.LARGURA + 60:
            return

        surf = pygame.Surface((larg + 40, alt + 24), pygame.SRCALPHA)
        cx = (larg + 40) // 2
        base_y = alt + 16
        alpha = int(235 * fade)

        # Poça espalhada na base
        pygame.draw.ellipse(surf, (48, 86, 24, alpha), (10, base_y - 12, larg + 20, 18))
        pygame.draw.ellipse(surf, (84, 146, 36, alpha), (18, base_y - 10, larg + 4, 13))

        # Corpo central escorrendo e derretendo
        if alt > 12:
            topo_w = max(16, int(larg * (0.62 - prog * 0.35)))
            corpo = [
                (cx - larg // 2, base_y - 4),
                (cx - topo_w // 2, base_y - alt),
                (cx + topo_w // 2, base_y - alt),
                (cx + larg // 2, base_y - 4),
            ]
            pygame.draw.polygon(surf, (66, 118, 30, alpha), corpo)
            pygame.draw.ellipse(surf, (108, 178, 44, alpha), (cx - topo_w // 2, base_y - alt - 5, topo_w, 12))

        # Bolhas ácidas estourando na gosma
        for desloc_x, fase, r_max in self.bolhas:
            bx = cx + int(desloc_x * larg)
            pulso = (math.sin(self.t * 6.0 + fase) + 1.0) * 0.5
            r = max(2, int(r_max * pulso))
            by = base_y - 6 - int(pulso * min(12, alt * 0.45))
            pygame.draw.circle(surf, (148, 224, 62, alpha), (bx, by), r)
            pygame.draw.circle(surf, (210, 250, 140, alpha), (bx - 1, by - 1), max(1, r // 2))

        tela.blit(surf, (sx - cx, sy - base_y))


class Fase(Cena):
    def __init__(self, jogo, numero=1):
        super().__init__(jogo)
        self.numero = numero
        eh_fase_2 = (numero == 2)
        eh_fase_3 = (numero == 3)
        eh_fase_4 = (numero == 4)   # fase final: tela estática (câmera parada)

        nomes_fundos = {
            1: "fundo_fase1.png",
            2: "fundo_fase2.jpeg",
            3: "fundo_fase3.jpeg",
            4: "fundofase4.jpeg",
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
        self.timer_passo = 0.0
        self._trocando = False
        self.contagem_epilogo = None   # Fase 4: segundos até a tela 5 (depois que o dragão foge)

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

        # ---------- jogador ----------
        x, y = dados.inicio
        if eh_fase_2:
            self.jogador = JogadorPlasma(x - JogadorPlasma.LARGURA // 2, y - JogadorPlasma.ALTURA)
            self.jogador.estilo = "guerreira"
        else:
            arma = "besta" if eh_fase_3 else "espingarda"
            self.jogador = Jogador(
                x - Jogador.LARGURA // 2,
                y - Jogador.ALTURA,
                modo_arma=arma,
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
            for ix, iy in getattr(dados, "chefes", []):
                guardiao = GuardiaoFloresta(ix, iy)
                self.inimigos.append(guardiao)
                if self.chefe is None:
                    self.chefe = guardiao
            if eh_fase_4:   # Fase 4: o chefe 'C' do mapa é o Dragão Vermelho
                self.inimigos = [DragaoVermelho(ix, iy) for ix, iy in getattr(dados, "chefes", [])]
                self.chefe = self.inimigos[0] if self.inimigos else None

        # ---------- listas de efeitos / objetos ----------
        self.projeteis = []
        self.ondas_sombrias = []
        self.particulas = []
        self.pedacos_orgaos = []
        self.gosmas_derretidas = []
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

        self.zumbis_derrotados = 0
        self.zumbis_nascidos_extra = 0
        self.max_zumbis_extra = 38
        self.fila_spawns = []
        self.timer_pressao_horda = 4.0

        self.shake_tempo = 0.0
        self.shake_forca = 0
        self.aviso_portal_cooldown = 0.0

        self.hitstop = 0.0
        self.proximo_relampago = random.uniform(7.0, 12.0)
        self.flash_relampago = 0.0
        self.combo_dash = 0
        self.dash_acertados = set()
        self.textos_flutuantes = []

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

        self.camera = Camera(self.largura, self.altura)
        self.camera.centralizar(self.jogador.rect)
        if eh_fase_4:
            self._fixar_camera()
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

        if eh_fase_4:
            self.mensagem = (
                "Fase 4 - O Castelo das Três Maldições",
                "Derrote o Dragão Vermelho, guardião do castelo! (J/X atira, ESPAÇO pula)",
            )
            self.tempo_mensagem = 4.5

        if eh_fase_3:
            self._gerar_floresta_sombria()
            self.mensagem = (
                "Fase 3 - As Profundezas da Floresta Sombria",
                "Use sua Besta de 3 Virotes (J/X) e Dash Hitkill! Derrote a Abominação Derretida no final!",
            )
            self.tempo_mensagem = 4.5
        self.jogo.iniciar_musica_fase(self.numero)

    # ---------- utilidades ----------
    def _fixar_camera(self):
        """Fase 4 é uma tela só: a câmera não segue o jogador (o chão fica na parte de baixo)."""
        self.camera.x = 0.0
        self.camera.y = float(max(0, self.altura - config.ALTURA))

    def _atualizar_camera(self, dt):
        if self.numero == 4:
            self._fixar_camera()
        else:
            self.camera.seguir(self.jogador.rect, dt)

    def _som(self, nome):
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
        if self.numero == 2 and hasattr(self.camera, "tremer"):
            self.camera.tremer(forca, duracao)
        else:
            self._tremer_camera(duracao, forca)

    def _trepaveis(self):
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

    def _explodir_orgaos_chefe(self, chefe):
        cx, cy = chefe.rect.centerx, chefe.rect.centery
        tipos = ["coracao", "olho", "olho", "costela", "costela", "costela", "carne", "carne", "carne", "carne", "carne", "carne"]
        for tipo in tipos:
            vx = random.uniform(-340, 340)
            if abs(vx) < 70:
                vx = 110 if vx >= 0 else -110
            vy = random.uniform(-420, -140)
            self.pedacos_orgaos.append(PedacoOrgao(
                cx + random.randint(-14, 14),
                cy + random.randint(-16, 10),
                vx, vy, tipo
            ))
        self._emitir_particulas(
            cx, cy, 48, (165, 18, 32),
            vel_x=(-260, 260), vel_y=(-300, -40), raio=5, vida=0.85, grav=420.0
        )

    def _derreter_chefe_gosma(self, chefe):
        self.gosmas_derretidas.append(
            GosmaDerretida(chefe.rect.centerx, chefe.rect.bottom, chefe.rect.width)
        )
        self._emitir_particulas(
            chefe.rect.centerx, chefe.rect.centery, 36, (108, 178, 44),
            vel_x=(-200, 200), vel_y=(-190, -20), raio=5, vida=0.75, grav=320.0
        )

    def _gerar_floresta_sombria(self):
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
                if e.key in (pygame.K_w, pygame.K_UP) and self._tocando_trepavel():
                    continue
                if self.jogador.pular():
                    self._som("pulo")
            elif e.key in (pygame.K_j, pygame.K_x):
                self._atirar()
            elif e.key in (pygame.K_k, pygame.K_LSHIFT, pygame.K_RSHIFT):
                if self.jogador.avancar():
                    self.dash_acertados.clear()
                    self._tremer(3, 0.08)
                    self._som("dash")

    def _atirar(self):
        j = self.jogador
        d = j.direcao

        # Fase 2: Rifle de Plasma (som original mantido)
        if self.numero == 2:
            if not j.atacar():
                return
            self._som("plasma")
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

        # Fase 1 (Espingarda) e Fase 3 (Besta de 3 tiros)
        novos_tiros = j.atacar()
        if novos_tiros:
            self.projeteis.extend(novos_tiros)
            boca_x = j.rect.centerx + 30 * d
            boca_y = j.rect.centery + 3

            if j.modo_arma == "espingarda":
                self._som("espingarda")
                self._tremer_camera(0.11, 5)
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
            else:
                self._som("besta")
                self._tremer_camera(0.06, 2)
                self._emitir_particulas(
                    boca_x, boca_y, 4, (220, 235, 245),
                    vel_x=(40 * d, 120 * d) if d > 0 else (120 * d, 40 * d),
                    vel_y=(-35, 35), raio=2, vida=0.22, grav=0.0
                )

    def _assustar_corvos(self, origem_x, raio=190):
        for corvo in self.corvos:
            if not corvo["voando"] and abs(corvo["x"] - origem_x) < raio:
                corvo["voando"] = True
                lado = 1 if corvo["x"] >= origem_x else -1
                corvo["vx"] = lado * random.uniform(95, 165)
                corvo["vy"] = -random.uniform(130, 210)

    # ---------- horda da Fase 3 ----------
    def _encontrar_ponto_spawn_zumbi(self):
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

            ondas = getattr(inimigo, "ondas_pendentes", None)
            if ondas:
                self.ondas_sombrias.extend(ondas)
                ondas.clear()
            if getattr(inimigo, "tremor_pendente", False):
                inimigo.tremor_pendente = False
                self._tremer_camera(0.22, 8)
            if isinstance(inimigo, DragaoVermelho):
                self._eventos_dragao(inimigo)

        if novos_fantasmas:
            self.inimigos.extend(novos_fantasmas)

    def _eventos_dragao(self, dragao):
        """Sons, tremor e mensagens do Dragão Vermelho (Fase 4)."""
        for ev in dragao.eventos:
            if ev == "rugido":
                self._som("trovao")
                self._tremer_camera(0.5, 9)
            elif ev == "fogo":
                self._som("invocar")
            elif ev == "pouso":
                self._som("portao")
            elif ev == "vida":
                restantes = dragao.vidas_restantes
                self.mensagem = ("O Dragão perdeu uma vida!", f"Vidas restantes: {restantes} de {VIDAS_DRAGAO}")
                self.tempo_mensagem = 2.2
            elif ev == "derrotado":
                self.hitstop = 0.06
                self.ondas_sombrias.clear()
                self.mensagem = ("O Dragão Vermelho foi derrotado!", "Ele foge voando para longe...")
                self.tempo_mensagem = 4.0
            elif ev == "fugiu":
                self.mensagem = ("O caminho para o castelo está livre!", "")
                self.tempo_mensagem = 5.0
                self.contagem_epilogo = 3.5      # em seguida vai para a tela 5 (epílogo)
        dragao.eventos.clear()

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

        if self.contagem_epilogo is not None:
            self.contagem_epilogo -= dt
            if self.contagem_epilogo <= 0 and not self._trocando:
                self._trocando = True
                from cenas.epilogo import Epilogo
                self.jogo.trocar_cena(Epilogo(self.jogo))
                return

        if self.hitstop > 0:
            self.hitstop = max(0.0, self.hitstop - dt)
            self._atualizar_camera(dt)
            return

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
                    corvo["vy"] -= 25 * dt

        self.tempo_tiro_triplo = max(0.0, self.tempo_tiro_triplo - dt)

        self.jogador.atualizar(dt, self.solidos, self.largura, self._trepaveis())

        if self.numero == 4 and self.jogador.no_chao and abs(self.jogador.vel.x) > 10:
            self.timer_passo -= dt
            if self.timer_passo <= 0:
                self.timer_passo = 0.34
                self._som("passo")
        else:
            self.timer_passo = 0.0

        if self.jogador.no_chao:
            self.combo_dash = 0
        if not self.jogador.avancando:
            self.dash_acertados.clear()

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

        for orgao in self.pedacos_orgaos:
            orgao.atualizar(dt, self.solidos, self.particulas)
        self.pedacos_orgaos = [o for o in self.pedacos_orgaos if o.vida > 0]

        for gosma in self.gosmas_derretidas:
            gosma.atualizar(dt, self.particulas)
        self.gosmas_derretidas = [g for g in self.gosmas_derretidas if g.ativo]

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

        # Morte do chefe da Fase 2: explode jogando órgãos para os lados
        if chefe_estava_vivo and self.numero == 2 and self.chefe and not self.chefe.vivo:
            self.hitstop = 0.08
            self._tremer(13, 0.45)
            self._som("hitkill_fantasma")
            self._explodir_orgaos_chefe(self.chefe)
            self.mensagem = ("Monstro Pálido Derrotado!", "Entre no Portal Dimensional Vermelho para avançar!")
            self.tempo_mensagem = 4.5

        self._atualizar_camera(dt)

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
        if self.numero == 2:
            return
        eh_chefe = getattr(inimigo, "eh_chefe", False)
        if eh_chefe:
            # Chefe da Fase 3 derrete como uma gosma
            self._derreter_chefe_gosma(inimigo)
            self._tremer_camera(0.48, 10)
            self._som("hitkill_fantasma")
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
        else:
            self._emitir_particulas(
                inimigo.rect.centerx, inimigo.rect.centery, 14, (130, 22, 30),
                vel_x=(-230, 230), vel_y=(-270, -40), raio=4, vida=0.5
            )
            if self.numero == 3:
                self.zumbis_derrotados += 1
                if self.zumbis_nascidos_extra < self.max_zumbis_extra:
                    self.fila_spawns.append(random.uniform(1.1, 2.0))
                    if self.zumbis_derrotados % 2 == 0:
                        self.fila_spawns.append(random.uniform(2.1, 3.3))

        eh_anciao = isinstance(inimigo, ZumbiAnciao)
        if self.numero == 3 and (eh_chefe or eh_anciao or random.random() < 0.16):
            self.orbes_cura.append(OrbeChama(inimigo.rect.centerx, inimigo.rect.centery))

    def _combate(self):
        # Projéteis: espingarda (Fase 1), plasma (Fase 2) e besta de 3 virotes (Fase 3)
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
                    self._som("dano")
                    self._tremer_camera(0.18, 7)
                onda.ativo = False

        for esp in self.espinhos:
            if self.jogador.rect.colliderect(esp.rect):
                if self.jogador.receber_dano(1, esp.rect.centerx):
                    self._som("dano")
                    self._tremer_camera(0.14, 5)

        for vinha in self.vinhas:
            if self.jogador.rect.colliderect(vinha.rect):
                if self.jogador.receber_dano(1, vinha.rect.centerx):
                    self._som("dano")
                    self._tremer_camera(0.14, 5)

        for arm in self.armadilhas:
            if arm.fechada:
                continue
            if self.jogador.rect.colliderect(arm.rect):
                if self.jogador.receber_dano(1, arm.rect.centerx):
                    arm.acionar()
                    self._som("dano")
                    self._tremer_camera(0.16, 6)
                    self._emitir_particulas(arm.rect.centerx, arm.rect.top, 6, (210, 195, 160), raio=2, vida=0.25)

        # Dash Hitkill padronizado em TODAS as fases contra monstros comuns
        for inimigo in self.inimigos:
            if not inimigo.vivo:
                continue

            if self.jogador.avancando:
                zona_dash = self.jogador.rect.inflate(26, 14)
                if zona_dash.colliderect(inimigo.rect):
                    eh_chefe = isinstance(inimigo, (MonstroPalido, GuardiaoFloresta)) or getattr(inimigo, "eh_chefe", False)
                    if not eh_chefe:
                        inimigo.vivo = False
                        self.jogador.recarga_avanco = 0.0
                        self.jogador.pulos_restantes = self.jogador.pulos_maximos
                        self.combo_dash += 1
                        self.hitstop = 0.045
                        self._tremer(7, 0.16)
                        self._som("hitkill_fantasma")
                        self._ao_derrotar_inimigo(inimigo)

                        label = f"HITKILL {self.combo_dash}x!" if self.combo_dash > 1 else "HITKILL!"
                        self.textos_flutuantes.append([
                            inimigo.rect.centerx, inimigo.rect.top - 10, label, 0.9, (120, 255, 255)
                        ])
                        for _ in range(20):
                            self.particulas.append(
                                ParticulaPlasma(inimigo.rect.centerx, inimigo.rect.centery, (130, 255, 255))
                            )
                        continue
                    elif id(inimigo) not in self.dash_acertados:
                        self.dash_acertados.add(id(inimigo))
                        inimigo.receber_dano(2, self.jogador.rect.centerx)
                        self._tremer(6, 0.14)
                        if not inimigo.vivo:
                            self._ao_derrotar_inimigo(inimigo)
                        continue

            if self.jogador.rect.colliderect(inimigo.rect):
                if self.jogador.receber_dano(inimigo.dano, inimigo.rect.centerx):
                    self._som("dano")
                    if self.numero == 2:
                        self._tremer(9, 0.22)
                    else:
                        self._tremer_camera(0.16, 6)

    def _interacoes(self):
        for reliquia in self.reliquias:
            if self.jogador.rect.colliderect(reliquia.rect):
                reliquia.coletada = True
                self.jogador.desbloquear(reliquia.tipo)
                self.jogo.habilidades.add(reliquia.tipo)
                self._som("powerup")
                self.mensagem = reliquia.textos
                self.tempo_mensagem = 5.0
        self.reliquias = [r for r in self.reliquias if not r.coletada]

        for orbe in self.orbes_cura:
            if not orbe.coletado and self.jogador.rect.colliderect(orbe.rect):
                orbe.coletado = True
                self._som("powerup")
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

    def _desenhar_barra_chefe(self, tela):
        """Barra de vida padronizada entre o chefe da Fase 2 e o chefe da Fase 3."""
        chefe = self._chefe_ativo()
        if chefe is None:
            return
        if self.numero == 4:
            self._desenhar_barra_dragao(tela, chefe)
            return
        if abs(self.jogador.rect.centerx - chefe.rect.centerx) >= 750:
            return

        larg_barra = 420
        alt_barra = 16
        bx = config.LARGURA // 2 - larg_barra // 2
        by = 48

        if self.numero == 2:
            titulo_txt = "MONSTRO PÁLIDO - SENHOR DO CEMITÉRIO"
        else:
            nome_chefe = getattr(chefe, "nome", "ABOMINAÇÃO DERRETIDA").upper()
            titulo_txt = f"{nome_chefe} - SENHOR DA FLORESTA"

        nome = self.fonte.render(titulo_txt, True, (235, 225, 240))
        sombra = self.fonte.render(titulo_txt, True, (0, 0, 0))
        pos_nome = nome.get_rect(center=(config.LARGURA // 2, by - 14))
        tela.blit(sombra, pos_nome.move(2, 2))
        tela.blit(nome, pos_nome)

        pygame.draw.rect(tela, (25, 15, 25), (bx - 2, by - 2, larg_barra + 4, alt_barra), border_radius=4)
        atual = int(larg_barra * max(0, chefe.vida) / chefe.vida_max)
        pygame.draw.rect(tela, (190, 35, 65), (bx, by, atual, alt_barra - 4), border_radius=3)

    def _desenhar_barra_dragao(self, tela, dragao):
        """5 barras de vida lado a lado; cada tiro certeiro apaga 25% da barra atual."""
        larg_bar, alt_bar, espaco = 82, 14, 6
        total = VIDAS_DRAGAO * larg_bar + (VIDAS_DRAGAO - 1) * espaco
        x0 = config.LARGURA // 2 - total // 2
        y0 = 50

        titulo_txt = "DRAGÃO VERMELHO - GUARDIÃO DO CASTELO"
        nome = self.fonte.render(titulo_txt, True, (235, 225, 240))
        sombra = self.fonte.render(titulo_txt, True, (0, 0, 0))
        pos_nome = nome.get_rect(center=(config.LARGURA // 2, y0 - 16))
        tela.blit(sombra, pos_nome.move(2, 2))
        tela.blit(nome, pos_nome)

        for i in range(VIDAS_DRAGAO):
            bx = x0 + i * (larg_bar + espaco)
            restante = max(0, min(TIROS_POR_VIDA, dragao.golpes - i * TIROS_POR_VIDA))
            pygame.draw.rect(tela, (25, 15, 25), (bx - 2, y0 - 2, larg_bar + 4, alt_bar + 4), border_radius=4)
            if restante > 0:
                pygame.draw.rect(tela, (220, 60, 30), (bx, y0, larg_bar * restante // TIROS_POR_VIDA, alt_bar), border_radius=3)
            for q in range(1, TIROS_POR_VIDA):      # marcas de 25%
                pygame.draw.line(tela, (25, 15, 25), (bx + larg_bar * q // TIROS_POR_VIDA, y0),
                                 (bx + larg_bar * q // TIROS_POR_VIDA, y0 + alt_bar), 2)

    # ---------- desenho: Fase 2 (cemitério) ----------
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

        for cura in self.curas:
            rc = self.camera.aplicar(cura)
            pulso = int(math.sin(self.t * 6) * 3)
            pygame.draw.circle(tela, (60, 235, 140), rc.center, 10 + pulso)
            pygame.draw.circle(tela, (220, 255, 235), rc.center, 5)

        for pw in self.powerups:
            rp = self.camera.aplicar(pw)
            flutuar = int(math.sin(self.t * 5) * 4)
            cx, cy = rp.centerx, rp.centery + flutuar
            losango = [(cx, cy - 16), (cx + 12, cy), (cx, cy + 16), (cx - 12, cy)]
            pygame.draw.polygon(tela, (0, 220, 255), losango)
            pygame.draw.polygon(tela, config.BRANCO, losango, 2)

        for orbe in self.orbes_cura:
            orbe.desenhar(tela, self.camera)

        for gosma in self.gosmas_derretidas:
            gosma.desenhar(tela, self.camera)

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
        for orgao in self.pedacos_orgaos:
            orgao.desenhar(tela, self.camera)
        for part in self.particulas:
            part.desenhar(tela, self.camera)

        for tf in self.textos_flutuantes:
            pos = self.camera.aplicar(pygame.Rect(round(tf[0]), round(tf[1]), 1, 1)).topleft
            img = self.fonte_combo.render(tf[2], True, tf[4])
            tela.blit(img, img.get_rect(center=pos))

    def desenhar(self, tela):
        cam_orig = (self.camera.x, self.camera.y)
        if self.shake_tempo > 0 and self.shake_forca > 0:
            self.camera.x += random.randint(-self.shake_forca, self.shake_forca)
            self.camera.y += random.randint(-self.shake_forca, self.shake_forca)
        try:
            self._desenhar_mundo(tela)
        finally:
            self.camera.x, self.camera.y = cam_orig

        self.hud.desenhar(tela, self.jogador, self.numero)
        self._desenhar_barra_chefe(tela)

        if self.tempo_tiro_triplo > 0:
            txt_pw = self.fonte.render(f"Plasma Triplo: {self.tempo_tiro_triplo:.1f}s", True, (80, 240, 255))
            tela.blit(txt_pw, (16, 120))

        if self.numero == 2:
            ajuda = f"Fase {self.numero} | A-D: andar | W/S: escada | ESPAÇO: pular | K/SHIFT: dash hitkill | J/X: plasma"
        elif self.numero == 3:
            ajuda = f"Fase {self.numero} | A-D: andar | W/S: escalar | ESPAÇO: pular | K/SHIFT: dash hitkill | J/X: besta (3 tiros)"
        else:
            ajuda = f"Fase {self.numero} | A-D: andar | ESPAÇO: pular | K/SHIFT: dash hitkill | J/X: calibre 12"
        self.hud.desenhar_comandos(tela, ajuda)

        if self.contagem_epilogo is not None and self.contagem_epilogo < 1.2:   # escurece para a tela 5
            veu = pygame.Surface((config.LARGURA, config.ALTURA))
            veu.set_alpha(int(255 * (1.0 - max(0.0, self.contagem_epilogo) / 1.2)))
            tela.blit(veu, (0, 0))

        if self.mensagem and self.tempo_mensagem > 0:
            titulo, descricao = self.mensagem
            for texto, fonte, cor, y in ((titulo, self.fonte_msg, config.DOURADO, 130),
                                         (descricao, self.fonte_msg2, config.BRANCO, 168)):
                sombra = fonte.render(texto, True, (0, 0, 0))
                img = fonte.render(texto, True, cor)
                pos = img.get_rect(center=(config.LARGURA // 2, y))
                tela.blit(sombra, pos.move(2, 2))
                tela.blit(img, pos)