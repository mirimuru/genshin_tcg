from engine.characters import CharacterDefinition
from engine.effects import create_pyro_infusion
from engine.events import RoundEndEvent
from engine.state import Element
from engine.statuses import StatusDefinition, StatusInstance
from engine.dice import DiceType


class DilucSearingOnslaughtCounter(StatusDefinition):
    status_id = "diluc_searing_onslaught_counter"
    name = "逆焔の刃使用回数"

    def on_event(self, instance, event, game, context):
        if isinstance(event, RoundEndEvent) and event.player_id == context.owner_id:
            instance.data["uses"] = 0


class Diluc(CharacterDefinition):
    character_id = "diluc"
    name = "ディルック"
    element = Element.PYRO
    max_hp = 10
    max_energy = 3
    weapon_type = "claymore"
    normal_attack_cost = {DiceType.PYRO: 1, DiceType.ANY: 2}
    elemental_skill_cost = {DiceType.PYRO: 3}
    elemental_burst_cost = {DiceType.PYRO: 4}

    def _skill_counter(self, game, player_id: int):
        character = game.state.players[player_id].active_character
        status = character.get_status("diluc_searing_onslaught_counter")
        if status is None:
            status = StatusInstance(DilucSearingOnslaughtCounter, data={"uses": 0})
            character.add_status(status)
        status.data["uses"] = status.data.get("uses", 0) + 1
        return status.data["uses"]

    def normal_attack(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 2, Element.PHYSICAL)

    def elemental_skill(self, game, player_id: int) -> None:
        damage = 5 if self._skill_counter(game, player_id) == 3 else 3
        game.deal_damage(player_id, 1 - player_id, damage, Element.PYRO)

    def elemental_burst(self, game, player_id: int) -> None:
        game.deal_damage(player_id, 1 - player_id, 8, Element.PYRO)
        game.state.players[player_id].active_character.add_status(create_pyro_infusion(2))


DILUC = Diluc()
