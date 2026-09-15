from engine.actions import Action, ActionType
from engine.state import GamePhase


class HumanPlayer:
    def choose_action(self, game, player_id, legal_actions=None):
        player = game.state.players[player_id]

        if legal_actions is None:
            legal_actions = game.get_legal_actions(player_id)

        if game.state.phase is GamePhase.ROLL:
            dice = player.dice.as_list()
            print()
            print("ダイス：")
            for index, dice_type in enumerate(dice, start=1):
                print(f"{index}. {dice_type.value}")
            print("振り直すダイスの番号をカンマ区切りで入力（空欄でリロールなし）")
            while True:
                command = input("リロール：").strip()
                if not command:
                    return Action(player_id, ActionType.REROLL_DICE, target=())
                try:
                    indices = [int(value.strip()) - 1 for value in command.split(",")]
                    if len(set(indices)) != len(indices) or any(index < 0 or index >= len(dice) for index in indices):
                        raise ValueError
                    target = tuple(dice[index] for index in indices)
                    action = Action(player_id, ActionType.REROLL_DICE, target=target)
                    if action in legal_actions:
                        return action
                except ValueError:
                    pass
                print("無効な入力です")

        character = player.active_character
        print()
        print(f"現在のキャラクター：{character.name}")
        print(f"HP：{character.hp}/{character.max_hp}")
        print()

        action_map = {
            "1": ActionType.NORMAL_ATTACK,
            "2": ActionType.ELEMENTAL_SKILL,
            "3": ActionType.ELEMENTAL_BURST,
            "5": ActionType.END_ROUND,
        }
        print("1. 通常攻撃")
        print("2. 元素スキル")
        print("3. 元素爆発")
        print("4. キャラクター交代")
        print("5. ラウンド終了")

        while True:
            command = input("行動を選択してください：").strip()
            if command in action_map:
                action_type = action_map[command]
                action = next((item for item in legal_actions if item.action_type is action_type), None)
                if action is not None:
                    return action

            if command == "4":
                try:
                    index = int(input("交代先の番号："))
                    action = Action(player_id, ActionType.SWITCH_CHARACTER, target=index)
                    if action in legal_actions:
                        return action
                except ValueError:
                    pass

            print("無効な入力です")
