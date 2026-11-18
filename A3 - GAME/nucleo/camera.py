import random
import config


class Camera:
    """Decide qual pedaço do mundo aparece na tela, segue o jogador e aplica tremor."""

    def __init__(self, largura_mundo, altura_mundo):
        self.largura_mundo = largura_mundo
        self.altura_mundo = altura_mundo
        self.x = 0.0
        self.y = 0.0
        self.tempo_tremor = 0.0
        self.intensidade_tremor = 0.0
        self.offset_x = 0
        self.offset_y = 0

    def tremer(self, intensidade=8, duracao=0.18):
        self.intensidade_tremor = max(self.intensidade_tremor, intensidade)
        self.tempo_tremor = max(self.tempo_tremor, duracao)

    def _alvo(self, rect):
        x = rect.centerx - config.LARGURA / 2
        y = rect.centery - config.ALTURA / 2
        x = max(0, min(x, max(0, self.largura_mundo - config.LARGURA)))
        y = max(0, min(y, max(0, self.altura_mundo - config.ALTURA)))
        return x, y

    def centralizar(self, rect):
        self.x, self.y = self._alvo(rect)

    def seguir(self, rect, dt):
        alvo_x, alvo_y = self._alvo(rect)
        suavidade = min(1.0, 8 * dt)
        self.x += (alvo_x - self.x) * suavidade
        self.y += (alvo_y - self.y) * suavidade

        if self.tempo_tremor > 0:
            self.tempo_tremor = max(0.0, self.tempo_tremor - dt)
            mag = int(self.intensidade_tremor)
            self.offset_x = random.randint(-mag, mag)
            self.offset_y = random.randint(-mag, mag)
            if self.tempo_tremor <= 0:
                self.intensidade_tremor = 0.0
                self.offset_x = 0
                self.offset_y = 0
        else:
            self.offset_x = 0
            self.offset_y = 0

    def aplicar(self, rect):
        return rect.move(-round(self.x) + self.offset_x, -round(self.y) + self.offset_y)