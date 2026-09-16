# Character Effect Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CharacterDefinitionから共通Effect APIを利用してCharacter Status / Combat Status / Summonを扱えるようにし、固有効果を`engine/game.py`のキャラクター別分岐なしで実装できる基盤を作る。

**Architecture:** `Game`に状態効果追加用の小さな共通APIを追加し、既存の`_emit_event()`とStatus/SummonのDefinition/Instance設計をそのまま利用する。CharacterDefinitionは具体的な効果を呼び出す側、Gameは状態変更とイベント配送を担当する。

**Tech Stack:** Python 3.14, pytest 9.x, 既存の`engine.state`, `engine.statuses`, `engine.summons`, `engine.events`。

**Spec:** `docs/superpowers/specs/2026-09-17-character-effect-pipeline-design.md`

## Global Constraints

- Python 3.14を対象とする。
- 既存の166テストを壊さない。
- `engine/game.py`へキャラクターID/classによる固有処理分岐を追加しない。
- Character Status / Combat Status / Summonは既存のDefinition / Instance設計を利用する。
- 実際の七聖召喚の個別効果は、基盤完成後に個別ルールとテストを確認して追加する。

---

### Task 1: Character Status追加API

**Files:**
- Modify: `engine/game.py` — `Game`の状態効果API
- Test: `tests/test_effect_api.py` — Character Status追加と検証

**Interfaces:**
- Consumes: `StatusInstance`, `PlayerState.characters`。
- Produces: `Game.add_character_status(player_id: int, character_index: int, status: StatusInstance) -> StatusInstance`

- [ ] **Step 1: Write the failing test**

```python
from engine.events import EffectContext
from engine.game import Game
from engine.state import CharacterState, Element, GameState, PlayerState
from engine.statuses import StatusDefinition, StatusInstance


class TestCharacterStatus(StatusDefinition):
    status_id = "test_character_status"
    name = "テストCharacter Status"
    max_usages = 2


def make_game():
    players = [
        PlayerState(0, [CharacterState(f"P0-{i}", Element.PYRO) for i in range(3)]),
        PlayerState(1, [CharacterState(f"P1-{i}", Element.HYDRO) for i in range(3)]),
    ]
    return Game(GameState(players))


def test_add_character_status_to_specific_character():
    game = make_game()
    status = StatusInstance(TestCharacterStatus)

    result = game.add_character_status(0, 1, status)

    assert result is status
    assert game.state.players[0].characters[1].get_status("test_character_status") is status
    assert not game.state.players[0].characters[0].has_status("test_character_status")


def test_add_character_status_rejects_invalid_character_index():
    game = make_game()
    status = StatusInstance(TestCharacterStatus)

    try:
        game.add_character_status(0, 3, status)
    except ValueError as exc:
        assert "character_index" in str(exc)
    else:
        raise AssertionError("ValueErrorが発生していません")


def test_add_character_status_rejects_invalid_status_type():
    game = make_game()

    try:
        game.add_character_status(0, 0, object())
    except TypeError:
        pass
    else:
        raise AssertionError("TypeErrorが発生していません")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_effect_api.py -q`
Expected: FAIL because `Game.add_character_status` is not defined.

- [ ] **Step 3: Write minimal implementation**

```python
from engine.statuses import StatusInstance


def add_character_status(self, player_id: int, character_index: int, status: StatusInstance) -> StatusInstance:
    if player_id not in (0, 1):
        raise ValueError("player_id must be 0 or 1")
    player = self.state.players[player_id]
    if not 0 <= character_index < len(player.characters):
        raise ValueError("character_indexが不正です")
    if not isinstance(status, StatusInstance):
        raise TypeError("状態はStatusInstanceである必要があります")
    return player.characters[character_index].add_status(status)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_effect_api.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add engine/game.py tests/test_effect_api.py
git commit -m "feat: add character status effect API"
```

---

### Task 2: Combat Status / Summon追加API

**Files:**
- Modify: `engine/game.py` — Combat Status / Summon API
- Test: `tests/test_effect_api.py` — プレイヤー効果の追加と検証

**Interfaces:**
- Consumes: `StatusInstance`, `SummonInstance`, `PlayerState.add_combat_status`, `PlayerState.add_summon`。
- Produces: `Game.add_combat_status(player_id: int, status: StatusInstance) -> StatusInstance`; `Game.add_summon(player_id: int, summon: SummonInstance) -> SummonInstance`

- [ ] **Step 1: Write the failing test**

```python
from engine.summons import SummonDefinition, SummonInstance


class TestCombatStatus(StatusDefinition):
    status_id = "test_combat_status"
    name = "テストCombat Status"
    max_usages = 2


class TestSummon(SummonDefinition):
    summon_id = "test_summon"
    name = "テスト召喚物"
    max_usages = 2


def test_add_combat_status():
    game = make_game()
    status = StatusInstance(TestCombatStatus)

    assert game.add_combat_status(0, status) is status
    assert game.state.players[0].get_combat_status("test_combat_status") is status


def test_add_summon():
    game = make_game()
    summon = SummonInstance(TestSummon)

    assert game.add_summon(1, summon) is summon
    assert game.state.players[1].get_summon("test_summon") is summon
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_effect_api.py -q`
Expected: FAIL because the two `Game` methods are not defined.

