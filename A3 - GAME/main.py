from nucleo.jogo import Jogo
from cenas.menu import Menu

if __name__ == "__main__":
    jogo = Jogo()
    jogo.trocar_cena(Menu(jogo))
    jogo.executar()
