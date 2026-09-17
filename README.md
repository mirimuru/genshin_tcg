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
| GUI・対戦画面 | 未実装 |

## キャラクターDefinition

固定情報と固有行動を `CharacterDefinition` に分離し、`CharacterState` はHP・Energy・元素付着・Statusなどの可変状態を保持します。武器種 `weapon_type` は `sword` / `claymore` / `polearm` / `bow` / `catalyst` を想定しています。

```text
CharacterDefinition
  ├─ character_id / name / element
  ├─ max_hp / max_energy / weapon_type
  ├─ normal_attack()
  ├─ elemental_skill()
  └─ elemental_burst()

CharacterState
  ├─ definition
  ├─ hp / energy
  ├─ elemental_aura
  └─ statuses
```

現在の具体的キャラクターはディルック、香菱、ガイアです。

## カードDefinition

カードの固定情報と効果を `CardDefinition` に分離し、`Game` は `CardRegistry` からカード定義を解決します。カード固有処理は `content/cards/` に分離しています。

```text
CardDefinition
  ├─ card_id / name / cost
  ├─ target_type
  ├─ get_cost()
  ├─ get_legal_targets()
  ├─ is_target_legal()
  ├─ can_play()
  └─ play()
```

`CardTargetType` は `NONE` / `ACTIVE_CHARACTER` / `ANY_ALLY_CHARACTER` を持ち、`Game.get_legal_actions()` と `Game.is_action_legal()` が同じTarget定義を利用します。

天賦・武器・聖遺物は `EquipmentStatusDefinition` を基盤とし、`talent` / `weapon` / `artifact` の装備スロットを独立して管理します。同一スロットの装備は置き換えられます。

## 状態効果・イベント

持続効果は以下に分離されています。

- **Character Status**: キャラクター単位の状態
- **Combat Status**: プレイヤー単位の状態
- **Summon**: プレイヤー単位の召喚物
- **Equipment Status**: キャラクターに装備される状態

各状態は `Definition` と `Instance` に分離されています。イベントには `NormalAttackEvent`、`ElementalSkillEvent`、`ElementalBurstEvent`、`CharacterSwitchEvent`、`DamageEvent`、`EnergyEvent`、`RoundEndEvent`、`CardActionEvent` があります。

## 元素反応

現在、蒸発、溶解、過負荷、感電、凍結、超電導、拡散、結晶化、燃焼、開花、激化を実装しています。

## 状態コピー・シミュレーション

`GameState.copy()` はゲーム中の可変状態を独立したオブジェクトとして複製します。

`engine/simulation.py` には以下のヘルパーがあります。

- `copy_state(state)`
- `copy_game(game)`
- `simulate_action(game, action)`

`simulate_action()` は元の `Game` を変更せず、コピーしたゲームへActionを実行します。CPU探索で「このActionを実行したらどうなるか」を安全に評価するための基盤です。

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

終局時は通常のヒューリスティック評価より勝敗を優先し、勝利/敗北を大きな固定値として返します。また、仮想状態を評価するため、評価関数自身はゲーム状態を変更しません。

```text
Game
  │
  ├─ get_legal_actions()
  │
  └─ simulate_action()
          │
          ▼
      仮想GameState
          │
          ▼
      evaluate_state()
          │
          ▼
       評価値(float)
```

この構造を次段階のCPU探索・Action選択へ接続します。

## CPU

現在のCPUはヒューリスティック方式で合法手を利用して行動します。状態評価とシミュレーション基盤が追加されたため、今後は複数手先を考慮する探索方式へ拡張します。

## ラウンド進行

1. **ROLLフェーズ**: ダイス取得・リロール
2. **ACTIONフェーズ**: 攻撃、スキル、爆発、交代、調和、カードなどを実行
3. 両プレイヤーがラウンド終了すると `RoundEndEvent` を処理
4. 次ラウンドのROLLフェーズへ移行

## テスト

```powershell
python -m pytest
```

状態コピー・シミュレーション、カードTarget、装備、元素反応、イベント、合法手生成、CPUなどを含むテストを実施しています。

現在のGitHub Actionsでは状態評価実装のテストとして **258 passed** を確認しています。ユーザー環境の最新テスト結果は `249 passed` で、状態評価テスト追加後に9件増加しています。

## 今後の予定

1. 状態評価の精度を拡張する
2. シミュレーションと状態評価をCPUへ接続する
3. 相手の応答を考慮する探索CPUを実装する
4. ダイス・ランダム効果を含む探索を強化する
5. 武器・聖遺物・Target付きカードを増やす
6. 各カード・キャラクターのルール実装範囲を拡張する
7. 多様なデッキへの対応を進める
8. GUIを実装する
