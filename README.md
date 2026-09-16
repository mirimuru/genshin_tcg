# 原神TCG CPU作成

原神の七聖召喚を題材にした、Python製の対戦ゲームエンジンおよびCPUプレイヤーの開発プロジェクトです。

## 開発環境

- Python 3.14
- pytest
- GitHub: https://github.com/mirimuru/genshin_tcg

## 現在の実装状況

| 機能 | 状態 |
|---|---|
| キャラクター状態管理 | 実装済み |
| HP・エネルギー管理 | 基本実装 |
| ダメージ処理 | 実装済み |
| キャラクター交代 | 実装済み |
| `Action` データモデル | 実装済み |
| 合法手生成 | 実装済み |
| CPU対CPUの進行 | 実装済み |
| ダイス生成 | 実装済み |
| ダイスコスト計算・支払い | 実装済み |
| ダイス調和 | 実装済み |
| ダイス再ロール | 実装済み |
| ロールフェーズ / アクションフェーズ | 実装済み |
| 元素反応 | 基本実装 |
| Burning / Bloom / Quicken | 実装済み |
| Electro-Charged / Superconduct / Swirl | 実装済み |
| Vaporize / Melt / Overloaded / Frozen | 基本実装 |
| Crystallize / チームシールド | 実装済み |
| Status / Combat Status | 基盤実装済み |
| Summon | 基盤実装済み |
| カードシステム | 基盤実装済み |
| GUI・対戦画面 | 未実装 |

## 状態効果のアーキテクチャ

ゲーム中の可変な効果は、用途に応じて次の3系統で管理します。

- **Character Status**: 特定キャラクターに付く状態。例: 凍結など
- **Combat Status**: プレイヤー側に属し、キャラクター交代後も維持される状態。例: Catalyzing Field、Dendro Core、チームシールド
- **Summon**: ラウンド終了時などに独立して処理される召喚物。例: Burning Flame

各効果は `StatusDefinition` / `StatusInstance`、`SummonDefinition` / `SummonInstance` に分離され、ID・名前・使用回数の定義と、対戦中の残り使用回数を分けて管理します。

## ラウンド進行

現在はラウンドを次の2フェーズに分離しています。

1. **ROLLフェーズ**
   - ラウンド開始時に各プレイヤーが8個のダイスを取得
   - 現在のプレイヤーから順に、1回だけ任意のダイスをリロール可能
   - 0個を選択してリロールをスキップすることも可能
   - 両プレイヤーのリロール終了後、ACTIONフェーズへ移行
2. **ACTIONフェーズ**
   - 通常攻撃、元素スキル、元素爆発、交代、調和、カード使用などを実行
   - 両プレイヤーがラウンド終了すると、召喚物などのラウンド終了時効果を処理
   - その後、次ラウンドのROLLフェーズへ戻る

`GameState.phase` で現在のフェーズを確認できます。

## 元素反応

現在のルールエンジンには、以下の元素反応と関連効果が実装されています。

- Vaporize / Melt / Overloaded
- Electro-Charged / Superconduct
- Frozen
- Swirl
- Crystallize
- Burning → `BurningFlame` Summon
- Bloom → `DendroCore` Combat Status
- Quicken → `CatalyzingField` Combat Status

反応そのものの判定は `engine/elemental_reactions.py`、対戦中の状態管理は `engine/statuses.py` / `engine/summons.py` / `engine/effects.py` が担当します。

## ダイスシステム

- ダイスは元素7種（炎・水・風・雷・草・氷・岩）と万能
- 1ラウンドにつき8個を生成
- 元素ダイスはキャラクターの元素コストに使用
- 万能ダイスは元素ダイスの代用として使用可能
- 通常攻撃・元素スキル・元素爆発は簡易ルールでは3個の元素ダイスを要求
- 通常のキャラクター交代は任意ダイス1個を消費
- 戦闘不能による強制交代は無料
- 不要な元素ダイス1個をアクティブキャラクターの元素へ調和可能

