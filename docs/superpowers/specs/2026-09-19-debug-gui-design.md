# 原神TCG デバッグGUI 設計仕様

## 1. 目的

現在の七聖召喚エンジンとCPUを、テストコードを書かずに細かく手動検証できるデバッグGUIを追加する。

GUIは完成版のゲームUIではなく、既存の `Game` / `GameState` / `Action` / CPU探索を利用する検証クライアントとして実装する。既存エンジンのゲームルールをGUI側へ重複実装しない。

成功条件は以下とする。

- GUIから既存の合法Actionを選択・実行できる。
- 実行後のHP、Energy、元素付着、Status、Summon、装備、ダイス等を確認できる。
- Action/Eventの履歴を時系列で確認できる。
- 現在の合法Actionと、選択Actionの対象・コストを確認できる。
- CPUに1手実行させ、探索統計を確認できる。
- デバッグ用に保存した状態を後から再現できる拡張余地を持つ。
- GUI追加後も既存のゲームエンジンのテストを壊さない。

## 2. スコープ

### Phase 1

最初の実装では以下を対象とする。

- Tkinterベースのメインウィンドウ
- ゲーム生成
- Player/Characterの状態表示
- HP / Energy / 元素 / 元素付着の表示
- ダイス表示
- 現在Phase / 現在手番表示
- 合法Action一覧
- Action実行
- 対象選択
- イベントログ
- 画面更新

### Phase 2

Phase 1の動作確認後、以下を追加する。

- Character Status詳細
- Combat Status詳細
- Summon詳細
- Weapon / Artifact / Talent詳細
- カード一覧とカード使用
- リロール操作
- CPU 1手実行
- CPU探索深度 / ノード上限 / Rollサンプル数設定
- CPUの探索ノード数 / Cache Hit等の表示

### Phase 3

デバッグ・再現性を高めるため、以下を追加する。

- デバッグ状態の作成・編集
- 状態JSON保存 / 読み込み
- シナリオ再生
- 特定イベント・元素反応の検証補助

Phase 1の完成をもってGUI基盤の初回実装完了とし、Phase 2/3は既存エンジンの成熟度に応じて段階的に追加する。

## 3. 技術方針

Python標準ライブラリのTkinterを使用する。GUI専用の外部依存は追加しない。

理由:

- 現在のPython 3.14環境から利用しやすい。
- Windowsで追加インストールなしに起動しやすい。
- デバッグGUIとして十分な入力・表示機能を持つ。
- 既存エンジンへの依存方向を単純にできる。

想定構成:

```text
gui/
    __init__.py
    app.py
    game_view.py
    state_view.py
    action_panel.py
    event_log.py
    debug_state.py
run_gui.py
```

Phase 1ではファイル分割を必要以上に増やさず、責務が明確になる範囲で分離する。将来のPhase 2/3で状態編集やCPUデバッグが大きくなった場合に追加モジュールへ分離する。

## 4. アーキテクチャ

GUIとゲームエンジンの責務を分離する。

```text
Tkinter GUI
   │
   │ Action / 表示要求
   ▼
GUI Controller / View
   │
   │ 既存APIを呼び出す
   ▼
Game / GameState / Action / CPU
   │
   ▼
既存のルール・イベント・シミュレーション
   │
   ▼
更新されたGameState + Events
   │
   ▼
GUI再描画
```

GUIから直接HPやStatusを書き換えることを通常の対戦操作には使用しない。通常操作は必ず既存のAction生成・合法性検証・実行経路を通す。

これにより、GUIで成功した操作が通常ゲームでも同じルールで実行されることを保証しやすくする。

## 5. 画面設計

メイン画面は以下の領域に分ける。

```text
┌──────────────────────────────────────────────────────┐
│ 原神TCG Debug GUI                       Phase / Round │
├──────────────────────┬───────────────────────────────┤
│ Opponent              │ State Inspector               │
│ Character 1           │ Current Player                │
│ Character 2           │ Phase                         │
│ Character 3           │ Dice                          │
│ Status / Summon       │ Selected Action               │
├──────────────────────┼───────────────────────────────┤
│ Player                │ Action Panel                  │
│ Character 1           │ [Normal] [Skill] [Burst]     │
│ Character 2           │ [Card] [Switch] [End]        │
│ Character 3           │ Target / Dice controls        │
│ Status / Summon       │                               │
├──────────────────────┴───────────────────────────────┤
│ Event Log                                             │
└──────────────────────────────────────────────────────┘
```

キャラクター欄は最低限、名前、元素、HP、Energy、元素付着、装備状態を確認できるようにする。詳細なStatus/SummonはPhase 2で拡張する。

## 6. Action操作

