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
| 具体的キャラクターDefinition | ディルック・香菱・ガイアを実装 |
| Character Effect API | 実装済み |
| HP・Energy・ダメージ管理 | 実装済み |
| キャラクター交代 | 実装済み |
| Action / 合法手生成・合法性検証 | 実装済み |
| カードTarget定義・合法Target生成 | 実装済み |
| CPU対CPUの進行 | 実装済み |
| ダイス生成・支払い・調和・再ロール | 実装済み |
| 元素付着・元素反応 | 実装済み（対応範囲は拡張中） |
| Character Status / Combat Status | 実装済み |
| Summon / イベントフック | 実装済み |
| キャラクター・交代・ダメージ・Energy・ラウンド・カードイベント | 実装済み |
| 食事・Summon生成カード | 実装済み |
| 天賦・武器・聖遺物の装備基盤 | 実装済み |
| 武器カード参照実装 | 「旅道の剣」を実装 |
| 聖遺物カード参照実装 | 「教官の帽子」を実装 |
| ゲーム状態コピー | 実装済み |
| ゲーム状態シミュレーション | 実装済み |
| ゲーム状態評価 | 実装済み |
| CPUへの状態評価接続 | 実装済み |
| CPU 2手先minimax探索 | 実装済み |
| CPU Alpha-Beta枝刈り | 実装済み |
| CPU探索深度・ノード上限設定 | 実装済み |
| 確率結果コンテナ・期待値計算 | 実装済み |
| ダイスロールの確率結果列挙 | 実装済み |
| ゲーム状態のダイスロールChance Node化 | 実装済み |
| CPUによるダイスChance Node期待値評価 | 実装済み |
| 確率的Game結果をCPU探索へ統合 | 実装済み（ダイスロール・リロール・次ラウンドロール） |
| GUI・対戦画面 | 未実装 |

## キャラクターDefinition

固定情報と固有行動を `CharacterDefinition` に分離し、`CharacterState` はHP・Energy・元素付着・Statusなどの可変状態を保持します。武器種 `weapon_type` は `sword` / `claymore` / `polearm` / `bow` / `catalyst` を想定しています。

## カードDefinition

カードの固定情報と効果を `CardDefinition` に分離し、`Game` は `CardRegistry` からカード定義を解決します。カード固有処理は `content/cards/` に分離しています。

`CardTargetType` は `NONE` / `ACTIVE_CHARACTER` / `ANY_ALLY_CHARACTER` を持ち、`Game.get_legal_actions()` と `Game.is_action_legal()` が同じTarget定義を利用します。

天賦・武器・聖遺物は `EquipmentStatusDefinition` を基盤とし、`talent` / `weapon` / `artifact` の装備スロットを独立して管理します。同一スロットの装備は置き換えられます。

## 状態効果・イベント

持続効果は Character Status、Combat Status、Summon、Equipment Status に分離されています。各状態は `Definition` と `Instance` に分離されています。

主なイベントは `NormalAttackEvent`、`ElementalSkillEvent`、`ElementalBurstEvent`、`CharacterSwitchEvent`、`DamageEvent`、`EnergyEvent`、`RoundEndEvent`、`CardActionEvent` です。

## 元素反応

現在、蒸発、溶解、過負荷、感電、凍結、超電導、拡散、結晶化、燃焼、開花、激化を実装しています。

## 状態コピー・シミュレーション

`GameState.copy()` はゲーム中の可変状態を独立したオブジェクトとして複製します。

`engine/simulation.py` には以下のヘルパーがあります。

- `copy_state(state)`
- `copy_game(game)`
- `simulate_action(game, action)`
- `simulate_roll(game, player_id, count)`
- `ChanceOutcome`
- `expected_value(outcomes, value_function)`

`ChanceOutcome` は確率的に発生する結果と確率を保持し、`expected_value()` は確率の合計を検証した上で期待値を計算します。

`DicePool.roll_outcomes()` は乱数を使用せず、指定されたダイス個数について重複する組み合わせをまとめた全確率結果を生成します。`simulate_roll()` はその結果を独立した `Game` に適用し、CPU探索で利用できるChance Node形式へ変換します。通常のゲーム進行で使用する `DicePool.roll()` は変更していません。

