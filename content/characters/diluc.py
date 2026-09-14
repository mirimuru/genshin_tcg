from engine.characters import CharacterDefinition
from engine.state import Element


class Diluc(CharacterDefinition):
    name = "ディルック"
    element = Element.PYRO
    max_hp = 10
    max_energy = 2

    def normal_attack(self, game, player_id):
        game.deal_damage(
            attacker_id=player_id,
            target_id=1 - player_id,
            amount=2,
            element=Element.PHYSICAL,
        )

    def elemental_skill(self, game, player_id):
        game.deal_damage(
            attacker_id=player_id,
            target_id=1 - player_id,
            amount=3,
            element=Element.PYRO,
        )

    def elemental_burst(self, game, player_id):
        game.deal_damage(
            attacker_id=player_id,
            target_id=1 - player_id,
            amount=8,
            element=Element.PYRO,
        )