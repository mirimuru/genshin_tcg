# 原神TCG CPU作成

原神の七聖召喚を題材にした、Python製の対戦ゲームエンジンおよびCPUプレイヤーの開発プロジェクトです。

## 開発環境

- Python 3.14
- pytest
- GitHub: https://github.com/mirimuru/genshin_tcg

## 現在の実装状況

| 機能 | 状態 |
|---|---|
| キャラクター・プレイヤー状態管理 | 実装済み |
| キャラクターDefinition / Registry | 実装済み |
| 具体的キャラクターDefinition | ディルックを実装 |
| Character Effect API | 実装済み |
| HP・エネルギー管理 | 基本実装 |
| ダメージ処理 | 実装済み |
| キャラクター交代 | 実装済み |
| `Action` / 合法手生成 | 実装済み |
| CPU対CPUの進行 | 実装済み |
| ダイス生成・支払い・調和・再ロール | 実装済み |
| 元素付着・元素反応 | 実装済み（対応範囲は拡張中） |
| Character Status | 実装済み |
| Combat Status | 実装済み |
| Summon | 実装済み |
| Status / Summon イベントフック | 実装済み |
| ダメージイベント | 実装済み |
| エネルギー変更イベント | ゲーム処理へ接続済み |
| ラウンド終了イベント | 実装済み |
| カード定義・Registry | 基盤実装済み |
| GUI・対戦画面 | 未実装 |

## キャラクターDefinitionのアーキテクチャ

キャラクターの固定情報と固有行動を `CharacterDefinition` に分離し、`CharacterState` はHP・Energy・元素付着・Statusなどの可変状態を保持します。

キャラクター固有効果からは共通の **Character Effect API** を利用でき、`Game` にキャラクターID/classごとの条件分岐を追加せずに状態効果を生成できます。

現在の共通API:

- `Game.add_character_status(player_id, character_index, status)`
- `Game.add_combat_status(player_id, status)`
- `Game.add_summon(player_id, summon)`

これらは既存の `StatusDefinition` / `StatusInstance` / `SummonDefinition` / `SummonInstance` と `_emit_event()` のイベント配送経路を利用します。

```text
CharacterDefinition
  ├─ character_id / name / element
  ├─ max_hp / max_energy
  ├─ normal_attack()
  ├─ elemental_skill()
  └─ elemental_burst()
       │
       └─ Game Effect API
            ├─ add_character_status()
            ├─ add_combat_status()
            └─ add_summon()

CharacterState
  ├─ definition
  ├─ hp / energy
  ├─ elemental_aura
  └─ statuses

CharacterRegistry
  └─ character_id -> CharacterDefinition

content/characters/
  └─ diluc.py
```

具体的なキャラクターは `content/characters/` に分離します。現在はDefinition方式の実装例としてディルックを追加しています。今後は各キャラクターの実際の七聖召喚上の固有効果をこの方式で追加します。

## 状態効果のアーキテクチャ

ゲーム中の持続効果は、用途に応じて3種類に分離しています。

- **Character Status**: 個々のキャラクターに付与される状態
- **Combat Status**: プレイヤー側に保持され、交代しても維持される状態
- **Summon**: プレイヤー側に保持され、ラウンド終了などのイベントで処理される召喚物

各状態は `Definition` と `Instance` に分離されています。

## イベントシステム

`engine/events.py` にゲームイベントを定義し、`Game._emit_event()` が現在存在する Status / Summon に通知します。

現在のイベント:

- `DamageEvent`
- `EnergyEvent`
- `RoundEndEvent`

## 実装済み元素反応

- 蒸発
- 溶解
- 過負荷
- 感電
- 凍結
- 超電導
- 拡散
- 結晶化
- 燃焼
- 開花
- 激化

## ラウンド進行

1. **ROLLフェーズ**
   - 各プレイヤーがダイスを取得
   - 任意のダイスを1回リロール
2. **ACTIONフェーズ**
   - 通常攻撃、元素スキル、元素爆発、交代、調和、カードなどを実行
   - 両プレイヤーがラウンド終了するとラウンド終了イベントを処理
   - 次ラウンドのROLLフェーズへ移行

## CPU

現在のCPUはヒューリスティック方式です。合法手生成を利用して行動を選択します。

## テスト

```powershell
python -m pytest
```

キャラクターEffect APIについて、Character Status / Combat Status / Summonの追加、イベントによる自動期限切れ、CharacterDefinitionからの利用をテストしています。既存の166テストを維持したうえで、新規Effect APIテストを追加しています。

## ディレクトリ構成

```text
engine/
  __init__.py         # Gameへの共通Effect API登録
  actions.py
  cards.py
  dice.py
  effect_api.py       # Character / Combat Status / Summon共通API
  effects.py
  elemental_reactions.py
  events.py
  game.py
  characters.py       # CharacterDefinition / Registry
  state.py            # ゲーム状態・キャラクター状態
  statuses.py
  summons.py
content/
  characters/
    diluc.py          # ディルックDefinition
players/
  human.py
  cpu.py
tests/
  test_character_definitions.py
  test_effect_api.py
  # その他各ルール・状態・反応・イベントのテスト
```

## 今後の実装方針

### 短期

1. 実際のキャラクター固有効果をDefinition方式で追加
2. Character Status / Combat Status / Summonへのイベント委譲を拡張
3. カード効果を同じイベント基盤へ接続
4. 正式な七聖召喚ルールへの対応範囲を拡張

### 中期

- 装備カード・イベントカード・支援カード
- 武器・聖遺物・天賦などの装備状態
- より正式な七聖召喚ルールへの対応
- 手動対戦UI

### 長期

- CPU評価関数の改善
- 探索ベースAI
- 対戦データ収集・性能評価
- リプレイ・対戦ログ保存
- GUI / Webインターフェース

## 現時点での制限

このプロジェクトは開発途中であり、七聖召喚の完全なルールを再現していません。特にカードの網羅、キャラクター固有効果、装備、詳細なゲームルールは今後の実装対象です。
