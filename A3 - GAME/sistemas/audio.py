"""Opcional audio for the final battle."""
import logging
import os

import pygame


_LOGGER = logging.getLogger(__name__)
_EXTENSOES = (".wav", ".ogg", ".mp3")


class Audio:
    def __init__(self):
        self.ativo = False
        self.sons = {}
        self._avisos = set()
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.pasta_sons = os.path.join(raiz, "sons")

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error as erro:
            self._avisar("mixer", f"Audio da batalha desativado: {erro}")
            return

        self.ativo = True

    def _avisar(self, chave, mensagem):
        if chave not in self._avisos:
            _LOGGER.warning(mensagem)
            self._avisos.add(chave)

    def _arquivo(self, nome):
        for extensao in _EXTENSOES:
            caminho = os.path.join(self.pasta_sons, nome + extensao)
            if os.path.isfile(caminho):
                return caminho
        return None

    def pre_carregar(self, nomes):
        if not self.ativo:
            return

        ausentes = []
        for nome in nomes:
            caminho = self._arquivo(nome)
            if caminho is None:
                ausentes.append(nome)
                continue
            try:
                self.sons[nome] = pygame.mixer.Sound(caminho)
            except (pygame.error, OSError) as erro:
                self._avisar(nome, f"Nao foi possivel carregar o som '{nome}': {erro}")

        if ausentes:
            self._avisar(
                "sons-ausentes",
                "Sons opcionais da batalha nao encontrados em 'sons/': "
                + ", ".join(ausentes),
            )

    def tocar(self, nome, volume=1.0):
        som = self.sons.get(nome)
        if self.ativo and som is not None:
            som.set_volume(max(0.0, min(1.0, volume)))
            som.play()

    def musica(self, nome):
        if not self.ativo:
            return
        caminho = self._arquivo(nome)
        if caminho is None:
            self._avisar(nome, f"Musica opcional '{nome}' nao encontrada em 'sons/'.")
            return
        try:
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.play(-1)
        except (pygame.error, OSError) as erro:
            self._avisar(nome, f"Nao foi possivel iniciar a musica '{nome}': {erro}")

    def parar_musica(self):
        if self.ativo:
            pygame.mixer.music.stop()
