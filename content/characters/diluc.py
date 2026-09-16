from engine.characters import CharacterDefinition
from engine.state import Element


class Diluc(CharacterDefinition):
    """ディルックの基本Definition。"""

    character_id = "diluc"
    name = "ディルック"
    element = Element.PYRO
    max_hp = 10
    max_energy = 2

    def normal_attack(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 2, Element.PHYSICAL)

    def elemental_skill(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 3, Element.PYRO)

    def elemental_burst(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 4, Element.PYRO)


DILUC = Diluc()
