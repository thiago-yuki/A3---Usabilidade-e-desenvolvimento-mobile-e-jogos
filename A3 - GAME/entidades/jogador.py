
import pygame
import os
import math
import config


class Jogador:
    """Guerreira protagonista do jogo."""

    LARGURA = 40
    ALTURA = 56

    def __init__(self, x, y):
        self.inicio = (x, y)

        # Retângulo original de colisão
        self.rect = pygame.Rect(
            x, y,
            self.LARGURA,
            self.ALTURA
        )

        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)

        self.no_chao = False
        self.direcao = 1

        # ==========================================
        # CARREGAMENTO DA GUERREIRA
        # ==========================================

        raiz_projeto = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        caminho_personagem = os.path.join(
            raiz_projeto,
            "assets",
            "guerreira.1.jfif"
        )

        if not os.path.exists(caminho_personagem):
            raise FileNotFoundError(
                "Imagem da guerreira não encontrada! "
                f"Verifique este caminho: {caminho_personagem}"
            )

        imagem_original = pygame.image.load(
            caminho_personagem
        ).convert_alpha()

        # Remove o fundo branco puro
        imagem_original.set_colorkey((255, 255, 255))

        # Recorta margens transparentes
        area_visivel = imagem_original.get_bounding_rect(
            min_alpha=1
        )

        if area_visivel.width > 0 and area_visivel.height > 0:
            imagem_original = imagem_original.subsurface(
                area_visivel
            ).copy()

        # ==========================================
        # TAMANHO VISUAL DA PERSONAGEM
        # ==========================================

        # Aumenta 8 pixels em relação ao tamanho original
        self.sprite_largura = self.LARGURA + 8
        self.sprite_altura = self.ALTURA + 8

        # Mantém a proporção original da imagem
        fator = min(
            self.sprite_largura / imagem_original.get_width(),
            self.sprite_altura / imagem_original.get_height()
        )

        nova_largura = max(
            1,
            round(imagem_original.get_width() * fator)
        )

        nova_altura = max(
            1,
            round(imagem_original.get_height() * fator)
        )

        imagem_redimensionada = pygame.transform.smoothscale(
            imagem_original,
            (nova_largura, nova_altura)
        )

        # Área transparente da personagem
        sprite_original = pygame.Surface(
            (self.sprite_largura, self.sprite_altura),
            pygame.SRCALPHA
        )

        # Alinha os pés da guerreira
        posicao_sprite = imagem_redimensionada.get_rect(
            midbottom=(
                self.sprite_largura // 2,
                self.sprite_altura
            )
        )

        sprite_original.blit(
            imagem_redimensionada,
            posicao_sprite
        )

        # A imagem original está virada para a esquerda
        self.sprite_esquerda = sprite_original

        # Espelha para criar a versão virada para a direita
        self.sprite_direita = pygame.transform.flip(
            self.sprite_esquerda,
            True,
            False
        )

        # ==========================================
        # PULO
        # ==========================================

        self.pulos_maximos = 1
        self.pulos_restantes = 1

        # ==========================================
        # HABILIDADES
        # ==========================================

        self.tem_salto_duplo = False
        self.tem_avanco = False

        self.tempo_avanco = 0.0
        self.recarga_avanco = 0.0

        # ==========================================
        # COMBATE E VIDA
        # ==========================================

        self.vida = config.VIDA_JOGADOR

        self.tempo_ataque = 0.0
        self.tempo_recarga = 0.0

        self.alvos_acertados = set()

        self.invencivel = 0.0
        self.recuo = 0.0

    # ==============================================
    # AÇÕES
    # ==============================================

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

        if (
            self.tem_avanco
            and self.recarga_avanco <= 0
            and self.recuo <= 0
        ):

            self.tempo_avanco = config.AVANCO_DURACAO
            self.recarga_avanco = config.AVANCO_RECARGA

            self.invencivel = max(
                self.invencivel,
                config.AVANCO_DURACAO
            )

    def atacar(self):

        if self.tempo_recarga <= 0:
            self.tempo_ataque = config.ATAQUE_DURACAO
            self.tempo_recarga = config.ATAQUE_RECARGA

            self.alvos_acertados.clear()

    def receber_dano(self, dano, origem_x):
        """Recebe dano e aplica o recuo, se não estiver invencível."""

        if self.invencivel > 0:
            return False

        self.vida -= dano
        self.invencivel = config.TEMPO_INVENCIVEL

        sentido = (
            1 if self.rect.centerx >= origem_x else -1
        )

        self.vel.x = sentido * config.RECUO_X
        self.vel.y = -config.RECUO_Y

        self.recuo = 0.2

        return True

    # ==============================================
    # ESTADOS DO JOGADOR
    # ==============================================

    @property
    def avancando(self):
        return self.tempo_avanco > 0

    @property
    def atacando(self):
        return self.tempo_ataque > 0

    @property
    def hitbox_ataque(self):
        """Área de ataque da personagem."""

        if not self.atacando:
            return None

        alcance = config.ATAQUE_ALCANCE
        altura = 40

        if self.direcao == 1:
            area = pygame.Rect(
                self.rect.right,
                0,
                alcance,
                altura
            )
        else:
            area = pygame.Rect(
                self.rect.left - alcance,
                0,
                alcance,
                altura
            )

        area.centery = self.rect.centery

        return area

    # ==============================================
    # ATUALIZAÇÃO E MOVIMENTAÇÃO
    # ==============================================

    def atualizar(self, dt, plataformas, largura_mundo):

        self.tempo_ataque = max(
            0.0, self.tempo_ataque - dt
        )

        self.tempo_recarga = max(
            0.0, self.tempo_recarga - dt
        )

        self.tempo_avanco = max(
            0.0, self.tempo_avanco - dt
        )

        self.recarga_avanco = max(
            0.0, self.recarga_avanco - dt
        )

        self.invencivel = max(
            0.0, self.invencivel - dt
        )

        # Movimento horizontal
        if self.avancando:

            self.vel.x = (
                self.direcao * config.AVANCO_VELOCIDADE
            )

            self.vel.y = 0

        elif self.recuo > 0:

            self.recuo -= dt

        else:

            teclas = pygame.key.get_pressed()
            direcao = 0

            if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
                direcao -= 1

            if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
                direcao += 1

            self.vel.x = (
                direcao * config.VELOCIDADE_JOGADOR
            )

            if direcao != 0:
                self.direcao = direcao

        # Gravidade
        if not self.avancando:

            self.vel.y = min(
                self.vel.y + config.GRAVIDADE * dt,
                config.VELOCIDADE_QUEDA_MAX
            )

        # Movimento no eixo X e colisões
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)

        for plataforma in plataformas:

            if self.rect.colliderect(plataforma.rect):

                if self.vel.x > 0:
                    self.rect.right = plataforma.rect.left

                elif self.vel.x < 0:
                    self.rect.left = plataforma.rect.right

                self.pos.x = self.rect.x

        # Movimento no eixo Y e colisões
        estava_no_chao = self.no_chao

        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)

        self.no_chao = False

        for plataforma in plataformas:

            if self.rect.colliderect(plataforma.rect):

                if self.vel.y > 0:
                    self.rect.bottom = plataforma.rect.top
                    self.no_chao = True

                elif self.vel.y < 0:
                    self.rect.top = plataforma.rect.bottom

                self.vel.y = 0
                self.pos.y = self.rect.y

        # Verifica o chão abaixo dos pés
        if not self.no_chao and self.vel.y >= 0:

            sonda = self.rect.move(0, 1)

            if any(
                sonda.colliderect(p.rect)
                for p in plataformas
            ):
                self.no_chao = True

        if self.no_chao:

            self.pulos_restantes = self.pulos_maximos

        elif estava_no_chao and self.vel.y >= 0:

            self.pulos_restantes = min(
                self.pulos_restantes,
                max(1, self.pulos_maximos - 1)
            )

        # Limites horizontais do mapa
        if self.rect.left < 0:

            self.rect.left = 0
            self.pos.x = self.rect.x

        if self.rect.right > largura_mundo:

            self.rect.right = largura_mundo
            self.pos.x = self.rect.x

    # ==============================================
    # ANIMAÇÃO PROCEDURAL DA GUERREIRA
    # ==============================================

    def _obter_sprite_animado(self):

        tempo = pygame.time.get_ticks() / 1000

        if self.direcao == 1:
            imagem = self.sprite_direita
        else:
            imagem = self.sprite_esquerda

        escala_x = 1.0
        escala_y = 1.0
        angulo = 0.0
        deslocamento_y = 0.0

        # AVANÇO
        if self.avancando:

            fase = tempo * 18

            escala_x = 1.06
            escala_y = 0.96

            angulo = -self.direcao * 5
            deslocamento_y = math.sin(fase) * 0.7

        # ATAQUE
        elif self.atacando:

            duracao = max(
                0.001,
                config.ATAQUE_DURACAO
            )

            progresso = max(
                0.0,
                min(
                    1.0,
                    1 - self.tempo_ataque / duracao
                )
            )

            impacto = math.sin(progresso * math.pi)

            escala_x = 1.0 + impacto * 0.035
            escala_y = 1.0 - impacto * 0.025

            angulo = -self.direcao * 6 * impacto

            deslocamento_y = -impacto * 1.2

        # PULO E QUEDA
        elif not self.no_chao:

            if self.vel.y < 0:
                angulo = self.direcao * 5
                escala_y = 0.98

            else:
                angulo = -self.direcao * 3
                escala_y = 1.015

        # CAMINHADA
        elif abs(self.vel.x) > 20:

            fase = tempo * 11
            passo = math.sin(fase)

            deslocamento_y = abs(passo) * 2.0

            angulo = -passo * self.direcao * 1.8

            escala_x = 1.0 + abs(passo) * 0.006
            escala_y = 1.0 - abs(passo) * 0.012

        # RESPIRAÇÃO QUANDO ESTÁ PARADA
        else:

            respiracao = math.sin(tempo * 2.3)

            escala_y = 1.0 + respiracao * 0.012
            escala_x = 1.0 - respiracao * 0.005

            angulo = math.sin(tempo * 1.15) * 0.6

            deslocamento_y = respiracao * 0.7

        # Redimensiona de acordo com o movimento
        nova_largura = max(
            1,
            round(self.sprite_largura * escala_x)
        )

        nova_altura = max(
            1,
            round(self.sprite_altura * escala_y)
        )

        imagem = pygame.transform.smoothscale(
            imagem,
            (nova_largura, nova_altura)
        )

        # Aplica inclinação
        if abs(angulo) > 0.1:

            imagem = pygame.transform.rotate(
                imagem,
                angulo
            )

        return imagem, deslocamento_y

    # ==============================================
    # EFEITO VISUAL DO ATAQUE
    # ==============================================

    def _desenhar_golpe(self, tela, camera):

        area = self.hitbox_ataque

        if not area:
            return

        area = camera.aplicar(area)

        centro_x = area.centerx
        centro_y = area.centery

        pontos = []

        for i in range(17):

            angulo = (
                -1.15
                + (i / 16) * 2.3
            )

            px = centro_x + (
                self.direcao * math.cos(angulo) * 23
            )

            py = centro_y + (
                math.sin(angulo) * 27
            )

            pontos.append((
                int(px),
                int(py)
            ))

        # Rastro roxo
        pygame.draw.lines(
            tela,
            (130, 85, 197),
            False,
            pontos,
            8
        )

        # Brilho dourado
        pygame.draw.lines(
            tela,
            (255, 220, 154),
            False,
            pontos,
            3
        )

        pygame.draw.circle(
            tela,
            (255, 237, 190),
            pontos[-1],
            3
        )

    # ==============================================
    # DESENHO DA GUERREIRA
    # ==============================================

    def desenhar(self, tela, camera):

        # Pisca quando está invencível
        if (
            self.invencivel > 0
            and not self.avancando
            and int(self.invencivel * 20) % 2 == 0
        ):
            return

        rect = camera.aplicar(self.rect)

        # Rastro do avanço
        if self.avancando:

            rastro = pygame.Surface(
                rect.size,
                pygame.SRCALPHA
            )

            rastro.fill((133, 74, 174, 95))

            tela.blit(
                rastro,
                (
                    rect.x - self.direcao * 26,
                    rect.y
                )
            )

        # Sprite animado
        imagem, deslocamento_y = self._obter_sprite_animado()

        # Alinha os pés com o chão
        posicao = imagem.get_rect(
            midbottom=(
                rect.centerx,
                rect.bottom - round(deslocamento_y)
            )
        )

        tela.blit(
            imagem,
            posicao
        )

        # Efeito do ataque
        if self.atacando:
            self._desenhar_golpe(tela, camera)

