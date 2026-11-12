import pygame
import config
from nucleo.cena import Cena


class Menu(Cena):
    def __init__(self, jogo):
        super().__init__(jogo)
        self.fonte_titulo = pygame.font.Font(None, 72)
        self.fonte_texto = pygame.font.Font(None, 36)
        self.fonte_pequena = pygame.font.Font(None, 26)

    def _iniciar(self, numero):
        from cenas.fase import Fase
        self.jogo.habilidades.clear()   # novo jogo = sem relíquias
        self.jogo.trocar_cena(Fase(self.jogo, numero))

    def eventos(self, eventos):
        for e in eventos:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    self._iniciar(1)
                elif e.key == pygame.K_2:
                    self._iniciar(2)          # atalho para testar a fase 2
                elif e.key == pygame.K_ESCAPE:
                    self.jogo.sair()

    def desenhar(self, tela):
        tela.fill(config.PRETO)
        self._centralizar(tela, "A Última Chama de Esparta", self.fonte_titulo, config.DOURADO, 180)
        self._centralizar(tela, "ENTER - Jogar", self.fonte_texto, config.BRANCO, 320)
        self._centralizar(tela, "ESC - Sair", self.fonte_texto, config.CINZA, 370)
        self._centralizar(tela, "[2] atalho de teste: ir direto para a Fase 2", self.fonte_pequena, (90, 90, 100), 480)

    def _centralizar(self, tela, texto, fonte, cor, y):
        img = fonte.render(texto, True, cor)
        tela.blit(img, img.get_rect(center=(config.LARGURA // 2, y)))
