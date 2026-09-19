"""Tkinter製の七聖召喚デバッグ画面。"""

import tkinter as tk
from tkinter import messagebox, ttk

from gui.action_panel import ActionPanel
from gui.game_view import GuiController, default_game_factory


class DebugApp(tk.Tk):
    def __init__(self, controller=None):
        super().__init__()
        self.title("原神TCG Debug GUI")
        self.geometry("1200x800")
        self.minsize(980, 680)
        self.controller = controller or GuiController(default_game_factory)
        self._build()
        self.refresh()

    def _build(self):
        header = ttk.Frame(self, padding=(8, 6))
        header.pack(fill="x")
        ttk.Label(header, text="原神TCG Debug GUI", font=("TkDefaultFont", 16, "bold")).pack(side="left")
        self.phase_var = tk.StringVar()
        ttk.Label(header, textvariable=self.phase_var).pack(side="right", padx=8)
        ttk.Button(header, text="新しいゲーム", command=self._new_game).pack(side="right")

        main = ttk.Panedwindow(self, orient="vertical")
        main.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        upper = ttk.Panedwindow(main, orient="horizontal")
        main.add(upper, weight=4)
        lower = ttk.Frame(main, padding=4)
        main.add(lower, weight=2)

        self.state_text = tk.Text(upper, width=56, wrap="word", state="disabled", font=("TkFixedFont", 10))
        upper.add(self.state_text, weight=2)

        action_frame = ttk.Frame(upper)
        upper.add(action_frame, weight=3)
        self.action_panel = ActionPanel(action_frame, self._execute_action)
        self.action_panel.pack(fill="both", expand=True)

        ttk.Label(lower, text="Event Log").pack(anchor="w")
        log_frame = ttk.Frame(lower)
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, height=12, wrap="none", state="disabled", font=("TkFixedFont", 9))
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.error_var = tk.StringVar()
        ttk.Label(self, textvariable=self.error_var, foreground="red").pack(fill="x", padx=8, pady=(0, 6))

    def refresh(self):
        snapshot = self.controller.state_snapshot
        self.phase_var.set(
            f"Round {snapshot.round_number} / Phase {snapshot.phase} / Current Player P{snapshot.current_player + 1}"
        )
        self._set_text(self.state_text, self._state_text(snapshot))
        self.action_panel.set_actions(self.controller.action_views)
        self._set_text(self.log_text, "\n".join(self.controller.event_log.entries))
        self.log_text.see("end")
        self.error_var.set(self.controller.last_error or "")

    @staticmethod
    def _state_text(snapshot):
        lines = [
            "STATE INSPECTOR",
            f"Round: {snapshot.round_number}",
            f"Phase: {snapshot.phase}",
            f"Current Player: P{snapshot.current_player + 1}",
            f"Game Over: {snapshot.game_over}",
            f"Winner: {('P' + str(snapshot.winner + 1)) if snapshot.winner is not None else '-'}",
            "",
        ]
        for player in snapshot.players:
            lines.append(f"P{player.player_id + 1}  Active: Character {player.active_character_index + 1}  Shield: {player.shield}")
            dice = ", ".join(f"{name}×{count}" for name, count in player.dice if count)
            lines.append(f"  Dice: {dice or '-'}")
            for index, character in enumerate(player.characters):
                active = "*" if index == player.active_character_index else " "
                aura = character.aura or "なし"
                status = ", ".join(character.statuses) or "なし"
                lines.append(
                    f"  {active}C{index + 1} {character.name} [{character.element}] "
                    f"HP {character.hp}/{character.max_hp}  Energy {character.energy}/{character.max_energy}  Aura {aura}"
                )
                lines.append(f"     Status: {status}")
            if player.combat_statuses:
                lines.append(f"  Combat Status: {', '.join(player.combat_statuses)}")
            if player.summons:
                lines.append("  Summons: " + ", ".join(f"{name}×{usage}" for name, usage in player.summons))
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _set_text(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _execute_action(self, action):
        if not self.controller.execute_action(action):
            messagebox.showerror("Action Error", self.controller.last_error or "Actionの実行に失敗しました")
        self.refresh()

    def _new_game(self):
        self.controller.new_game()
        self.refresh()


def main():
    DebugApp().mainloop()


if __name__ == "__main__":
    main()
