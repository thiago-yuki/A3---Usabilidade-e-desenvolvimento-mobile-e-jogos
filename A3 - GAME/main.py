from nucleo.jogo import Jogo
from cenas.introducao import Introducao

if __name__ == "__main__":
    jogo = Jogo()
    jogo.trocar_cena(Introducao(jogo))
    jogo.executar()
