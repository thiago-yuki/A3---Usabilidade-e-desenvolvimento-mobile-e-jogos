import array
import math
import random
import pygame


class Sons:
    """Efeitos sonoros sintetizados via código para a Fase 2."""

    def __init__(self):
        self.ativo = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.ativo = True
        except pygame.error:
            self.ativo = False
            return

        self.plasma = self._criar_som(freq_ini=980, freq_fim=260, duracao=0.11, volume=0.22, onda="quadrada")
        self.dash = self._criar_som(freq_ini=240, freq_fim=680, duracao=0.14, volume=0.25, onda="seno")
        self.hitkill_fantasma = self._criar_som(freq_ini=520, freq_fim=110, duracao=0.20, volume=0.30, onda="ruido")
        self.pulo = self._criar_som(freq_ini=260, freq_fim=490, duracao=0.09, volume=0.16, onda="seno")
        self.powerup = self._criar_som(freq_ini=440, freq_fim=880, duracao=0.25, volume=0.24, onda="seno")
        self.dano = self._criar_som(freq_ini=180, freq_fim=70, duracao=0.22, volume=0.32, onda="quadrada")
        self.invocar = self._criar_som(freq_ini=140, freq_fim=310, duracao=0.28, volume=0.20, onda="ruido")
        self.trovao = self._criar_som(freq_ini=95, freq_fim=38, duracao=0.55, volume=0.26, onda="ruido")
        self.portao = self._criar_som(freq_ini=120, freq_fim=55, duracao=0.35, volume=0.28, onda="quadrada")

    def _criar_som(self, freq_ini, freq_fim, duracao, volume=0.25, onda="seno"):
        taxa = 22050
        total = int(taxa * duracao)
        buf = array.array("h")
        fase = 0.0
        for i in range(total):
            prog = i / max(1, total)
            freq = freq_ini + (freq_fim - freq_ini) * prog
            fase += (2.0 * math.pi * freq) / taxa
            envelope = (1.0 - prog) ** 1.4

            if onda == "quadrada":
                val = 1.0 if math.sin(fase) >= 0 else -1.0
            elif onda == "ruido":
                val = math.sin(fase) * 0.5 + math.sin(fase * 3.7) * 0.3 + random.uniform(-0.35, 0.35)
            else:
                val = math.sin(fase)

            amostra = int(val * envelope * volume * 32767)
            buf.append(max(-32768, min(32767, amostra)))

        return pygame.mixer.Sound(buffer=buf)

    def tocar(self, nome):
        if not self.ativo:
            return
        som = getattr(self, nome, None)
        if som:
            som.play()