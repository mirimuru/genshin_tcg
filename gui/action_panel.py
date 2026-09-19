"""合法Actionの選択・詳細表示パネル。"""

import tkinter as tk
from tkinter import ttk


class ActionPanel(ttk.Frame):
    def __init__(self, master, on_execute):
        super().__init__(master, padding=6)
        self._on_execute = on_execute
        self.action_views = ()
        ttk.Label(self, text="合法Action").pack(anchor="w")
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(body, exportselection=False, height=16)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self._selection_changed)

        self.detail = tk.StringVar(value="Actionを選択してください")
        ttk.Label(self, textvariable=self.detail, justify="left", wraplength=360).pack(fill="x", pady=(6, 4))
        self.execute_button = ttk.Button(self, text="Action実行", command=self._execute_selected, state="disabled")
        self.execute_button.pack(anchor="e")

    def set_actions(self, action_views):
        self.action_views = tuple(action_views)
        self.listbox.delete(0, tk.END)
        for view in self.action_views:
            self.listbox.insert(tk.END, view.label)
        self.detail.set("Actionを選択してください")
        self.execute_button.configure(state="disabled")

    def _selection_changed(self, _event=None):
        selection = self.listbox.curselection()
        if not selection:
            self.detail.set("Actionを選択してください")
            self.execute_button.configure(state="disabled")
            return
        view = self.action_views[selection[0]]
        self.detail.set(
            f"Type: {view.action_type}\n"
            f"Player: P{view.player_id + 1}\n"
            f"Target: {view.target}\n"
            f"Cost: {view.cost}\n"
            f"Legal: {'YES' if view.legal else 'NO'}"
        )
        self.execute_button.configure(state="normal" if view.legal else "disabled")

    def _execute_selected(self):
        selection = self.listbox.curselection()
        if selection:
            self._on_execute(self.action_views[selection[0]].action)
