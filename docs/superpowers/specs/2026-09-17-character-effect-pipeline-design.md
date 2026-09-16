# キャラクター固有効果パイプライン設計

## Goal

キャラクター固有効果を `engine/game.py` のキャラクター別分岐なしで実装できるようにし、Character Status / Combat Status / Summon / GameEvent を共通の効果パイプラインへ接続する。

## Context

現在の `CharacterDefinition` は通常攻撃・元素スキル・元素爆発をオーバーライドでき、`CharacterState` はDefinitionへの参照を保持している。Status / Summon はDefinitionとInstanceに分離され、`Game._emit_event()` がイベントを各インスタンスへ通知している。

この基盤を維持しながら、キャラクター固有効果がゲーム状態を変更するための共通APIを `Game` に追加する。キャラクター固有処理は `content/characters/` のDefinition側に置き、Game本体にはキャラクターIDによる分岐を追加しない。

## Architecture

```text
CharacterDefinition
      |
      | action method
      v
Game effect API
      |
      +-- damage
      +-- Character Status
      +-- Combat Status
      +-- Summon
      +-- Energy
      |
      v
GameEvent
      |
      +-- Character Status
      +-- Combat Status
      +-- Summon
      |
      v
state mutation / usage consumption
```

### Effect API

`Game` は少なくとも次の操作を提供する。

- `add_character_status(player_id, character_index, status)`
- `add_combat_status(player_id, status)`
- `add_summon(player_id, summon)`
- 既存の `deal_damage()` / `change_energy()` を共通Effect APIとして利用する

入力は既存の `StatusInstance` / `SummonInstance` とし、Definitionから生成する場合は各Registryの `create()` を利用できる。キャラクターDefinitionは具体的なInstanceを生成して渡せるため、Gameは効果の種類を判定するだけでキャラクター固有の意味を持たない。

### Event lifecycle

効果の発動前後を識別できるよう、既存の `resolved` フラグを維持する。

1. Gameがイベントを作成する。
2. `_emit_event(event)` で既存効果へ通知する。
3. 必要な効果がイベントを変更する。
4. Gameが状態を確定する。
5. `resolved=True` として再度イベントを通知する。
6. 期限切れStatus / Summonを除去する。

既存のDamageEventとEnergyEventの二段階通知を基本形とする。新しいイベントを追加する場合も、同じ「変更可能な未解決イベント → 状態確定 → 解決済み通知」の考え方を採用する。

### Status / Summon ownership

- Character Statusは `PlayerState.characters[character_index].statuses` に保持する。
- Combat Statusは `PlayerState.combat_statuses` に保持する。
- Summonは `PlayerState.summons` に保持する。
- `EffectContext` の `owner_id` と `character_index` を使い、イベントを受けた効果自身が所有者を識別できる。

### Stacking / replacement

既存仕様を維持する。

- 同一Character Status IDは既存Instanceを削除して新しいInstanceへ置換する。
- 同一Combat Status IDも置換する。
- 同一Summon IDは新しいInstanceへ置換する。

使用回数の加算・上限処理など、実際の七聖召喚で必要になる複雑な重ね掛け規則は、この段階では一般化しすぎず、個別効果の実装時に明示する。

## Character Definition contract

`CharacterDefinition` の既存メソッドを維持する。

```python
normal_attack(game, player_id) -> None
elemental_skill(game, player_id) -> None
elemental_burst(game, player_id) -> None
```

各Definitionは `game` の共通Effect APIだけを利用する。`engine.game` がキャラクターの具体的クラスやIDを参照することは禁止する。

## Error handling

- player_idが0/1以外なら `ValueError`
- character_indexが範囲外なら `ValueError`
- Status / Summonの型が不正なら `TypeError`
- 死亡キャラクターへのCharacter Status付与など、一般的に禁止する操作は共通APIで検証する
- 既存の攻撃・エネルギー・カード処理のエラー仕様は変更しない

## Testing strategy

TDDで次を検証する。

1. Character Statusを指定キャラクターへ追加できる。
2. Combat Statusを指定プレイヤーへ追加できる。
3. Summonを指定プレイヤーへ追加できる。
4. 追加した効果が次のイベントを受け取る。
5. 使用回数0の効果がイベント後に除去される。
6. Definition側から共通Effect APIを使って効果を生成できる。
7. 既存の166テストがすべて維持される。

キャラクター固有の実際の七聖召喚効果は、この基盤完成後に個別のルール確認とテストを行って追加する。

## Non-goals

この変更では以下を実装しない。

- 全キャラクターの追加
- 全カードの追加
- 装備システムの完成
- GUI
- 高度なCPU探索アルゴリズム
- 七聖召喚の完全なルール再現

## Success criteria

- CharacterDefinitionから固有効果を共通API経由で実装できる。
- `engine/game.py` にキャラクター固有のID/class分岐を追加しない。
- Status / Summon / Eventの既存挙動を壊さない。
- テストスイートが全件成功する。
