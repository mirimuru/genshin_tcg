# カード効果イベント駆動化 設計書

## 目的

カード効果をキャラクター効果と同じイベント駆動基盤へ接続し、カード使用前後の状態変化をStatus / Summon / Character Statusから監視できるようにする。カード追加時に`engine/game.py`へ個別分岐を増やさず、カード定義を独立して拡張できる構造を維持する。

## 現状

`CardDefinition`は`play(game, player_id, target)`を持ち、`CardRegistry`でカードIDから定義を解決している。`Game._execute_card()`では、カードの合法性確認、ダイス支払い、手札からの削除、`card.play()`を一箇所で実行している。

キャラクター側では`CharacterActionEvent`、`CharacterSwitchEvent`、`DamageEvent`、`EnergyEvent`などを`Game._emit_event()`でStatus / Summon / Character Statusへ通知する仕組みが既にある。

## 設計

### 1. CardActionEvent

`engine/events.py`に`CardActionEvent`を追加する。

フィールド:

- `player_id: int` — カードを使用したプレイヤー
- `card_id: str` — 使用したカードID
- `target: object | None` — カードへ渡された対象
- `resolved: bool = False` — カード効果の解決完了を示す

キャラクターイベントと同様に、解決前イベントと解決後イベントの2段階で通知する。

### 2. Game._execute_card()

既存の順序を維持する。

1. カード定義を取得
2. 手札・コスト・`can_play()`を検証
3. コストを支払う
4. 手札からカードを削除
5. `CardActionEvent(resolved=False)`を通知
6. `card.play()`を実行
7. `CardActionEvent.resolved = True`として再通知

これにより、既存カードの効果そのものを変更せずイベント購読だけを追加できる。

### 3. CardDefinition API

既存の`play()` / `can_play()` APIは維持する。今回の変更ではカード定義を全面的に作り直さない。

将来的にカード効果をより細粒度のEffectへ分割できる余地を残すが、本変更の範囲には含めない。

### 4. イベント通知のスナップショット性

`Game._emit_event()`が既に採用している「イベント開始時点で存在したStatus / Summonをリスト化して通知する」方式をカードイベントにもそのまま適用する。カード効果中に追加されたStatus / Summonが同じイベントの途中で再入場することはない。

### 5. リファレンスカード

既存の`SweetMadame`を最初のリファレンスカードとする。これはカード使用時に対象キャラクターを1 HP回復する単純なEvent Cardであり、カードイベント基盤と既存のターゲット指定APIを検証するのに適している。

現行の仕様資料ではSweet Madameはコスト0で対象キャラクターを1 HP回復し、Foodカードとして1ラウンドにつき各キャラクター1回までの制限がある。今回はイベント基盤接続を主目的とし、既存コードにないFood制限全体の実装は別スコープとする。citeturn0search0turn0search1

### 6. テスト

新規テストで以下を保証する。

- CardActionEventが解決前に通知される
- カード効果後に`resolved=True`で再通知される
- `player_id` / `card_id` / `target`が正しい
- カードイベントを購読するCombat StatusまたはCharacter Statusが正常に反応できる
- 既存カードの効果と既存195テストを壊さない

## 非目標

- 全カードの実装
- Food制限など未実装ルール全体の追加
- カードAIの実装
- カード効果を新しいEffect DSLへ全面移行
- ターン進行方式の変更

## 成功条件

- `CardActionEvent`がキャラクターイベントと同じ`Game._emit_event()`経路で通知される
- 既存カードの挙動が変わらない
- 新しいカード固有イベント反応を`Game`の個別分岐なしでテストできる
- 既存195件以上のテストがすべて成功する