`DicePool.reroll()` により、選択したダイスだけを再生成できます。テスト時には `random.Random` を渡して再現可能な結果にできます。

## カードシステム

カードは `CardDefinition` と `CardRegistry` により定義と登録を分離しています。

- カードID・名前・コストを定義
- `can_play()` で使用条件を検証
- `play()` で効果を実行
- `Game.execute_action()` から通常のActionとして使用

今後はイベントカード、装備カード、支援カードなどをこの基盤へ追加していきます。

## CPU

CPUはROLLフェーズでは、アクティブキャラクターの元素と異なる元素ダイスを優先してリロールします。万能ダイスと一致する元素ダイスは保持します。

ACTIONフェーズでは次の優先順位で行動します。

1. 強制交代
2. 元素爆発
3. HPが低い場合の交代
4. 元素スキル
5. 通常攻撃
6. 攻撃・スキルを可能にする調和
7. ラウンド終了

今後は現在のヒューリスティックを、盤面評価・手札・元素反応・相手の残りHPなどを考慮する評価関数へ発展させます。

## CPU対CPU対戦ループ

```python
from engine.game import Game
from players.cpu import CpuPlayer

players = [CpuPlayer(), CpuPlayer()]

history = game.run(players, max_actions=1000)
```

`step()` は現在のフェーズに応じてリロールまたは通常のアクションを1回実行します。`run()` はゲーム終了または最大行動数到達まで進行します。

## テスト

```powershell
python -m pytest
```

元素反応・状態効果については、通常のダメージテストに加えて、`StatusInstance` / `SummonInstance` がゲーム状態へ正しく統合されていることもテストします。

## ディレクトリ構成

```text
engine/
  actions.py              # ActionとActionType
  cards.py                # カード定義・レジストリ
  dice.py                 # ダイス種別・生成・支払い・調和・リロール
  effects.py              # 標準的なCombat Status / Summonの定義
  elemental_reactions.py  # 元素反応の判定
  game.py                 # フェーズ、合法手生成、ダメージ、Action実行、対戦ループ
  state.py                # ゲーム・プレイヤー・キャラクター状態
  statuses.py             # Character/Combat Statusの定義・実体・レジストリ
  summons.py              # Summonの定義・実体・レジストリ
players/
  human.py                # 人間プレイヤー
  cpu.py                  # ヒューリスティックCPU
tests/
  test_damage.py
  test_elemental_reactions.py
  test_burning.py
  test_bloom.py
  test_quicken.py
  test_crystallize.py
  test_swirl.py
  test_statuses.py
  test_status_integration.py
  test_summons.py
  test_effect_state_integration.py
  ...
```

## 今後の実装ロードマップ

### 1. ルールエンジンの完成度向上

- エネルギー増減の体系化
- 元素付着の詳細化
- Character Status / Combat Status / Summonのイベント処理を共通化
- ラウンド終了・攻撃前後などのイベントフックを整理
- 七聖召喚の正式ルールとの差分を一つずつ埋める

### 2. キャラクター・カードのデータ化

- キャラクター定義をデータファイルから読み込める構造へ整理
- 通常攻撃・元素スキル・元素爆発を定義化
- イベントカード、装備カード、支援カードを追加
- 効果を個別ファイルへ分離し、追加・変更を容易にする

### 3. 手動対戦環境

- コマンドラインまたはWeb UIで手動対戦
- 盤面・手札・ダイス・状態効果を表示
- 対戦ログとリプレイを保存

### 4. CPU AI

- 盤面評価関数
- 相手の手札・状態・残りHPを考慮した行動選択
- デッキごとの戦略・対策
- モンテカルロ木探索などの探索ベースAI
- 対戦データ収集と性能評価

## 現時点での制限

このプロジェクトは開発途中であり、七聖召喚の完全なルールを再現していません。特にカードの網羅、キャラクター固有効果、細かな優先順位・イベント処理、正式ルールとの差分は今後の実装対象です。