## ゲーム状態評価

`engine/evaluation.py` の `evaluate_state(game, player_id)` は、ゲーム状態を指定プレイヤー視点の `float` に変換します。正の値は指定プレイヤー側、負の値は相手側に有利な状態を表します。

現在の評価対象:

- キャラクターHP
- 生存キャラクター数
- Energy
- Character Status
- Summon
- 手札枚数
- ダイス数
- Shield
- 元素付着
- ラウンド終了状態
- ACTIONフェーズの行動権
- 勝敗・終局状態

終局時は通常のヒューリスティック評価より勝敗を優先し、勝利/敗北を大きな固定値として返します。また、評価関数自身はゲーム状態を変更しません。

## CPU探索

`players/cpu.py` のCPUはACTIONフェーズで、合法手をシミュレーションし、`evaluate_state()` によって結果状態を評価します。

現在は探索深度を `CpuPlayer(search_depth=...)` で設定でき、既定値は2です。候補となる自分のActionから探索を開始し、相手の合法手、その後の自分の合法手というように交互に探索します。

探索はAlpha-Beta枝刈りを使用します。また `max_search_nodes` によって1回のAction評価で探索するノード数の上限を設定できます。深い探索を利用する場合でも、ノード上限によって計算量を制御できます。

```text
自分の合法手
    │
    ├─ Action A ── simulate ── 相手の応答 ── 自分の応答 ...
    ├─ Action B ── simulate ── 相手の応答 ── 自分の応答 ...
    ├─ Action C ── simulate ── 相手の応答 ── 自分の応答 ...
    │                 │
    │                 └─ Alpha-Betaで不要な枝を削除
    │
    └─ 探索ノード上限で計算量を制御
              │
              ▼
       evaluate_state()
```

探索では指定したCPUプレイヤーの評価視点を末端まで固定します。これにより、相手側の評価値をそのまま最大化する誤りを避けています。

確率結果の共通基盤として `ChanceOutcome` / `expected_value()` を追加し、さらに実際のダイスロールを `simulate_roll()` から確率的Game状態へ展開できるようにしました。現在は `CpuPlayer._evaluate_chance_roll()` が各ダイス結果を探索へ渡し、確率で重み付けした期待評価値を計算できます。さらに、リロールActionも `simulate_reroll()` によってChance Node化し、CPUが複数のリロール候補を期待値で比較できます。次ラウンド開始時の両プレイヤーのダイス生成についても `simulate_round_roll()` で完全な確率結果を列挙でき、CPU探索では `sample_round_roll()` による固定seedの有界サンプリングを利用します。また、ラウンド終了を先に宣言したプレイヤーを次ラウンドの開始プレイヤーとして保持します。`END_ROUND → 次ラウンドRoll Chance → Reroll Chance → Action` までをCPU探索から再帰的に評価できるようにし、次ラウンドRoll後の各結果を現在手番から探索へ接続します。Roll後のリロール候補は上位16件に制限し、`round_roll_samples`（既定64）と`max_search_nodes`で分岐数を制御します。8個のダイスを両者同時に完全列挙した際の巨大な分岐数は、CPU探索では固定seedの有界サンプリングによって抑えています。

## ラウンド進行

1. **ROLLフェーズ**: ダイス取得・リロール
2. **ACTIONフェーズ**: 攻撃、スキル、爆発、交代、調和、カードなどを実行
3. 両プレイヤーがラウンド終了すると `RoundEndEvent` を処理
4. 次ラウンドのROLLフェーズへ移行

## テスト

```powershell
python -m pytest
```

状態コピー・シミュレーション、確率結果、ダイスChance Node、カードTarget、装備、元素反応、イベント、合法手生成、状態評価、CPU探索、CPUのChance Node評価などを含むテストを実施しています。

## 今後の予定

1. Chance Nodeのキャッシュ・トランスポジションを実装して探索性能を改善する
2. 探索性能を改善し、深い探索を安定して実行できるようにする
4. 探索性能を改善し、深い探索を安定して実行できるようにする
5. 武器・聖遺物・Target付きカードを増やす
6. 各カード・キャラクターのルール実装範囲を拡張する
7. 多様なデッキへの対応を進める
8. GUIを実装する