GUIは `game.get_legal_actions(player_id)` を基準に現在の合法Actionを表示する。

Action実行時は既存のAction実行APIを呼び出す。GUI側で独自の合法性判定を行わない。

Actionの種類ごとに必要なTargetやコスト情報を表示する。

```text
Action: ELEMENTAL_SKILL
Player: 0
Character: Xingqiu
Target: Character 1
Cost: Hydro 1 + Any 2
Legal: YES
```

不正なActionや対象が選択された場合は、ゲーム状態を変更せず、GUI上にエラーを表示する。

## 7. イベントログ

既存イベントAPIを利用し、GUI操作によって発生したイベントを時系列で表示する。

最低限、以下を人間が追跡可能な形式へ変換する。

- Action開始 / 解決
- Damage
- Energy
- Character Switch
- Elemental Skill
- Elemental Burst
- Card Action
- Round End
- Elemental Reaction
- Status / Summonの追加・消費・変化（取得できる範囲）

例:

```text
[15:02:31] P1 Normal Attack
[15:02:31] P1 -> P2 Character 1: 2 Physical Damage
[15:02:31] P2 HP 10 -> 8
[15:02:32] P1 Xingqiu Elemental Skill
[15:02:32] Reaction: Vaporize
[15:02:32] Rain Sword usages: 0 -> 2
```

ログはゲーム状態とは別のGUI表示データとして扱う。

## 8. State Inspector

State Inspectorはゲーム状態を読み取り専用で表示する。

Phase 1:

- Round
- Phase
- Current Player
- Player dice
- Character HP / Max HP
- Character Energy
- Character Element
- Elemental Aura
- Game Over / Winner

Phase 2:

- Character Status
- Combat Status
- Summon
- Weapon
- Artifact
- Talent
- Hand

表示用変換はGUI側に置き、ゲーム状態そのものを変更しない。

## 9. CPU連携

Phase 2で `CpuPlayer` をGUIから実行できるようにする。

CPU実行は通常のGUI Actionと同じく、既存のゲームオブジェクトを使用する。

表示する探索情報:

- Search Depth
- Max Search Nodes
- Round Roll Samples
- Last Search Nodes
- Last Search Cache Hits
- 選択されたAction

CPU探索自体をGUI用に複製しない。

## 10. 状態保存

Phase 3ではデバッグ用状態をJSONとして保存する。

保存対象はゲーム状態を再現するために必要な値に限定し、GUI固有のウィジェット状態は保存しない。

保存・読み込み経路は、可能なら既存の `GameState.copy()` と整合する形にする。既存モデルに安全なシリアライズ機構が存在しない段階で、GUIが `__dict__` を無条件にJSON化する方式は採用しない。

## 11. エラー処理

GUIからの操作で発生する入力エラー、合法性エラー、ゲーム終了後の操作などはGUIをクラッシュさせず、エラーメッセージとして表示する。

予期しない例外はログへ記録し、開発中に原因を追跡できるようにする。ただし例外を無条件に握り潰さない。

## 12. テスト

GUI自体のテストとゲームエンジンのテストを分離する。

Phase 1では少なくとも以下をテストする。

- GUI Controllerがゲームを生成できる。
- 合法Action一覧を取得して表示用データへ変換できる。
- 選択Actionが既存のゲーム実行経路へ渡される。
- Action実行後にState Inspector用データが更新される。
- イベントログがAction実行に対応して更新される。
- ゲーム終了状態でもGUIが例外終了しない。

Tkinterの実ウィンドウを必要とするテストは、通常のルールエンジンテストとは分ける。可能な範囲では表示変換・Controllerを純粋なPythonロジックとしてテストし、GUIウィジェットへの依存を最小化する。

既存のテストスイートは変更後も全件通過を維持する。

## 13. 起動方法

プロジェクトルートから以下で起動できる形を目標とする。

```powershell
python run_gui.py
```

GUI起動処理は `run_gui.py` に集約し、ゲームルールは `engine/` に置いたままにする。

## 14. 非目標

初回GUIでは以下を実装しない。

- 完成版の美術・演出を目的としたゲームUI
- オンライン対戦
- ネットワーク通信
- 画像アセット管理
- 音声
- GUI専用の独自ゲームルール
- CPUアルゴリズムのGUI専用実装

## 15. 将来拡張

本設計では、以下を後から追加できるようにする。

- 任意GameState生成
- 状態JSONの保存・読み込み
- シナリオテスト
- 行動候補ごとの評価値比較
- CPU探索木の可視化
- イベントフィルタ
- 特定イベントのステップ実行
- カード・キャラクター追加時の手動回帰テスト

特に将来的なカード・キャラクター大量追加を考慮し、GUI側にカード固有処理やキャラクター固有処理を実装しない。
