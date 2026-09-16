# イベント駆動型キャラクター固有効果 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** キャラクター固有効果を `Game` のキャラクターID分岐なしでイベント駆動に拡張できる基盤を実装し、異なるタイプのリファレンスキャラクターを1体追加する。

**Architecture:** 既存の `GameEvent` / `StatusDefinition.on_event()` / `StatusDefinition.modify_damage()` を維持し、攻撃開始・解決、切り替え、ダメージ、Energyのイベント境界を追加する。固有効果はCharacterDefinitionとStatus/Combat Status/Summonに閉じ込め、`engine/game.py` にはキャラクター固有IDの分岐を追加しない。

**Tech Stack:** Python 3.14、pytest 9、既存の `engine` アーキテクチャ。

**Spec:** `docs/superpowers/specs/2026-09-17-event-driven-character-effects-design.md`

## Global Constraints

- 既存179テストを回帰テストとして維持する。
- `engine/game.py` にキャラクターID依存の固有効果分岐を追加しない。
- `StatusDefinition.on_event()` をStatusの主イベントAPIとして維持する。
- `StatusInstance.data` を一時状態・カウンタの保存先として利用する。
- `_emit_event()` のスナップショット性を維持する。
- CPU探索、GUI、全キャラクター・全カード実装は今回の対象外。

---

### Task 1: 攻撃・切り替えイベントのモデル追加

**Files:**
- Modify: `engine/events.py`
- Modify: `engine/game.py`
- Test: `tests/test_events.py`

**Interfaces:**
- Produces `ActionEvent` 系イベントと、攻撃開始・解決およびキャラクター切り替えをStatusから観測できる境界。

- [ ] **Step 1: Write the failing tests**

```python
def test_normal_attack_emits_start_and_resolved_events(game, recorder):
    recorder.attach(game, player_id=0)
    game.normal_attack(0)
    assert recorder.events == ["normal_attack_start", "normal_attack_resolved"]


def test_character_switch_emits_switch_event(game, recorder):
    recorder.attach(game, player_id=0)
    game.switch_character(0, 1)
    assert recorder.events == ["character_switch"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_events.py -v`
Expected: FAIL because the new event types and emission points do not exist.

- [ ] **Step 3: Write minimal implementation**

`engine/events.py` に攻撃種別と切り替えを表現するイベントを追加し、`Game.normal_attack()`、`Game.elemental_skill()`、`Game.elemental_burst()`、キャラクター切り替え処理の既存解決順序を壊さない位置でイベントをemitする。イベントには `player_id` と `character_index` を保持する。

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_events.py -v`
Expected: PASS。

- [ ] **Step 5: Run regression tests**

Run: `python -m pytest`
Expected: 既存テストを含め全件PASS。

- [ ] **Step 6: Commit**

```bash
git add engine/events.py engine/game.py tests/test_events.py
git commit -m "feat: add action and switch events"
```

---

### Task 2: Statusイベントの選択的トリガーとデータ保持を検証

**Files:**
- Modify: `tests/test_events.py`
- Modify: `engine/statuses.py` only if the focused tests expose a missing API requirement

**Interfaces:**
- Consumes `Game._emit_event()` and `StatusInstance.data`.
- Produces regression coverage proving event filtering, usage consumption, and snapshot behavior.

- [ ] **Step 1: Write failing tests**

```python
def test_status_reacts_only_to_matching_event(game):
    status = StatusInstance(AttackCounter)
    game.add_character_status(0, 0, status)
    game.normal_attack(0)
    assert status.data["count"] == 1
    game.change_energy(0, 0, 1, "test")
    assert status.data["count"] == 1


def test_status_added_during_event_is_not_reentered(game):
    parent = StatusInstance(AddChildStatusOnAttack)
    game.add_character_status(0, 0, parent)
    game.normal_attack(0)
    child = game.state.players[0].active_character.get_status("child")
    assert child is not None
    assert child.data["count"] == 0
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_events.py -v`
Expected: FAIL until the test fixtures and event filtering behavior are aligned with the current implementation.

- [ ] **Step 3: Implement only missing behavior**

`StatusInstance.data` の既存仕様を維持し、必要な場合のみイベントの種別判定をStatusDefinition側へ追加する。`_emit_event()` のスナップショット取得を変更しない。

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_events.py -v`
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add tests/test_events.py engine/statuses.py
 git commit -m "test: cover selective status event handling"
