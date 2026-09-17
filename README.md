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
| キャラクター固有ダメージ変更フック | 実装済み |
| キャラクター固有コスト定義 | 実装済み |
| ディルック固有効果 | 実装済み（スキル3回目強化・元素爆発・炎元素付与） |
| 香菱固有効果 | 実装済み（グゥオパァー・旋火輪をイベント駆動で生成） |
| ガイア固有効果 | 実装済み（元素爆発・霜の舞を交代イベントで処理） |
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
| キャラクターアクションイベント | 実装済み（通常攻撃・元素スキル・元素爆発の開始/解決） |
| キャラクター交代イベント | 実装済み（開始/解決） |
| ダメージイベント | 実装済み（確定前/確定後） |
| エネルギー変更イベント | 実装済み（変更前/変更後） |
| ラウンド終了イベント | 実装済み |
| カード定義・Registry | 基盤実装済み |
| カードアクションイベント | 実装済み（使用開始/解決後） |
| Combat Statusを生成するコンテンツカード | 絶雲お焦げを実装 |
| Summonを生成するコンテンツカード | アビスの呼びかけを実装 |
| 装備状態 / 装備スロット | 基盤実装済み（Character State） |
| 天賦カード | ガイア「冷血の剣」を実装 |
| GUI・対戦画面 | 未実装 |

## キャラクターDefinitionのアーキテクチャ

キャラクターの固定情報と固有行動を `CharacterDefinition` に分離し、`CharacterState` はHP・Energy・元素付着・Statusなどの可変状態を保持します。

キャラクター固有効果からは共通の **Character Effect API** を利用でき、`Game` にキャラクターID/classごとの条件分岐を追加せずに状態効果を生成できます。

```text
CharacterDefinition
  ├─ character_id / name / element
  ├─ max_hp / max_energy
  ├─ normal_attack()
  ├─ elemental_skill()
  └─ elemental_burst()
       │
       ├─ Character Effect API
       │    ├─ add_character_status()
       │    ├─ add_combat_status()
       │    └─ add_summon()
       │
       └─ Character Status / Combat Status / Summon

CharacterState
  ├─ definition
  ├─ hp / energy
  ├─ elemental_aura
  └─ statuses

CharacterRegistry
  └─ character_id -> CharacterDefinition

content/characters/
  ├─ diluc.py
  ├─ kaeya.py
  └─ xiangling.py
```

## カードDefinitionのアーキテクチャ

カードの固定情報と固有効果を `CardDefinition` に分離し、`Game` はカードIDから `CardRegistry` を通して定義を解決します。カード固有処理を `Game` のカードID分岐へ追加せず、`content/cards/` の個別ファイルへ配置できます。

```text
CardDefinition
  ├─ card_id / name / cost
  ├─ can_play()
  └─ play()
       │
       └─ CardActionEvent
            ├─ 使用開始（resolved=False）
            └─ 効果解決後（resolved=True）

TalentCardDefinition
  ├─ equipment_slot = "talent"
  ├─ required_character_id
  ├─ can_play()       # 対象キャラクターがアクティブか検証
  └─ create_status()  # 装備Statusを生成
       │
       └─ CharacterState.add_equipment()

CardRegistry
  └─ card_id -> CardDefinition

content/cards/
  ├─ __init__.py
  ├─ foods.py
  ├─ summons.py
  └─ talents.py
```

現在のコンテンツカードは以下を実装しています。

- `モンド風ハッシュドポテト`: 出場キャラクターが生存しておりHPが最大未満の場合に使用でき、1HP回復。コストは任意1ダイス。
- `絶雲お焦げ`: Combat Statusを生成し、次に使用する通常攻撃のダメージを1増加。
- `アビスの呼びかけ`: ランダムなヒルチャール召喚物を1体生成。各ヒルチャールはラウンド終了時に対応元素1ダメージを与え、使用可能回数を1消費する。
- `冷血の剣`: ガイア専用天賦カード。装備時に元素スキルを即時使用し、装備中は元素スキル使用後に1ラウンド1回まで2HP回復する。コストは氷4ダイス。

