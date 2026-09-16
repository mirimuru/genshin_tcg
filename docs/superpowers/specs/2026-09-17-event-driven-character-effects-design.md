# イベント駆動型キャラクター固有効果 設計書

**日付:** 2026-09-17

## 目的

七聖召喚のキャラクター、キャラクター状態、戦闘状態、召喚物を追加しても `engine/game.py` にキャラクターID依存の分岐を増やさず、固有効果をイベント駆動で表現できる基盤を整える。

現在のルールエンジンは `DamageEvent`、`EnergyEvent`、`RoundEndEvent` と `StatusDefinition.on_event()` / `modify_damage()` を持っている。この設計では既存APIを尊重し、イベントモデルを段階的に拡張する。

## 設計方針

### 1. イベントをルール解決の共通境界にする

ゲーム中の主要な出来事を `GameEvent` のサブクラスとして表現する。

対象は以下とする。

- 通常攻撃の開始・解決
- 元素スキルの開始・解決
- 元素爆発の開始・解決
- キャラクター切り替え
- ダメージの確定前・確定後
- Energyの変更前・変更後
- ラウンド終了

ただし、既存実装を一度に大きく変更せず、現在の `DamageEvent`、`EnergyEvent`、`RoundEndEvent` を互換性を保って拡張する。

### 2. Statusはイベント購読者として維持する

`StatusDefinition.on_event(instance, event, game, context)` を主APIとする。

一時的な使用回数、トリガー済みフラグ、ターン内カウンタなどは `StatusInstance.data` に保持する。

ダメージの変更は引き続き `modify_damage()` で処理し、イベント通知と責務を分離する。

### 3. CharacterDefinitionへ固有ルールを閉じ込める

キャラクターの通常攻撃、元素スキル、元素爆発、コスト、固有状態生成などは `CharacterDefinition` またはそこから生成されるStatus/Combat Status/Summonで表現する。

`Game` に以下のような分岐を追加しない。

```python
if character.character_id == "...":
    ...
```

これにより、新キャラクターの追加が既存ルールエンジンの変更を必要としない構造を目指す。

### 4. イベント処理のスナップショット性を維持する

`Game._emit_event()` は現在と同様、イベント開始時点で存在するStatus/Summonをスナップショットとして取得して通知する。

イベント処理中にStatus/Summonが追加・消費されても、同じイベントの途中で新しく追加された効果を意図せず再入場させない。

## データフロー

```text
Action
  |
  v
Game action resolver
  |
  +--> cost / pre-resolution event
  |
  +--> CharacterDefinition
  |       |
  |       +--> direct damage
  |       +--> Status
  |       +--> Combat Status
  |       +--> Summon
  |
  +--> DamageEvent / EnergyEvent
  |
  v
post-resolution event
  |
  v
GameState update / defeat check
```

## ダメージ処理

ダメージは次の順序を基本とする。

1. 攻撃者側Character Statusによるダメージ入力変更
2. 対象の元素オーラ確認
3. 元素反応解決
4. 反応・凍結解除などの追加ダメージ計算
5. `DamageEvent` の事前通知
6. 実ダメージ適用
7. `DamageEvent.resolved = True`
8. `DamageEvent` の事後通知
9. 反応による貫通・拡散などの追加処理
10. ゲーム終了判定

この順序をテストで固定する。

## Energy処理

Energy変更は既存の `change_energy()` をイベント境界として利用する。

1. `EnergyEvent` 作成
2. 事前通知
3. 上限・下限を適用して実値変更
4. `event.amount` を実際の変化量へ更新
5. `resolved = True`
6. 事後通知

これにより「Energyを得たとき」「Energyが減少したとき」の効果を共通APIで実装できる。

## キャラクター追加方針

次のリファレンスキャラクターは、単純な固定ダメージだけでなく、イベント発生時にStatus/Combat Statusを生成または消費するタイプを選ぶ。

実装前に公式・信頼できるカードデータを確認し、通常攻撃・元素スキル・元素爆発・コスト・Energy・固有効果をテストへ落とし込む。

## テスト方針

既存179テストを回帰テストとして維持する。

追加テストでは最低限以下を検証する。

- 攻撃イベントの発火順序
- Statusが対象イベントだけに反応すること
- Statusの使用回数・`data` が正しく更新されること
- 同一イベント中に追加されたStatus/Summonが誤って再実行されないこと
- DamageEventの変更が実ダメージへ反映されること
- EnergyEventの実変化量が上限・下限込みで正しく通知されること
- 新キャラクターの固有効果
- 既存ディルックの挙動が変わらないこと

## 非目標

この段階では以下を行わない。

- CPU探索アルゴリズムそのものの実装
- 全キャラクターの実装
- 全カードの実装
- GUIの実装
- ルールエンジン全体の大規模リファクタリング

まずイベント駆動の拡張性とルール正確性を確立し、その後にCPUの合法手生成・評価・探索へ進む。
