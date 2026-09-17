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
| HP・エネルギー管理 | 基本実装 |
| ダメージ処理 | 実装済み |
| キャラクター交代 | 実装済み |
| `Action` / 合法手生成 | 実装済み |
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

## キャラクターDefinition

キャラクターの固定情報と固有行動を `CharacterDefinition` に分離し、`CharacterState` はHP・Energy・元素付着・Statusなどの可変状態を保持します。

`CharacterDefinition` には武器種 `weapon_type` も保持できます。現在は `sword` / `claymore` / `polearm` / `bow` / `catalyst` を想定した文字列値を使用し、既存キャラクターとの後方互換性のため未指定も許容します。

```text
CharacterDefinition
  ├─ character_id / name / element
  ├─ max_hp / max_energy
  ├─ weapon_type
  ├─ normal_attack()
  ├─ elemental_skill()
  └─ elemental_burst()
       │
       └─ Character Status / Combat Status / Summon / Equipment

CharacterState
  ├─ definition
  ├─ hp / energy
  ├─ elemental_aura
  └─ statuses

CharacterRegistry
  └─ character_id -> CharacterDefinition

content/characters/
  ├─ diluc.py       # claymore
  ├─ kaeya.py       # sword
  └─ xiangling.py   # polearm
```

## カードDefinition

カードの固定情報と固有効果を `CardDefinition` に分離し、`Game` はカードIDから `CardRegistry` を通して定義を解決します。カード固有処理は `content/cards/` の個別ファイルへ配置します。

`CardDefinition.get_cost()` を通して、現在のゲーム状態からコストを解決できる設計にしています。通常カードは静的な `cost` を返し、武器カードはアクティブキャラクターの元素に応じて「同色」コストを返します。

```text
CardDefinition
  ├─ card_id / name / cost
  ├─ get_cost()
  ├─ can_play()
  └─ play()
       │
       └─ CardActionEvent
            ├─ 使用開始（resolved=False）
            └─ 効果解決後（resolved=True）

TalentCardDefinition
  ├─ equipment_slot = "talent"
  ├─ required_character_id
  ├─ can_play()
  └─ create_status()

WeaponCardDefinition
  ├─ equipment_slot = "weapon"
  ├─ weapon_type
  ├─ get_cost()       # アクティブキャラクターの元素に応じた同色コスト
  ├─ can_play()       # アクティブキャラクターの武器種を検証
  └─ create_status()  # WeaponEquipmentStatusDefinitionを生成
       │
       └─ CharacterState.add_equipment()

ArtifactCardDefinition
  ├─ equipment_slot = "artifact"
  ├─ can_play()       # CardDefinitionのダイス支払い判定を利用
  └─ create_status()  # ArtifactEquipmentStatusDefinitionを生成
       │
       └─ CharacterState.add_equipment()

CardRegistry
  └─ card_id -> CardDefinition

content/cards/
  ├─ artifacts.py
  ├─ foods.py
  ├─ summons.py
  ├─ talents.py
  └─ weapons.py
```

## 装備システム

装備は `EquipmentStatusDefinition` を共通基盤として、キャラクターの `statuses` に保持します。

`CharacterState.add_equipment()` は `equipment_slot` が同じ装備を置き換えます。そのため、天賦・武器・聖遺物は独立したスロットとして同時に装備でき、同じスロットの装備を付け替えた場合は以前の装備だけが置き換わります。

武器専用には `WeaponEquipmentStatusDefinition` を追加し、`weapon_type` を持たせています。`WeaponCardDefinition` はカード側の武器種と生成する装備Statusの武器種が一致することも検証します。

聖遺物専用には `ArtifactEquipmentStatusDefinition` を追加し、`equipment_slot = "artifact"` を共通化しています。これにより今後の聖遺物カードを個別の `StatusDefinition` として追加できます。

### 武器カード参照実装

`content/cards/weapons.py` に片手剣「旅道の剣」を参照実装しています。現在の七聖召喚カード仕様では、2個の同色元素サイコロをコストとし、片手剣キャラクターのみ装備でき、装備キャラクターの与えるダメージを+1します。

- `card_id = traveler_handy_sword`
- `weapon_type = sword`
- 武器スロットへ装備
- コストはアクティブキャラクターの元素に対応する同色2ダイス
- 装備キャラクターの通常攻撃に+1ダメージ
- 元素スキルなど通常攻撃以外には適用しない

通常攻撃への効果は `NormalAttackEvent` の開始イベントで状態を有効化し、既存の `modify_damage()` フックでダメージ確定前に+1します。これにより `Game` 本体へ武器IDごとの条件分岐を追加していません。

### 聖遺物カード参照実装