## カードから状態効果を生成する流れ

カード効果はキャラクター固有処理と同じイベント・状態基盤を利用します。

```text
CardActionEvent
      │
      ▼
CardDefinition.play()
      │
      ├── Combat Status
      │      └── Damage / CharacterActionEventへ反応
      │
      ├── Summon
      │      └── RoundEndEvent / 後続アクションへ反応
      │
      └── TalentCardDefinition
             │
             └── CharacterState.add_equipment()
                    │
                    └── EquipmentStatusDefinition
                           └── CharacterActionEventへ反応
```

### ディルック

現在のディルックDefinitionは、2026年時点の七聖召喚カード仕様を基準に以下を実装しています。

- 通常攻撃: 2物理ダメージ、炎1 + 任意2
- 元素スキル: 3炎ダメージ、ラウンド中3回目のみ+2
- 元素爆発: 8炎ダメージ、Energy 3、炎4ダイス
- 元素爆発後: 2ラウンドの炎元素付与
- 炎元素付与中は物理ダメージを炎ダメージへ変換
- 元素スキル使用回数はCharacter Statusのデータとして保持し、ラウンド終了時にリセット

### 香菱

香菱はイベント駆動型キャラクターのリファレンス実装として追加しています。カードデータでは、通常攻撃が2物理ダメージ、元素スキル「グゥオパァー出撃」がグゥオパァーを2回使用で生成、元素爆発「旋火輪」が3炎ダメージと旋火輪を2回使用で生成します。

実装では `ElementalSkillEvent` / `ElementalBurstEvent` の解決イベントを `Character Status` が購読し、対応する `Summon` を生成します。グゥオパァーは `RoundEndEvent`、旋火輪は後続の `ElementalSkillEvent` に反応してダメージを与えます。これにより、キャラクター固有処理を `Game` のキャラクターID分岐へ追加せずに実装できます。

### ガイア

ガイアは `CharacterSwitchEvent` を利用するイベント駆動型キャラクターのリファレンスとして追加しています。公式カード仕様では、元素爆発「凛冽なる輪舞」は1氷ダメージを与え、「霜の舞」を3回使用で生成し、自分がキャラクターを交代した後に2氷ダメージを与えます。

実装では元素爆発の解決イベントをCharacter Statusが購読して `kaeya_icicle` Combat Statusを生成し、そのCombat Statusが自分の `CharacterSwitchEvent` の解決時に2氷ダメージを与えて使用回数を1消費します。相手側の交代では発動しません。

### ガイア天賦「冷血の剣」

`ColdBloodedStrike` は装備カードのリファレンス実装です。七聖召喚の仕様では、アクティブキャラクターがガイアのときに装備し、装備直後に「霜の噛みつき」を即時使用します。装備中のガイアが元素スキルを使用すると、1ラウンドにつき1回、ガイアを2HP回復します。citeturn0search0turn0search2

実装では `TalentCardDefinition` が対象キャラクター条件を検証し、`CharacterState.add_equipment()` が `talent` スロットへ装備します。装備状態は `EquipmentStatusDefinition` として通常のCharacter Statusと同じイベントパイプラインを購読し、元素スキルの解決イベントから回復を行います。即時使用もカード固有の `play()` から共通の `Game.elemental_skill()` を呼び出して処理します。

## 状態効果のアーキテクチャ

ゲーム中の持続効果は、用途に応じて3種類に分離しています。

- **Character Status**: 個々のキャラクターに付与される状態
- **Combat Status**: プレイヤー側に保持され、交代しても維持される状態
- **Summon**: プレイヤー側に保持され、ラウンド終了や後続アクションなどのイベントで処理される召喚物
- **Equipment Status**: Character Statusのイベント基盤を利用しつつ、`equipment_slot` 単位で装備を管理する状態

各状態は `Definition` と `Instance` に分離されています。`StatusInstance` は追加の状態データを `data` として保持でき、キャラクター固有の使用回数やラウンド内カウンタにも利用できます。