- [ ] **Step 3: Write minimal implementation**

```python
from engine.summons import SummonInstance


def add_combat_status(self, player_id: int, status: StatusInstance) -> StatusInstance:
    if player_id not in (0, 1):
        raise ValueError("player_id must be 0 or 1")
    if not isinstance(status, StatusInstance):
        raise TypeError("状態はStatusInstanceである必要があります")
    return self.state.players[player_id].add_combat_status(status)


def add_summon(self, player_id: int, summon: SummonInstance) -> SummonInstance:
    if player_id not in (0, 1):
        raise ValueError("player_id must be 0 or 1")
    if not isinstance(summon, SummonInstance):
        raise TypeError("召喚物はSummonInstanceである必要があります")
    return self.state.players[player_id].add_summon(summon)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_effect_api.py -q`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add engine/game.py tests/test_effect_api.py
git commit -m "feat: add combat status and summon effect APIs"
```

---

### Task 3: Effect APIからのイベント配送テスト

**Files:**
- Modify: `tests/test_effect_api.py` — Status/Summonのイベント受信を追加
- Modify: `engine/game.py` — 必要な場合のみイベント配送APIを追加

**Interfaces:**
- Consumes: `Game._emit_event`, `StatusDefinition.on_event`, `SummonDefinition.on_event`。
- Produces: Effect APIで登録した状態が既存イベント配送経路から通知されること。

- [ ] **Step 1: Write the failing test**

```python
from dataclasses import dataclass
from engine.events import GameEvent


@dataclass
class TestEvent(GameEvent):
    value: int


class EventStatus(StatusDefinition):
    status_id = "event_status"
    name = "イベントテスト"
    max_usages = 1

    def on_event(self, instance, event, game, context):
        if isinstance(event, TestEvent):
            instance.consume()


def test_effect_added_through_api_receives_events_and_expires():
    game = make_game()
    status = StatusInstance(EventStatus)
    game.add_character_status(0, 0, status)

    game._emit_event(TestEvent(1))

    assert not game.state.players[0].characters[0].has_status("event_status")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_effect_api.py::test_effect_added_through_api_receives_events_and_expires -q`
Expected: FAIL only if the existing event/expiration path cannot satisfy the test.

- [ ] **Step 3: Write minimal implementation**

既存の`_emit_event()`でこのテストが通る場合、実装変更は行わない。通らない場合だけ、Status/Summonをイベント通知対象から除外している箇所を最小限修正する。

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_effect_api.py -q`
Expected: 全件 PASS。

- [ ] **Step 5: Commit**

```bash
git add tests/test_effect_api.py engine/game.py
git commit -m "test: verify effect API event delivery"
```

---

### Task 4: CharacterDefinitionからEffect APIを使う統合テスト

**Files:**
- Modify: `tests/test_character_definitions.py` — DefinitionからStatus/Summonを追加するテスト
- Modify: `content/characters/diluc.py` — 必要な統合例を追加する場合のみ

**Interfaces:**
- Consumes: Task 1-3の`Game.add_character_status`, `Game.add_combat_status`, `Game.add_summon`。
- Produces: CharacterDefinitionがGameの共通APIを利用できること。

- [ ] **Step 1: Write the failing test**

```python
class EffectfulCharacter(CharacterDefinition):
    character_id = "effectful_test"
    name = "効果テスト"
    element = Element.PYRO

    def elemental_skill(self, game, player_id: int) -> None:
        game.add_combat_status(player_id, StatusInstance(TestCombatStatus))
        game.deal_damage(player_id, 1 - player_id, 3, self.element)


def test_character_definition_can_use_effect_api():
    game = make_game_with_definition(EffectfulCharacter())
    game.elemental_skill(0)

    assert game.state.players[0].has_combat_status("test_combat_status")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_character_definitions.py -q`
Expected: FAIL if the test helper or Effect API integration is incomplete.

- [ ] **Step 3: Write minimal implementation**

Definition側から`game.add_combat_status(...)`を直接呼べるため、Game側にキャラクター固有分岐を追加しない。Task 1-2のAPIだけでテストを成立させる。

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_character_definitions.py -q`
Expected: 全件PASS。

- [ ] **Step 5: Commit**

```bash
git add tests/test_character_definitions.py content/characters/diluc.py
 git commit -m "test: integrate character definitions with effect API"
```

---

### Task 5: 全テスト・README更新

**Files:**
- Modify: `README.md` — キャラクター固有効果パイプラインの実装状況

**Interfaces:**
- Consumes: Tasks 1-4の完成状態。
- Produces: 現在のアーキテクチャとテスト件数をREADMEへ反映する。

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest`
Expected: 既存166件 + 新規テストが全件PASS。

- [ ] **Step 2: Update README**

以下の内容を追加する。

```markdown
| Character Effect API | 実装済み |
```

また、Definitionから共通Effect APIを利用し、`Game`にキャラクター別分岐を追加しない設計であることを「キャラクターDefinitionのアーキテクチャ」へ追記する。

- [ ] **Step 3: Run the full test suite again**

Run: `python -m pytest`
Expected: 全テストPASS。

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document character effect pipeline"
```

- [ ] **Step 5: Verify repository state**

Run: `git status --short`
Expected: 実装作業で意図しない未追跡・未コミット変更がないこと。