`content/cards/artifacts.py` に「教官の帽子」を参照実装しています。現在の七聖召喚カード仕様では、無色2個の元素サイコロをコストとし、装備キャラクターが元素反応を起こした後、そのキャラクターの元素タイプに対応する元素サイコロを1個生成します。この効果は1ラウンド最大3回です。citeturn0search4turn0search2

- `card_id = instructors_cap`
- `equipment_slot = artifact`
- コストは任意2ダイス
- 装備キャラクター自身が起こした元素反応のみ対象
- 装備キャラクターの元素と同じ種類のダイスを1個生成
- 1ラウンド最大3回
- `RoundEndEvent` でラウンド内カウンタをリセット

生成ダイスは `DicePool.add()` を通して追加し、既存のダイス支払い・合法手生成とは独立した「ダイス生成」処理として扱っています。

## 現在のコンテンツカード

- `モンド風ハッシュドポテト`: 出場キャラクターを1HP回復。コストは任意1ダイス。
- `絶雲お焦げ`: 次に使用する通常攻撃のダメージを1増加。
- `アビスの呼びかけ`: ランダムなヒルチャール召喚物を1体生成。
- `冷血の剣`: ガイア専用天賦カード。装備時に元素スキルを即時使用し、装備中の元素スキル後にラウンド1回2HP回復。
- `旅道の剣`: 片手剣武器カード。アクティブキャラクターの元素に対応する同色2ダイスで使用し、装備キャラクターの与えるダメージを+1。
- `教官の帽子`: 聖遺物カード。元素反応を起こした装備キャラクターに対応する元素ダイスを生成し、1ラウンド最大3回。

## 状態効果のアーキテクチャ

ゲーム中の持続効果は、用途に応じて以下に分離しています。

- **Character Status**: 個々のキャラクターに付与される状態
- **Combat Status**: プレイヤー側に保持され、交代しても維持される状態
- **Summon**: プレイヤー側に保持され、ラウンド終了や後続アクションなどのイベントで処理される召喚物
- **Equipment Status**: Character Statusのイベント基盤を利用しつつ、`equipment_slot` 単位で装備を管理する状態
  - `weapon`: 武器
  - `talent`: 天賦
  - `artifact`: 聖遺物

各状態は `Definition` と `Instance` に分離されています。`StatusInstance` は `data` を保持でき、キャラクター固有の使用回数やラウンド内カウンタにも利用できます。

## イベントシステム

`engine/events.py` にゲームイベントを定義し、`Game._emit_event()` が現在存在するStatus / Summonへイベントを通知します。

現在の主なイベント:

- `NormalAttackEvent`
- `ElementalSkillEvent`
- `ElementalBurstEvent`
- `CharacterSwitchEvent`
- `DamageEvent`
- `EnergyEvent`
- `RoundEndEvent`
- `CardActionEvent`

キャラクターアクション、交代、カードイベントには `resolved` フラグがあり、開始通知と解決通知を同じイベント型で扱います。

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

聖遺物カード基盤の実装では、装備スロットの独立性、同一聖遺物スロットの置換、元素反応によるダイス生成、ラウンド内3回制限、装備者以外の反応を無視することをテストしています。

**GitHub Actionsで 233 passed** を確認済みです。

主なテスト対象:

- 通常攻撃・元素スキル・元素爆発の開始/解決イベント
- キャラクター交代の開始/解決イベント
- カード使用の開始/解決イベント
- Status / Summonのイベント購読
- DamageEventの変更と実ダメージへの反映
- EnergyEventの上限・下限適用
- 元素反応と各反応固有効果
- 食事カード・Summon生成カード・天賦カード
- 天賦・武器・聖遺物の装備スロット独立性
- 天賦装備と同一装備スロットの置換
- キャラクターの武器種定義
- 武器装備Statusの生成
- 武器カードの武器種一致/不一致判定
- 武器カードの同色コスト判定
- 武器カードの装備処理
- 片手剣による通常攻撃ダメージ+1
- 武器効果が元素スキルへ誤適用されないこと
- 聖遺物装備Statusのスロット判定
- 聖遺物カードの装備処理
- 聖遺物スロットの置換
- 聖遺物と武器・天賦のスロット独立性
- 教官の帽子による元素ダイス生成
- 教官の帽子のラウンド3回制限とラウンド終了時リセット
- 装備者以外が起こした元素反応では教官の帽子が発動しないこと

## 今後の予定

1. 武器カード・聖遺物カードの種類を増やす
2. 各カード・キャラクターのルール実装範囲を拡張する
3. 合法手・状態評価を強化する
4. CPUの探索・戦略選択を強化する
5. 多様なデッキへの対応を進める
6. GUIを実装する