```

---

### Task 3: ダメージ・Energyイベント境界を固定する

**Files:**
- Modify: `tests/test_damage.py`
- Modify: `tests/test_energy.py` if present; otherwise create it
- Modify: `engine/game.py` only where event ordering is incorrect

**Interfaces:**
- Consumes `DamageEvent` and `EnergyEvent`.
- Produces tests proving pre/post event order and resolved amount semantics.

- [ ] **Step 1: Write failing tests**

```python
def test_damage_event_is_emitted_before_and_after_damage(game):
    recorder = EventRecorder()
    recorder.attach(game, 0)
    game.deal_damage(0, 1, 2, Element.PYRO)
    assert recorder.damage_amounts == [(2, False), (2, True)]


def test_energy_event_reports_actual_clamped_change(game):
    character = game.state.players[0].characters[0]
    character.energy = character.max_energy - 1
    events = EventRecorder()
    events.attach(game, 0)
    game.change_energy(0, 0, 2, "test")
    assert events.energy_amounts == [(2, False), (1, True)]
```

- [ ] **Step 2: Run focused tests**

Run: `python -m pytest tests/test_damage.py tests/test_energy.py -v`
Expected: FAIL if current ordering or assertions differ from the design.

- [ ] **Step 3: Implement minimal corrections**

`Game.deal_damage()` と `Game.change_energy()` のイベント境界を設計書の順序に合わせる。既存の反応計算・ダメージ量・Energy上下限処理は変更しない。

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_damage.py tests/test_energy.py -v`
Expected: PASS。

- [ ] **Step 5: Run full regression**

Run: `python -m pytest`
Expected: 全件PASS。

- [ ] **Step 6: Commit**

```bash
git add engine/game.py tests/test_damage.py tests/test_energy.py
git commit -m "test: lock damage and energy event ordering"
```

---

### Task 4: 第2リファレンスキャラクターの公式仕様確認とDefinition実装

**Files:**
- Create: `content/characters/<reference_character>.py`
- Modify: `content/characters/__init__.py`
- Modify: `tests/test_<reference_character>.py`
- Modify: `engine/characters.py` only if registry integration requires it

**Interfaces:**
- Produces a registered `CharacterDefinition` whose attacks, costs, Energy, and unique effects are expressed through existing event/status APIs.

- [ ] **Step 1: Add failing behavior tests**

```python
def test_reference_character_basic_attack_and_cost(game):
    character = create_reference_character()
    game.state.players[0].characters[0] = character.create_state()
    assert character.normal_attack_cost == EXPECTED_NORMAL_ATTACK_COST
    assert character.elemental_skill_cost == EXPECTED_SKILL_COST
    assert character.elemental_burst_cost == EXPECTED_BURST_COST


def test_reference_character_unique_effect(game):
    # 公式仕様で定めた発動条件を1つの再現可能なシナリオで検証する。
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_<reference_character>.py -v`
Expected: FAIL because the character definition does not yet exist.

- [ ] **Step 3: Confirm current official card data before implementation**

公式・信頼できるカードデータで通常攻撃、元素スキル、元素爆発、各コスト、Energy、固有効果を確認し、テストの期待値を確定する。

- [ ] **Step 4: Implement the Definition and effect classes**

CharacterDefinitionから既存のGame APIを呼び、固有効果はStatus/Combat Status/Summonへ委譲する。`game.py` にキャラクターID分岐を追加しない。

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/test_<reference_character>.py -v`
Expected: PASS。

- [ ] **Step 6: Commit**

```bash
git add content/characters tests/test_<reference_character>.py engine/characters.py
git commit -m "feat: add second reference character"
```

---

### Task 5: READMEと最終回帰確認

**Files:**
- Modify: `README.md`

**Interfaces:**
- Documents the event-driven effect layer and the second reference character.

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest`
Expected: 新規テストを含め全件PASS、警告なし。

- [ ] **Step 2: Update README**

イベント駆動型キャラクター固有効果、追加イベント、リファレンスキャラクター、最新テスト件数を進捗欄へ反映する。

- [ ] **Step 3: Verify README and repository files**

GitHub上で変更後のREADME、設計書、実装ファイルを再取得し、内容が一致することを確認する。

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: update event-driven effects progress"
```
