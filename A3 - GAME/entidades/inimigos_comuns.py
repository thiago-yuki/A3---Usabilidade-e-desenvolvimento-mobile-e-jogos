from entidades.inimigo import Inimigo


class GuerreiroCorrompido(Inimigo):
    """Soldado possuído pelas sombras: patrulha devagar, 3 golpes para cair."""

    def __init__(self, x_centro, y_base):
        super().__init__(x_centro, y_base, largura=38, altura=52,
                         vida=3, dano=1, velocidade=90, cor=(110, 60, 150))
