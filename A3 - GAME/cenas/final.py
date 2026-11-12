import pygame
import config
from nucleo.cena import Cena


class Final(Cena):
    """Provisória: aparece quando não existe a próxima fase. Vira o final de verdade depois."""

    def __init__(self, jogo):
        super().__init__(jogo)
        self.fonte_titulo = pygame.font.Font(None, 72)
        self.fonte_texto = pygame.font.Font(None, 34)

    def eventos(self, eventos):
        for e in eventos:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                from cenas.menu import Menu
                self.jogo.trocar_cena(Menu(self.jogo))

    def desenhar(self, tela):
        tela.fill(config.PRETO)
        self._centralizar(tela, "O Trono das Sombras aguarda...", self.fonte_titulo, config.DOURADO, 200)
        self._centralizar(tela, "Fim da demo por enquanto", self.fonte_texto, config.BRANCO, 300)
        self._centralizar(tela, "ENTER - Voltar ao menu", self.fonte_texto, config.CINZA, 360)

    def _centralizar(self, tela, texto, fonte, cor, y):
        img = fonte.render(texto, True, cor)
        tela.blit(img, img.get_rect(center=(config.LARGURA // 2, y)))
