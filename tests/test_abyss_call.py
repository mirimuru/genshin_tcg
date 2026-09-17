from engine.cards import CardDefinition
from engine.dice import DiceType
from engine.events import RoundEndEvent
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState
from engine.summons import SummonInstance
from content.cards.summons import ABYSS_CALL


def make_game():
    def player(player_id):
        return PlayerState(
            player_id,
            [
                CharacterState("A", Element.ANEMO),
                CharacterState("B", Element.HYDRO),
                CharacterState("C", Element.GEO),
            ],
        )

    return Game(GameState([player(0), player(1)]))


def test_abyss_call_generates_one_hilichurl_summon():
    game = make_game()
    game.state.players[0].hand.append(ABYSS_CALL.card_id)
    game.card_registry.register(ABYSS_CALL)
    game.state.players[0].dice._dice.clear()
    game.state.players[0].dice._dice[DiceType.OMNI] = 2

    game._execute_card(
        type(
            "Action",
            (),
            {"player_id": 0, "card_id": ABYSS_CALL.card_id, "target": None},
        )()
    )

    assert len(game.state.players[0].summons) == 1
    summon = next(iter(game.state.players[0].summons.values()))
    assert summon.summon_id in {
        "hilichurl_cryo",
        "hilichurl_hydro",
        "hilichurl_pyro",
        "hilichurl_electro",
    }
    assert summon.usages == 2


def test_hilichurl_summon_deals_one_damage_at_round_end_and_expires():
    game = make_game()
    game.state.players[0].add_summon(
        game.rng.choice([
            __import__("content.cards.summons", fromlist=["HilichurlCryo"]).HilichurlCryo,
            __import__("content.cards.summons", fromlist=["HilichurlHydro"]).HilichurlHydro,
            __import__("content.cards.summons", fromlist=["HilichurlPyro"]).HilichurlPyro,
            __import__("content.cards.summons", fromlist=["HilichurlElectro"]).HilichurlElectro,
        ])()
    )
    hp_before = game.state.players[1].active_character.hp

    game._emit_event(RoundEndEvent(0))

    assert game.state.players[1].active_character.hp == hp_before - 1
    summon = next(iter(game.state.players[0].summons.values()))
    assert summon.usages == 1


def test_abyss_call_has_two_any_dice_cost():
    assert ABYSS_CALL.cost == {DiceType.ANY: 2}
