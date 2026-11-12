import pygame
import config
from nucleo.cena import Cena
from nucleo.camera import Camera
from entidades.jogador import Jogador
from entidades.inimigos_comuns import GuerreiroCorrompido
from entidades.reliquia import Reliquia
from entidades.barreira import Barreira
from entidades.saida import Saida
from sistemas.mapa import carregar_mapa, existe_fase
from sistemas.hud import Hud

FUNDOS = {1: (25, 20, 30), 2: (18, 26, 38)}


class Fase(Cena):
    def __init__(self, jogo, numero=1):
        super().__init__(jogo)
        self.numero = numero
        self.fonte = pygame.font.Font(None, 28)
        self.fonte_msg = pygame.font.Font(None, 40)
        self.fonte_msg2 = pygame.font.Font(None, 28)

        dados = carregar_mapa(numero)
        self.largura, self.altura = dados.largura, dados.altura
        self.plataformas = dados.plataformas
        self.barreiras = [Barreira(*b) for b in dados.barreiras]
        self.solidos = self.plataformas + self.barreiras      # tudo em que se pode bater
        self.saida = Saida(*dados.saida) if dados.saida else None
        self.inimigos = [GuerreiroCorrompido(x, y) for x, y in dados.inimigos]
        # relíquias já conquistadas não aparecem de novo
        self.reliquias = [Reliquia(t, x, y) for t, x, y in dados.reliquias
                          if t not in jogo.habilidades]

        x, y = dados.inicio
        self.jogador = Jogador(x - Jogador.LARGURA // 2, y - Jogador.ALTURA)
        for habilidade in jogo.habilidades:
            self.jogador.desbloquear(habilidade)

        self.camera = Camera(self.largura, self.altura)
        self.camera.centralizar(self.jogador.rect)
        self.hud = Hud()
        self.mensagem = None
        self.tempo_mensagem = 0.0
        self.dicas = set()

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
                    self.jogador.atacar()
                elif e.key in (pygame.K_k, pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.jogador.avancar()

    # ---------- lógica ----------
    def atualizar(self, dt):
        self.jogador.atualizar(dt, self.solidos, self.largura)
        for inimigo in self.inimigos:
            inimigo.atualizar(dt, self.solidos)
        for reliquia in self.reliquias:
            reliquia.atualizar(dt)
        self.tempo_mensagem = max(0.0, self.tempo_mensagem - dt)

        self._combate()
        self._interacoes()
        self.inimigos = [i for i in self.inimigos if i.vivo]
        self.camera.seguir(self.jogador.rect, dt)

        # caiu em um buraco: perde 1 de vida e renasce no início
        if self.jogador.rect.top > self.altura + 200:
            self.jogador.vida -= 1
            if self.jogador.vida > 0:
                self.jogador.reiniciar()
                self.camera.centralizar(self.jogador.rect)

        if self.jogador.vida <= 0:
            from cenas.game_over import GameOver
            self.jogo.trocar_cena(GameOver(self.jogo, self.numero))

    def _combate(self):
        # golpe do Dáron acerta inimigos (no máximo 1 vez por inimigo em cada golpe)
        area = self.jogador.hitbox_ataque
        if area:
            for inimigo in self.inimigos:
                if id(inimigo) not in self.jogador.alvos_acertados and area.colliderect(inimigo.rect):
                    inimigo.receber_dano(config.DANO_ATAQUE, self.jogador.rect.centerx)
                    self.jogador.alvos_acertados.add(id(inimigo))

        # encostar em um inimigo vivo machuca o Dáron
        for inimigo in self.inimigos:
            if inimigo.vivo and self.jogador.rect.colliderect(inimigo.rect):
                self.jogador.receber_dano(inimigo.dano, inimigo.rect.centerx)

    def _interacoes(self):
        # relíquias
        for reliquia in self.reliquias:
            if self.jogador.rect.colliderect(reliquia.rect):
                reliquia.coletada = True
                self.jogador.desbloquear(reliquia.tipo)
                self.jogo.habilidades.add(reliquia.tipo)
                self.mensagem = reliquia.textos
                self.tempo_mensagem = 5.0
        self.reliquias = [r for r in self.reliquias if not r.coletada]

        # o avanço quebra barreiras (alcança um pouco além do corpo do Dáron)
        if self.jogador.avancando:
            zona = self.jogador.rect.inflate(72, 0)
            for barreira in list(self.barreiras):
                if zona.colliderect(barreira.rect):
                    self.barreiras.remove(barreira)
                    self.solidos.remove(barreira)

        # dica (uma vez) quando o Dáron chega perto de uma parede rachada
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

        # portal de saída
        if self.saida and self.jogador.rect.colliderect(self.saida.rect):
            self._proxima_fase()

    def _proxima_fase(self):
        if existe_fase(self.numero + 1):
            self.jogo.trocar_cena(Fase(self.jogo, self.numero + 1))
        else:
            from cenas.final import Final
            self.jogo.trocar_cena(Final(self.jogo))

    # ---------- desenho ----------
    def desenhar(self, tela):
        tela.fill(FUNDOS.get(self.numero, (25, 20, 30)))
        for p in self.plataformas:
            p.desenhar(tela, self.camera)
        for b in self.barreiras:
            b.desenhar(tela, self.camera)
        if self.saida:
            self.saida.desenhar(tela, self.camera)
        for r in self.reliquias:
            r.desenhar(tela, self.camera)
        for inimigo in self.inimigos:
            inimigo.desenhar(tela, self.camera)
        self.jogador.desenhar(tela, self.camera)
        self.hud.desenhar(tela, self.jogador)

        ajuda = f"Fase {self.numero} | A-D: andar | ESPAÇO: pular | J/X: atacar | ESC: menu"
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
