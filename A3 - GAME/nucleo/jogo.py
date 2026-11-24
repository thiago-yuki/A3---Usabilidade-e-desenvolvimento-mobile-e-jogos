import logging
import os

import pygame
import config

_LOGGER = logging.getLogger(__name__)
_MUSICAS_FASES = {
    1: "Fase1.mp3",
    2: "Fase2.wav",
    3: "Fase3.mp3",
    4: "Fase4.mp3",
}


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
        self._musicas_indisponiveis = set()
        self._efeitos_indisponiveis = set()
        self._musica_atual = None
        self._efeitos_audio = {}

    def iniciar_musica_menu(self):
        self._iniciar_musica("Intro.mp3")

    def iniciar_musica_fase(self, numero):
        arquivo = _MUSICAS_FASES.get(numero)
        if arquivo is None:
            self.parar_musica()
            return
        self._iniciar_musica(arquivo)

    def iniciar_musica_final(self):
        self._iniciar_musica("final.mp3")

    def _iniciar_musica(self, arquivo):
        if arquivo in self._musicas_indisponiveis:
            return

        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho = os.path.join(raiz, "audio", arquivo)
        if not os.path.isfile(caminho):
            raise FileNotFoundError(f"Trilha não encontrada: {caminho}")

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            if self._musica_atual == caminho and pygame.mixer.music.get_busy():
                return

            self.parar_efeitos()
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)
            self._musica_atual = caminho
        except (pygame.error, OSError) as erro:
            self._musica_atual = None
            self._musicas_indisponiveis.add(arquivo)
            _LOGGER.warning("Trilha '%s' desativada: %s", arquivo, erro)

    def tocar_efeito(self, arquivo, volume=1.0):
        if arquivo in self._efeitos_indisponiveis:
            return

        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho = os.path.join(raiz, "audio", arquivo)
        if not os.path.isfile(caminho):
            raise FileNotFoundError(f"Efeito sonoro não encontrado: {caminho}")

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            som = self._efeitos_audio.get(arquivo)
            if som is None:
                som = pygame.mixer.Sound(caminho)
                self._efeitos_audio[arquivo] = som
            som.set_volume(max(0.0, min(1.0, volume)))
            som.play()
        except (pygame.error, OSError) as erro:
            self._efeitos_indisponiveis.add(arquivo)
            _LOGGER.warning("Efeito sonoro '%s' desativado: %s", arquivo, erro)

    def parar_efeitos(self):
        if pygame.mixer.get_init():
            pygame.mixer.stop()

    def parar_musica(self):
        self.parar_efeitos()
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self._musica_atual = None

    def trocar_cena(self, nova_cena):
        self.cena = nova_cena

    def sair(self):
        self.parar_musica()
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
