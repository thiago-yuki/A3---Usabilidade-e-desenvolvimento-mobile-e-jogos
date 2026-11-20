import pygame
import config


class Jogo:
    """Cuida da janela, do loop principal e de qual cena está ativa."""

    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((config.LARGURA, config.ALTURA))
        pygame.display.set_caption(config.TITULO)
        self.relogio = pygame.time.Clock()
        self.rodando = True
        self.cena = None
        self.habilidades = set()  # relíquias conquistadas (valem para todas as fases)

    def trocar_cena(self, nova_cena):
        self.cena = nova_cena

    def sair(self):
        self.rodando = False

    def executar(self):
        while self.rodando:
            dt = self.relogio.tick(config.FPS) / 1000  # segundos
            dt = min(dt, 0.05)  # evita saltos enormes se o jogo travar

            eventos = pygame.event.get()
            for evento in eventos:
                if evento.type == pygame.QUIT:
                    self.sair()

            self.cena.eventos(eventos)
            self.cena.atualizar(dt)
            self.cena.desenhar(self.tela)
            pygame.display.flip()

        pygame.quit()
