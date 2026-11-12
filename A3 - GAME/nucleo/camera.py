import config


class Camera:
    """Decide qual pedaço do mundo aparece na tela e segue o jogador suavemente."""

    def __init__(self, largura_mundo, altura_mundo):
        self.largura_mundo = largura_mundo
        self.altura_mundo = altura_mundo
        self.x = 0.0
        self.y = 0.0

    def _alvo(self, rect):
        """Posição ideal da câmera (jogador no centro), sem sair dos limites do mapa."""
        x = rect.centerx - config.LARGURA / 2
        y = rect.centery - config.ALTURA / 2
        x = max(0, min(x, max(0, self.largura_mundo - config.LARGURA)))
        y = max(0, min(y, max(0, self.altura_mundo - config.ALTURA)))
        return x, y

    def centralizar(self, rect):
        """Pula direto para o alvo (usado ao começar a fase ou renascer)."""
        self.x, self.y = self._alvo(rect)

    def seguir(self, rect, dt):
        """Anda em direção ao alvo aos poucos, para o movimento ficar suave."""
        alvo_x, alvo_y = self._alvo(rect)
        suavidade = min(1.0, 8 * dt)
        self.x += (alvo_x - self.x) * suavidade
        self.y += (alvo_y - self.y) * suavidade

    def aplicar(self, rect):
        """Converte um retângulo do mundo para a posição na tela."""
        return rect.move(-round(self.x), -round(self.y))
