from Player import Player

class GameState:
    def __init__(self, players: list[Player], innocents: list[Player], mafias: list[Player], sheriff: Player, doctor: Player) -> None:
        self.alivePlayers = self.players = players
        self.innocents = innocents
        self.mafias = mafias
        self.sheriff = sheriff
        self.doctor = doctor
        self.deadPlayers = []
        self.currentDay = 1


    def killPlayer(self, player: Player):
        self.alivePlayers.remove(player)
        self.deadPlayers.append(player)