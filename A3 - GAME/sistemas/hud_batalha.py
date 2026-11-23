"""HUD simples para a batalha final."""
import pygame

from sistemas.hud import Hud
from sistemas.cenario import LARGURA


class HudBatalha:
    def __init__(self):
        self.vida_visual = 0.0
        self.hud_fases = Hud()
        self.fonte = self.hud_fases.fonte_titulo

    def atualizar(self, dt, dragao):
        self.vida_visual += (dragao.vida - self.vida_visual) * min(1.0, dt * 8.0)

    def _barra(self, tela, x, y, largura, vida, vida_max, cor):
        proporcao = max(0.0, min(1.0, vida / max(1, vida_max)))
        pygame.draw.rect(tela, (24, 18, 28), (x - 2, y - 2, largura + 4, 18), border_radius=5)
        pygame.draw.rect(tela, (78, 67, 76), (x, y, largura, 14), border_radius=4)
        if proporcao:
            pygame.draw.rect(tela, cor, (x, y, max(1, round(largura * proporcao)), 14), border_radius=4)

    def desenhar(self, tela, heroi, dragao):
        self.hud_fases.desenhar_vidas(tela, heroi)

        titulo_dragao = self.fonte.render("DRAGÃO", True, (255, 226, 190))
        tela.blit(titulo_dragao, titulo_dragao.get_rect(center=(LARGURA // 2, 28)))
        largura = 430
        self._barra(
            tela,
            (LARGURA - largura) // 2,
            42,
            largura,
            self.vida_visual,
            dragao.vida_max,
            (185, 39, 48),
        )
