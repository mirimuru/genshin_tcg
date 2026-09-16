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
| エネルギー変更イベント | 基盤実装済み・ゲーム処理への接続を進行中 |
| ラウンド終了イベント | 実装済み |
| カード定義・Registry | 基盤実装済み |
| GUI・対戦画面 | 未実装 |

## 状態効果のアーキテクチャ

ゲーム中の持続効果は、用途に応じて3種類に分離しています。

- **Character Status**: 個々のキャラクターに付与される状態
- **Combat Status**: プレイヤー側に保持され、交代しても維持される状態
- **Summon**: プレイヤー側に保持され、ラウンド終了などのイベントで処理される召喚物

各状態は `Definition` と `Instance` に分離されています。

```text
Definition
  └─ 効果のルール・ID・最大使用回数

Instance
  └─ 現在の使用回数などの可変状態
```

### イベントシステム

`engine/events.py` にゲームイベントを定義し、`Game._emit_event()` が現在存在する Status / Summon に通知します。

現在のイベント:

- `DamageEvent`: ダメージ計算後、HPへ適用する前後に通知
- `EnergyEvent`: キャラクターのEnergy増減を表すイベント。通常攻撃・元素スキルによるEnergy獲得や元素爆発による消費をイベント基盤へ移行するための土台
- `RoundEndEvent`: 両プレイヤーがラウンド終了した際に通知

Status / Summon の `on_event()` をオーバーライドすることで、`game.py` に個別効果を増やさずに新しい持続効果を実装できます。

現在、開花による `BloomCoreGeneration` は `DamageEvent` を利用して草原核を生成しています。燃焼も `BurningFlameGeneration` により `DamageEvent` から燃焼の炎を生成し、`BurningFlame` が `RoundEndEvent` を受け取ってダメージを処理します。結晶化シールドも解決済み `DamageEvent` を利用して生成されます。

## 実装済み元素反応

現在のルールエンジンには以下の反応が実装されています。

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

反応に応じた追加ダメージ、元素付着、強制交代、貫通ダメージ、シールド、燃焼の炎、草原核、激化フィールドなどをテストしています。

## ラウンド進行

1. **ROLLフェーズ**
   - 各プレイヤーがダイスを取得
   - 任意のダイスを1回リロール
2. **ACTIONフェーズ**
   - 通常攻撃、元素スキル、元素爆発、交代、調和、カードなどを実行
   - 両プレイヤーがラウンド終了するとラウンド終了イベントを処理
   - 次ラウンドのROLLフェーズへ移行

## CPU

現在のCPUはヒューリスティック方式です。合法手生成を利用して、強制交代、元素爆発、交代、元素スキル、通常攻撃、調和、ラウンド終了などを選択します。

```python
from engine.game import Game
from players.cpu import CpuPlayer

players = [CpuPlayer(), CpuPlayer()]
history = game.run(players, max_actions=1000)
```

将来的には評価関数を拡張し、探索ベースのAIへ発展させます。

## テスト

```powershell
python -m pytest
```

燃焼のイベント統合まで含めて **148 passed** を確認済みです。今回、エネルギー変更イベントの基盤テストを4件追加したため、次回実行時は **152 tests** になる想定です。

GitHub Actionsでも `main` へのpushおよび `main` 向けPull Requestでpytestを実行します。

## ディレクトリ構成

```text
engine/
  actions.py          # ActionとActionType
  cards.py            # カード定義・Registry
  dice.py             # ダイス種別・生成・支払い・調和・リロール
  effects.py          # 標準Status / Summon定義
  elemental_reactions.py # 元素反応ルール
  events.py           # ゲームイベント定義
  game.py             # ゲーム進行・合法手・Action実行・イベント通知
  state.py            # ゲーム状態・プレイヤー・キャラクター
  statuses.py         # Status定義・Instance・Registry
  summons.py         # Summon定義・Instance・Registry
players/
  human.py             # 人間プレイヤー基盤
  cpu.py               # ヒューリスティックCPU
tests/
  # 各ルール・状態・反応・イベントのテスト
```

## 今後の実装方針

### 短期

1. Status / Summon のイベントフックへ既存の個別処理を段階的に移行
2. エネルギー増減を `EnergyEvent` としてゲーム処理へ接続
3. キャラクター固有効果をDefinition方式で追加
4. カード効果を同じイベント基盤へ接続

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
