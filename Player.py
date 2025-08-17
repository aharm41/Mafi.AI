import PlayerRoles as Roles
 

class Player:
    def __init__(self, name: str, number: int = 1, role: Roles.PlayerRole = Roles.PlayerRole.INNOCENT) -> None:
        self.number = number
        self.name = name
        self.role = role