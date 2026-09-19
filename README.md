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
| 具体的キャラクターDefinition | ディルック・香菱・ガイア・行秋を実装 |
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
| 武器カード参照実装 | 5種の基礎武器を実装 |
| 特殊武器効果 | 祭礼シリーズ4種（剣・大剣・弓・法器）を実装 |
| 武器によるActionコスト変更 | 実装済み |
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
| CPU探索Transposition Table | 実装済み |
| デバッグGUI | Phase 1実装済み |
| GUI・完成版対戦画面 | 未実装 |

## デバッグGUI

Tkinterを利用した検証用GUIを追加しています。完成版のゲームUIではなく、既存の `Game` / `GameState` / `Action` を使ってルールを手動確認するためのクライアントです。GUI専用の外部依存は追加していません。

プロジェクトルートから以下で起動できます。

```powershell
python run_gui.py
```

Phase 1では以下を確認できます。

- Round / Phase / Current Player
- 両プレイヤーのキャラクター名・元素・HP・Energy・元素付着
- ダイス
- Character Status、Combat Status、Summonの表示
- 現在の合法Action一覧
- ActionのTarget / Cost / Legal状態
- 既存の `Game.execute_action()` を通したAction実行
- Actionで発生したイベントの時系列ログ
- 新しいゲームの開始

GUIのControllerはゲームルールを複製せず、既存の合法Action生成・合法性検証・Action実行経路を利用します。イベントログはGUI側の `DebugGame` ラッパーで既存イベント通知を記録します。

将来のPhase 2ではカード・CPU探索・詳細Status表示、Phase 3ではデバッグ状態の編集・JSON保存などを追加する予定です。

## キャラクターDefinition

固定情報と固有行動を `CharacterDefinition` に分離し、`CharacterState` はHP・Energy・元素付着・Statusなどの可変状態を保持します。武器種 `weapon_type` は `sword` / `claymore` / `polearm` / `bow` / `catalyst` を想定しています。

## カードDefinition

カードの固定情報と効果を `CardDefinition` に分離し、`Game` は `CardRegistry` からカード定義を解決します。カード固有処理は `content/cards/` に分離しています。

`CardTargetType` は `NONE` / `ACTIVE_CHARACTER` / `ANY_ALLY_CHARACTER` を持ち、`Game.get_legal_actions()` と `Game.is_action_legal()` が同じTarget定義を利用します。

天賦・武器・聖遺物は `EquipmentStatusDefinition` を基盤とし、`talent` / `weapon` / `artifact` の装備スロットを独立して管理します。同一スロットの装備は置き換えられます。

武器などの状態効果からActionコストを変更できるよう、`StatusDefinition.modify_action_cost()` と `Game._modify_action_cost()` を用意しています。これにより、コスト軽減を「コスト参照時に状態を消費する」のではなく、実際のActionイベント発生時に1回だけ消費する形で実装できます。

## 状態効果・イベント

持続効果は Character Status、Combat Status、Summon、Equipment Status に分離されています。各状態は `Definition` と `Instance` に分離されています。

主なイベントは `NormalAttackEvent`、`ElementalSkillEvent`、`ElementalBurstEvent`、`CharacterSwitchEvent`、`DamageEvent`、`EnergyEvent`、`RoundEndEvent`、`CardActionEvent` です。

## 元素反応

現在、蒸発、溶解、過負荷、感電、凍結、超電導、拡散、結晶化、燃焼、開花、激化を実装しています。

## 武器カード

基礎武器として、旅道の剣、白鉄の大剣、白纓槍、鴉羽の弓、魔導緒論を実装しています。各カードは対応する `weapon_type` のキャラクターだけが使用でき、アクティブキャラクターの元素に対応した2個の同色ダイスをコストとして使用します。

特殊武器効果として祭礼シリーズを実装しています。現在は祭礼の剣、祭礼の大剣、祭礼の弓、祭礼の断片があり、いずれも対応する武器種のキャラクターに装備できます。装備キャラクターが元素スキルを使用した後、そのキャラクターの次の通常攻撃・元素スキル・元素爆発のコストを1個軽減します。軽減状態は次の対象Actionの実行時に消費され、単なるコスト問い合わせでは消費されません。共通処理を `_SacrificialWeaponStatus` にまとめ、武器種ごとの差分は各StatusDefinitionで管理しています。

## キャラクター実装

行秋を追加しました。元素スキルで2水元素ダメージを与えて「雨すだれの剣」を2回分生成し、元素爆発で1水元素ダメージを与えて同状態を2回分生成します。「雨すだれの剣」は味方の通常攻撃解決後に2水元素ダメージを追加し、1回分消費します。Combat Statusとして実装することで、行秋以外の味方キャラクターが通常攻撃した場合にも発動できる構造にしています。

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

さらに探索中の同一状態を再利用するTransposition Tableを追加しました。状態の可変データを再帰的に正規化したキーに、root player、現在手番、探索深度を組み合わせ、同じ条件の探索結果を再利用します。Alpha-Betaで探索窓が狭められた途中結果はキャッシュせず、完全探索窓の結果だけを保存します。リロールChance Nodeと次ラウンドRoll Chance Nodeについても、状態・深度・対象プレイヤー・設定値・Actionを含むキーで期待値をキャッシュします。各ルート探索開始時にはキャッシュをクリアし、異なる盤面の探索結果が混ざらないようにしています。

## ラウンド進行

1. **ROLLフェーズ**: ダイス取得・リロール
2. **ACTIONフェーズ**: 攻撃、スキル、爆発、交代、調和、カードなどを実行
3. 両プレイヤーがラウンド終了すると `RoundEndEvent` を処理
4. 次ラウンドのROLLフェーズへ移行

## テスト

```text
python -m pytest
```

GUI追加前の回帰テストは298件が全件成功しており、GUI用テストを追加しています。pytestの警告は `TestState` が `__init__` を持つことによる `PytestCollectionWarning` が1件残っています。
