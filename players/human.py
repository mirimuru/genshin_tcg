class HumanPlayer:
    def choose_action(self, game, player_id):
        player = game.state.players[player_id]
        character = player.active_character

        print()
        print(f"現在のキャラクター：{character.name}")
        print(f"HP：{character.hp}/{character.max_hp}")
        print()
        print("1. 通常攻撃")
        print("2. 元素スキル")
        print("3. 元素爆発")
        print("4. キャラクター交代")
        print("5. ラウンド終了")

        while True:
            command = input("行動を選択してください：").strip()

            if command == "1":
                return ("normal_attack", None)

            if command == "2":
                return ("elemental_skill", None)

            if command == "3":
                return ("elemental_burst", None)

            if command == "4":
                index = int(input("交代先の番号："))
                return ("switch", index)

            if command == "5":
                return ("end_round", None)

            print("無効な入力です")