`CharacterState.add_equipment()` は同じ装備スロットの既存装備を置き換えるため、今後 `talent` に加えて `weapon` や `artifact` を追加できます。

## イベントシステム

`engine/events.py` にゲームイベントを定義し、`Game._emit_event()` がイベント開始時点で存在する Status / Summon をスナップショットとして取得して通知します。

現在のイベント:

- `NormalAttackEvent`
- `ElementalSkillEvent`
- `ElementalBurstEvent`
- `CharacterSwitchEvent`
- `DamageEvent`
- `EnergyEvent`
- `RoundEndEvent`
- `CardActionEvent`

キャラクターアクション、交代、カードイベントには `resolved` フラグがあり、開始通知と解決通知を同じイベント型で扱います。Damage / Energyについても、確定前と確定後を同じイベント境界で処理します。

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

直近のローカル確認では **212 passed**。その後、天賦カード・装備状態について5件のテストを追加しており、今回の実装後の想定テスト数は **217件** です。GitHub Actionsでもpytestを実行しています。

イベント駆動部分では、以下をテストしています。

- 通常攻撃・元素スキル・元素爆発の開始/解決イベント
- キャラクター交代の開始/解決イベント
- カード使用の開始/解決イベント
- Status / Summonのイベント購読とスナップショット性
- DamageEventの変更と実ダメージへの反映
- EnergyEventの上限・下限適用後の実変化量
- 香菱のグゥオパァー・旋火輪のイベント駆動生成と消費
- ガイアの元素爆発・霜の舞の交代イベント処理
- ディルックの既存固有効果
- モンド風ハッシュドポテトの使用条件・回復・コスト
- 絶雲お焦げのCombat Status生成・通常攻撃へのダメージ加算・消費
- アビスの呼びかけのカード→Summon生成
- ヒルチャール召喚物のRoundEndEventによる元素ダメージ・使用回数消費
- 天賦カードの装備条件・装備状態生成・即時元素スキル
- 天賦装備中の元素スキルによる1ラウンド1回の回復
- 同一装備スロットの装備置換

## ディレクトリ構成

```text
engine/
  __init__.py         # Gameへの共通Effect API登録
  actions.py
  cards.py            # CardDefinition / TalentCardDefinition / CardRegistry
  dice.py
  effect_api.py       # Character / Combat Status / Summon共通API
  effects.py
  elemental_reactions.py
  events.py           # ゲームイベント定義
  game.py
  characters.py       # CharacterDefinition / Registry
  state.py            # ゲーム状態・キャラクター状態・装備管理
  statuses.py         # Status / EquipmentStatus定義
  summons.py
content/
  characters/
    diluc.py          # ディルックDefinition
    kaeya.py          # ガイアDefinition・固有Combat Status
    xiangling.py      # 香菱Definition・固有Summon
  cards/
    __init__.py       # コンテンツカードのexport
    foods.py          # 料理・Combat Statusカード
    summons.py        # Summon生成カード・ヒルチャール召喚物
    talents.py        # 天賦カード・装備Status
players/
  human.py
  cpu.py
tests/
  test_character_definitions.py
  test_diluc_effects.py
  test_effect_api.py
  test_energy.py
  test_events.py
  test_kaeya.py
  test_xiangling.py
  test_content_cards.py
  test_summon_card.py
  test_abyss_call.py
  test_talent_equipment.py
  # その他各ルール・状態・反応・イベントのテスト
```

## 今後の実装方針

### 短期

1. 実際のキャラクター固有効果をDefinition方式で追加
2. Character Status / Combat Status / Summonへのイベント委譲を拡張
3. 装備カード・イベントカード・支援カードを追加
4. 正式な七聖召喚ルールへの対応範囲を拡張

### 中期

- 装備カード・イベントカード・支援カード
- 武器・聖遺物・天賦などの装備状態
- より正式な七聖召喚ルールへの対応
- 手動対戦UI
