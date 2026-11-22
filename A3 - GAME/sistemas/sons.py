import array
import math
import random
import pygame


class Sons:
    """Sintetiza efeitos sonoros retro em tempo real sem depender de arquivos externos."""

    TAXA = 22050

    def __init__(self):
        self.ativo = False
        self.sons = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.TAXA, size=-16, channels=1, buffer=512)
            self.ativo = True
            self._gerar_todos()
        except pygame.error:
            self.ativo = False

    def _criar_som(self, amostras):
        buf = array.array("h", [max(-32767, min(32767, int(v))) for v in amostras])
        return pygame.mixer.Sound(buffer=buf)

    def _gerar_todos(self):
        # 1. Plasma (Fase 2 - mantido original)
        self.sons["plasma"] = self._gerar_onda(0.14, 980, 260, volume=0.28, ruido=0.08)

        # 2. Espingarda Calibre 12 (Fase 1 - explosão grave + ruído + pump metálico)
        self.sons["espingarda"] = self._gerar_espingarda()

        # 3. Besta de 3 tiros (Fase 3 - estalo de corda + assobio dos virotes)
        self.sons["besta"] = self._gerar_besta()

        # 4. Efeitos padronizados para todas as fases
        self.sons["pulo"] = self._gerar_onda(0.12, 220, 540, volume=0.22)
        self.sons["dash"] = self._gerar_onda(0.16, 480, 140, volume=0.26, ruido=0.25)
        self.sons["hitkill_fantasma"] = self._gerar_onda(0.24, 300, 1180, volume=0.34, ruido=0.12)
        self.sons["dano"] = self._gerar_onda(0.22, 190, 65, volume=0.38, ruido=0.30)
        self.sons["powerup"] = self._gerar_arpejo([523, 659, 784, 1046], 0.06, volume=0.26)
        self.sons["invocar"] = self._gerar_onda(0.35, 110, 280, volume=0.30, ruido=0.18)

    def _gerar_espingarda(self):
        rng = random.Random(12)
        duracao = 0.28
        total = int(self.TAXA * duracao)
        amostras = []
        for i in range(total):
            t = i / self.TAXA
            prog = i / total
            # Estampido inicial grave com decaimento rápido
            env_tiro = math.exp(-t * 18.0)
            freq_grave = 155 * (1.0 - prog * 0.75) + 38
            grave = math.sin(2.0 * math.pi * freq_grave * t)
            explosao = rng.uniform(-1.0, 1.0) * math.exp(-t * 14.0)

            # Estalo metálico do pump-action no final (t > 0.14s)
            pump = 0.0
            if 0.14 <= t <= 0.23:
                t_p = t - 0.14
                env_p = math.sin((t_p / 0.09) * math.pi)
                pump = (
                    0.45 * math.sin(2.0 * math.pi * 1350 * t_p)
                    + 0.35 * rng.uniform(-1.0, 1.0)
                ) * env_p

            val = (grave * 0.65 + explosao * 0.75) * env_tiro + pump * 0.55
            amostras.append(val * 32767 * 0.42)
        return self._criar_som(amostras)

    def _gerar_besta(self):
        rng = random.Random(33)
        duracao = 0.19
        total = int(self.TAXA * duracao)
        amostras = []
        for i in range(total):
            t = i / self.TAXA
            # Estalo curto da corda e madeira
            env_corda = math.exp(-t * 42.0)
            corda = math.sin(2.0 * math.pi * (340 - 160 * (t / duracao)) * t) * env_corda

            # Assobio aerodinâmico agudo dos 3 virotes
            env_vento = math.sin(min(1.0, t / 0.03) * (math.pi / 2)) * math.exp(-t * 16.0)
            freq_assobio = 1450 - 650 * (t / duracao)
            assobio = (
                0.55 * math.sin(2.0 * math.pi * freq_assobio * t)
                + 0.45 * rng.uniform(-1.0, 1.0)
            ) * env_vento

            val = corda * 0.75 + assobio * 0.60
            amostras.append(val * 32767 * 0.32)
        return self._criar_som(amostras)

    def _gerar_onda(self, duracao, freq_ini, freq_fim, volume=0.25, ruido=0.0):
        rng = random.Random(42)
        total = int(self.TAXA * duracao)
        amostras = []
        fase = 0.0
        for i in range(total):
            prog = i / total
            freq = freq_ini + (freq_fim - freq_ini) * prog
            fase += (2.0 * math.pi * freq) / self.TAXA
            env = (1.0 - prog) ** 1.4
            sinal = math.sin(fase)
            if ruido > 0:
                sinal = sinal * (1.0 - ruido) + rng.uniform(-1.0, 1.0) * ruido
            amostras.append(sinal * env * volume * 32767)
        return self._criar_som(amostras)

    def _gerar_arpejo(self, notas, dur_nota, volume=0.25):
        amostras = []
        for freq in notas:
            total = int(self.TAXA * dur_nota)
            for i in range(total):
                prog = i / total
                env = 1.0 - prog * 0.7
                val = math.sin(2.0 * math.pi * freq * (i / self.TAXA))
                amostras.append(val * env * volume * 32767)
        return self._criar_som(amostras)

    def tocar(self, nome):
        if self.ativo and nome in self.sons:
            self.sons[nome].play()