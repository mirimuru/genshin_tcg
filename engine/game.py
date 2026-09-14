from engine.state import Element


class Game:
    def __init__(self, state):
        self.state = state

    def deal_damage(
        self,
        attacker_id: int,
        target_id: int,
        amount: int,
        element: Element,
    ):
        attacker = self.state.players[attacker_id]
        target = self.state.players[target_id]

        target_character = target.active_character

        if not target_character.alive:
            return

        print(
            f"{attacker_character_name(attacker)}が"
            f"{target_character.name}に"
            f"{amount}ダメージ（{element.value}）"
        )

        target_character.receive_damage(amount)

        print(
            f"{target_character.name}のHP："
            f"{target_character.hp}/{target_character.max_hp}"
        )

        self.state.check_game_over()

    def normal_attack(self, player_id: int):
        player = self.state.players[player_id]
        character = player.active_character

        character.definition.normal_attack(self, player_id)

    def elemental_skill(self, player_id: int):
        player = self.state.players[player_id]
        character = player.active_character

        character.definition.elemental_skill(self, player_id)

    def elemental_burst(self, player_id: int):
        player = self.state.players[player_id]
        character = player.active_character

        character.definition.elemental_burst(self, player_id)


def attacker_character_name(player):
    return player.active_character.name