from engine.cards import CardDefinition


class SweetMadame(CardDefinition):
    name = "甘雨ではなく、甘酔ではなく、甘い料理"
    cost = {
        "OMNI": 1
    }

    def can_play(self, game, player_id):
        player = game.state.players[player_id]
        character = player.active_character

        return character.alive and character.hp < character.max_hp

    def play(self, game, player_id):
        player = game.state.players[player_id]
        character = player.active_character

        character.hp = min(character.max_hp, character.hp + 1)