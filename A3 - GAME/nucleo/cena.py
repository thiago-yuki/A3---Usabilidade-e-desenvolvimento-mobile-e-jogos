class Cena:
    """Classe base. Toda tela do jogo (menu, fase, game over...) herda desta."""

    def __init__(self, jogo):
        self.jogo = jogo

    def eventos(self, eventos):
        """Recebe a lista de eventos do pygame (teclado, mouse...)."""
        pass

    def atualizar(self, dt):
        """Lógica do jogo. dt = segundos desde o último frame."""
        pass

    def desenhar(self, tela):
        """Desenha tudo na tela."""
        pass
