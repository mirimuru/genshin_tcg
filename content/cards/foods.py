from engine.cards import CardDefinition
from engine.dice import DiceType


class SweetMadame(CardDefinition):
    """モンド風ハッシュドポテト。出場キャラを1回復する。"""

    card_id = "sweet_madame"
    name = "モンド風ハッシュドポテト"
    cost = {DiceType.ANY: 1}

    def can_play(self, game, player_id, target=None):
        player = game.state.players[player_id]
        character = player.active_character
        return character.alive and character.hp < character.max_hp

    def play(self, game, player_id, target=None):
        character = game.state.players[player_id].active_character
        character.heal(1)


SWEET_MADAME = SweetMadame()
