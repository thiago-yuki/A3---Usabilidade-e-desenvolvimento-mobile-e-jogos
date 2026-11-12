import pygame
import config
from nucleo.cena import Cena


class GameOver(Cena):
    def __init__(self, jogo, numero):
        super().__init__(jogo)
        self.numero = numero
        self.fonte_titulo = pygame.font.Font(None, 80)
        self.fonte_texto = pygame.font.Font(None, 36)

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
        self._centralizar(tela, "A chama se apagou...", self.fonte_titulo, config.VERMELHO, 190)
        self._centralizar(tela, "ENTER - Tentar de novo", self.fonte_texto, config.BRANCO, 320)
        self._centralizar(tela, "ESC - Menu", self.fonte_texto, config.CINZA, 370)

    def _centralizar(self, tela, texto, fonte, cor, y):
        img = fonte.render(texto, True, cor)
        tela.blit(img, img.get_rect(center=(config.LARGURA // 2, y)))
