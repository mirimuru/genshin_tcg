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
| HP・エネルギー管理 | 基本実装 |
| ダメージ処理 | 実装済み |
| キャラクター交代 | 実装済み |
| `Action` / 合法手生成 | 実装済み |
| **統一合法手生成 `LegalActionGenerator`** | **実装済み** |
| CPU対CPUの進行 | 実装済み |
| ダイス生成・支払い・調和・再ロール | 実装済み |
| 元素付着・元素反応 | 実装済み（対応範囲は拡張中） |
| Character Status / Combat Status | 実装済み |
| Summon | 実装済み |
| Status / Summon イベントフック | 実装済み |
| キャラクターアクションイベント | 実装済み（開始/解決） |
| キャラクター交代イベント | 実装済み（開始/解決） |
| ダメージイベント | 実装済み（確定前/確定後） |
| エネルギー変更イベント | 実装済み（変更前/変更後） |
| ラウンド終了イベント | 実装済み |
| カード定義・Registry | 基盤実装済み |
| カードアクションイベント | 実装済み（使用開始/解決後） |
| 食事カード | 実装済み |
| Summon生成カード | 実装済み |
| 装備状態 / 装備スロット | 実装済み |
| 天賦カード | ガイア「冷血の剣」を実装 |
| 武器カード基盤 | 実装済み |
| 武器カード参照実装 | 片手剣「旅道の剣」を実装 |
| 聖遺物カード基盤 | 実装済み |
| 聖遺物カード参照実装 | 「教官の帽子」を実装 |
| GUI・対戦画面 | 未実装 |

## 合法手生成

現在の合法手生成を `engine/legal_actions.py` の `LegalActionGenerator` に集約しています。

```text
GameState
   │
   ▼
LegalActionGenerator.generate(game, player_id)
   │
   ├─ ROLL: リロール
   ├─ 通常攻撃
   ├─ 元素スキル
   ├─ 元素爆発
   ├─ キャラクター交代
   ├─ 元素調和
   ├─ カード使用
   │    └─ CardDefinition.get_legal_targets() で対象を列挙
   └─ ラウンド終了
        │
        ▼
     Action
```

`LegalActionGenerator` は、現在のフェーズ、手番、敗北状態、強制交代、凍結状態、Energy、ダイスコスト、手札、カードの `can_play()` 判定を考慮して候補を生成します。

カード側には `CardDefinition.get_legal_targets()` を追加しました。対象を必要としない既存カードは `None` を1件返し、今後対象選択を必要とするカードはこのメソッドをオーバーライドして合法対象を列挙できます。

CPUは `legal_actions` が渡されない場合に `LegalActionGenerator` を直接利用するため、CPU側の行動選択と合法手生成の責務を分離しています。

## キャラクターDefinition

`CharacterDefinition` はキャラクターの固定情報と固有行動を保持し、`CharacterState` はHP・Energy・元素付着・Statusなどの可変状態を保持します。武器種 `weapon_type` によって武器カードの装備条件も判定できます。

現在の具体的キャラクターは以下です。

- ディルック
- 香菱
- ガイア

## カード・装備

カードの固定情報と効果は `CardDefinition` とその派生クラスへ分離しています。

```text
CardDefinition
  ├─ TalentCardDefinition
  ├─ WeaponCardDefinition
  └─ ArtifactCardDefinition
```

装備は `EquipmentStatusDefinition` を基盤とし、以下のスロットを独立して管理します。

- `weapon`: 武器
- `talent`: 天賦
- `artifact`: 聖遺物

同じスロットの装備は置き換えられ、異なるスロットの装備は同時に保持できます。

現在の参照実装カード:

- `モンド風ハッシュドポテト`
- `絶雲お焦げ`
- `アビスの呼びかけ`
- `冷血の剣`
- `旅道の剣`
- `教官の帽子`

## イベントシステム

`engine/events.py` にイベントを定義し、`Game._emit_event()` がStatus / Summonへ通知します。

主なイベント:

- `NormalAttackEvent`
- `ElementalSkillEvent`
- `ElementalBurstEvent`
- `CharacterSwitchEvent`
- `DamageEvent`
- `EnergyEvent`
- `RoundEndEvent`
- `CardActionEvent`

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

1. **ROLLフェーズ**: ダイス取得と1回のリロール
2. **ACTIONフェーズ**: 通常攻撃、元素スキル、元素爆発、交代、調和、カードなどを実行
3. 両プレイヤーがラウンド終了すると `RoundEndEvent` を処理して次ラウンドへ移行

## CPU

CPUは現在ヒューリスティック方式です。合法手から元素爆発、交代、元素スキル、通常攻撃、調和などを優先して選択します。

今後は `GameState → Legal Actions → State Evaluation → CPU Search → Action` の流れへ発展させ、多様なデッキへの対応を進めます。

## テスト

```powershell
python -m pytest
```

現在のテスト項目数は **239件**です。

主なテスト対象:

- 通常攻撃・元素スキル・元素爆発の開始/解決イベント
- キャラクター交代の開始/解決イベント
- カード使用の開始/解決イベント
- Status / Summonのイベント購読
- DamageEvent / EnergyEvent
- 元素反応と各反応固有効果
- 食事・Summon生成・天賦・武器・聖遺物カード
- 装備スロットの独立性と同一スロット置換
- 武器種・武器コスト・武器効果
- 聖遺物のダイス生成とラウンド制限
- 統一合法手生成とカード対象列挙

## 今後の予定

1. 合法手生成を `Game` の対戦進行と完全統合
2. 武器カード・聖遺物カードの種類を増やす
3. 各カード・キャラクターのルール実装範囲を拡張する
4. 状態評価を強化する
5. CPUの探索・戦略選択を強化する
6. 多様なデッキへの対応を進める
7. GUIを実装する
