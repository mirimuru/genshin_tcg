from engine.cards import CardDefinition
from engine.dice import DiceType
from engine.events import NormalAttackEvent
from engine.statuses import StatusDefinition, StatusInstance


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


class JueyunGuobaStatus(StatusDefinition):
    """次に使用する通常攻撃のダメージを1増加させる。"""

    status_id = "jueyun_guoba"
    name = "絶雲お焦げ"
    max_usages = 1

    def on_event(self, instance, event, game, context):
        if isinstance(event, NormalAttackEvent) and event.player_id == context.owner_id and not event.resolved:
            instance.data["armed"] = True

    def modify_damage(self, instance, amount, element, game, context):
        if instance.data.pop("armed", False):
            instance.consume()
            return amount + 1, element
        return amount, element


class JueyunGuoba(CardDefinition):
    """絶雲お焦げ。次の通常攻撃のダメージを1増加させる。"""

    card_id = "jueyun_guoba"
    name = "絶雲お焦げ"
    cost = {DiceType.ANY: 1}

    def play(self, game, player_id, target=None):
        game.state.players[player_id].add_combat_status(StatusInstance(JueyunGuobaStatus))


SWEET_MADAME = SweetMadame()
JUEYUN_GUOBA = JueyunGuoba()
