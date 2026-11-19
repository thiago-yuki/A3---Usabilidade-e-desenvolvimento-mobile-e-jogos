import pygame
import config
from nucleo.cena import Cena


class GameOver(Cena):
    def __init__(self, jogo, numero):
        super().__init__(jogo)
        self.numero = numero
        self.fonte_titulo = pygame.font.Font(None, 78)
        self.fonte_sub = pygame.font.Font(None, 38)
        self.fonte_texto = pygame.font.Font(None, 34)

    def eventos(self, eventos):
        for e in eventos:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    from cenas.fase import Fase
                    self.jogo.trocar_cena(Fase(self.jogo, self.numero))
                elif e.key == pygame.K_ESCAPE:
                    from cenas.menu import Menu
                    self.jogo.trocar_cena(Menu(self.jogo))

    def desenhar(self, tela):
        tela.fill(config.PRETO)
        self._centralizar(tela, "O seu medo venceu...", self.fonte_titulo, config.VERMELHO, 175)
        self._centralizar(tela, f"Você caiu na Fase {self.numero}", self.fonte_sub, config.DOURADO, 245)
        self._centralizar(tela, f"ENTER - Tentar a Fase {self.numero} de novo", self.fonte_texto, config.BRANCO, 325)
        self._centralizar(tela, "ESC - Menu", self.fonte_texto, config.CINZA, 375)

    def _centralizar(self, tela, texto, fonte, cor, y):
        img = fonte.render(texto, True, cor)
        tela.blit(img, img.get_rect(center=(config.LARGURA // 2, y)))