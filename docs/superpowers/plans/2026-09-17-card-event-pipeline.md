# カード効果イベント駆動化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CardActionEventを導入し、カード使用前後のイベントを既存のStatus/Summon/Character Statusイベント基盤へ接続する。

**Architecture:** `Game._execute_card()`の既存の検証・支払い・手札削除・`CardDefinition.play()`という責務を維持し、その効果処理の前後へ`CardActionEvent`通知を追加する。既存の`_emit_event()`のスナップショット通知をそのまま利用するため、カードイベント専用のディスパッチ機構は作らない。

**Tech Stack:** Python 3.14、pytest 9、既存のengine events/statuses/cards architecture。

**Spec:** `docs/superpowers/specs/2026-09-17-card-event-pipeline-design.md`

## Global Constraints

- 既存の`CardDefinition.can_play()` / `play()` APIを維持する。
- カード固有処理を`engine/game.py`のカードID分岐へ戻さない。
- 既存195件以上のテストを壊さない。
- テスト先行で実装する。
- Food制限など今回のイベント基盤以外のルールは実装しない。

---

### Task 1: CardActionEventのモデルを追加

**Files:**
- Modify: `engine/events.py`
- Test: `tests/test_card_events.py`

**Interfaces:**
- Produces: `CardActionEvent(player_id: int, card_id: str, target: object | None = None, resolved: bool = False)`

- [ ] **Step 1: Write the failing test**
  - `CardActionEvent`を生成し、各フィールドと既定の`resolved=False`を検証する。
- [ ] **Step 2: Run the focused test and confirm failure**
  - `python -m pytest tests/test_card_events.py -q`
- [ ] **Step 3: Implement the minimal event dataclass**
  - `GameEvent`を継承し、カード固有情報を保持する。
- [ ] **Step 4: Run the focused test and confirm pass**
  - `python -m pytest tests/test_card_events.py -q`
- [ ] **Step 5: Commit**
  - `feat: add card action event`

### Task 2: Gameのカード実行へイベント通知を追加

**Files:**
- Modify: `engine/game.py`
- Modify: `tests/test_card_events.py`

**Interfaces:**
- Consumes: `CardActionEvent`
- Produces: `_execute_card()`がカード効果前後に同一イベントインスタンスを通知し、後段では`resolved=True`となる。

- [ ] **Step 1: Add failing integration tests**
  - テスト用Combat Statusをイベント購読させ、カード使用前後の通知順と値を記録する。
  - `player_id`、`card_id`、`target`、`resolved`を検証する。
- [ ] **Step 2: Run focused tests and confirm failure**
  - `python -m pytest tests/test_card_events.py -q`
- [ ] **Step 3: Implement event emission in `_execute_card()`**
  - コスト支払い・手札削除後、`play()`前に未解決イベントを通知する。
  - `play()`後に同じイベントを`resolved=True`で通知する。
- [ ] **Step 4: Run focused tests and full regression**
  - `python -m pytest tests/test_card_events.py -q`
  - `python -m pytest`
- [ ] **Step 5: Commit**
  - `feat: emit card action events`

### Task 3: Status/Summon側からカードイベントを利用できることを検証

**Files:**
- Modify: `tests/test_card_events.py`
- Possibly modify: `engine/statuses.py` only if the test exposes an actual API gap

**Interfaces:**
- Consumes: `CardActionEvent` via existing `StatusDefinition.on_event()` / `SummonDefinition.on_event()`.
- Produces: カードイベントを購読する効果の実装例と回帰テスト。

- [ ] **Step 1: Write a test Status that reacts only to the selected card**
  - `card_id`を確認し、`resolved=True`時だけ効果を実行する。
- [ ] **Step 2: Run test and confirm failure**
  - `python -m pytest tests/test_card_events.py -q`
- [ ] **Step 3: Implement only the minimal missing API, if any**
  - 既存`on_event()`で足りる場合はengine変更を追加しない。
- [ ] **Step 4: Run focused and full tests**
  - `python -m pytest tests/test_card_events.py -q`
  - `python -m pytest`
- [ ] **Step 5: Commit**
  - `test: verify status reactions to card events`

### Task 4: READMEと設計ドキュメントを更新

**Files:**
- Modify: `README.md`

**Interfaces:**
- Documents: CardActionEvent、カード使用前後通知、195件以上のテスト結果。

- [ ] **Step 1: Update implementation status**
  - キャラクターDefinitionをディルック・香菱・ガイアへ更新。
  - テスト件数を実測値へ更新。
  - カードイベント基盤を今後の実装項目から完了済み項目へ移す。
- [ ] **Step 2: Run full test suite**
  - `python -m pytest`
- [ ] **Step 3: Commit**
  - `docs: update README for card events`

### Task 5: 最終レビューと検証

- [ ] **Step 1: Fetch changed files and review diff**
- [ ] **Step 2: Run full test suite from project root**
  - `python -m pytest`
- [ ] **Step 3: Verify no card-specific branch was added to `Game`**
- [ ] **Step 4: Verify README matches actual implementation and test count**
- [ ] **Step 5: Record final verification evidence before claiming completion**
