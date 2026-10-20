from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass, field


CommandCallback = Callable[[str], None]
CancelCallback = Callable[[], None]


@dataclass
class CommandState:
    active_command: str | None = None
    prompt: str = "Comando:"
    history: list[str] = field(default_factory=list)
    on_confirm: CommandCallback | None = None
    on_cancel: CancelCallback | None = None

    @property
    def active(self) -> bool:
        return self.active_command is not None


class CadInteractionController:
    """Controlador único de interação CAD.

    Toda ferramenta deve chamar ``begin`` ao iniciar uma operação. O Enter confirma
    exatamente a operação ativa e o Esc cancela exatamente a operação ativa.
    O estado é limpo antes de executar callbacks, permitindo que o callback abra a
    próxima etapa com outro ``begin`` sem herdar estado antigo.
    """

    def __init__(self, app: tk.Tk) -> None:
        self.app = app
        self.state = CommandState()
        self.last_command: str | None = None
        self._build_console()
        self._build_context_menu()
        self._bind_global_keys()
        self.write("Pronto. Selecione uma ferramenta ou digite um comando.")

    def _build_console(self) -> None:
        self.console = tk.Frame(self.app, bg="#1f2329", bd=0, highlightthickness=0)
        self.console.pack(side="bottom", fill="x")

        self.history_text = tk.Text(
            self.console,
            height=3,
            bg="#1f2329",
            fg="#d8dee9",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            pady=4,
            font=("Consolas", 9),
            wrap="word",
        )
        self.history_text.pack(fill="x")
        self.history_text.configure(state="disabled")

        row = tk.Frame(self.console, bg="#111418")
        row.pack(fill="x")
        self.prompt_var = tk.StringVar(value="Comando:")
        self.prompt_label = tk.Label(
            row,
            textvariable=self.prompt_var,
            bg="#111418",
            fg="#9ecbff",
            padx=8,
            font=("Consolas", 10, "bold"),
        )
        self.prompt_label.pack(side="left")

        self.command_var = tk.StringVar()
        self.entry = tk.Entry(
            row,
            textvariable=self.command_var,
            bg="#111418",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            font=("Consolas", 10),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Escape>", self._on_escape)

    def _build_context_menu(self) -> None:
        self.context = tk.Menu(self.app, tearoff=False)
        self.context.add_command(label="Confirmar", command=self.confirm)
        self.context.add_command(label="Cancelar", command=self.cancel)
        self.context.add_separator()
        self.context.add_command(label="Repetir último comando", command=self.repeat_last)
        self.context.add_command(label="Focar linha de comando", command=self.focus_console)

    def _bind_global_keys(self) -> None:
        self.app.bind_all("<Return>", self._on_global_enter, add="+")
        self.app.bind_all("<KP_Enter>", self._on_global_enter, add="+")
        self.app.bind_all("<Escape>", self._on_global_escape, add="+")
        self.app.bind_all("<Button-3>", self._on_right_click, add="+")
        self.app.bind_all("<Control-l>", lambda _e: self.focus_console(), add="+")

    def write(self, message: str) -> None:
        message = str(message).strip()
        if not message:
            return
        self.state.history.append(message)
        self.history_text.configure(state="normal")
        self.history_text.insert("end", message + "\n")
        self.history_text.see("end")
        self.history_text.configure(state="disabled")

    def begin(
        self,
        command: str,
        prompt: str,
        *,
        on_confirm: CommandCallback | None = None,
        on_cancel: CancelCallback | None = None,
        default: str = "",
        focus: bool = True,
    ) -> None:
        if self.state.active:
            self.write(f"{self.state.active_command}: substituído por {command}.")
        self.state.active_command = command
        self.state.prompt = prompt
        self.state.on_confirm = on_confirm
        self.state.on_cancel = on_cancel
        self.last_command = command
        self.prompt_var.set(prompt)
        self.command_var.set(default)
        self.write(f"{command}: {prompt}")
        if focus:
            self.focus_console(select_all=bool(default))

    def update_prompt(self, prompt: str, default: str | None = None, *, focus: bool = False) -> None:
        self.state.prompt = prompt
        self.prompt_var.set(prompt)
        if default is not None:
            self.command_var.set(default)
        if focus:
            self.focus_console(select_all=default is not None)

    def _clear_active_state(self) -> tuple[str | None, CommandCallback | None, CancelCallback | None]:
        command = self.state.active_command
        confirm_cb = self.state.on_confirm
        cancel_cb = self.state.on_cancel
        self.state.active_command = None
        self.state.on_confirm = None
        self.state.on_cancel = None
        self.state.prompt = "Comando:"
        self.prompt_var.set("Comando:")
        return command, confirm_cb, cancel_cb

    def confirm(self) -> None:
        value = self.command_var.get().strip()
        if not self.state.active:
            self.command_var.set("")
            if value:
                self.write(f"Comando > {value}")
                self._execute_builtin(value)
            return

        command, callback, _ = self._clear_active_state()
        shown = value or "<Enter>"
        self.write(f"{command} > {shown}")
        self.command_var.set("")

        if callback is not None:
            callback(value)

    def cancel(self) -> None:
        if not self.state.active:
            self.command_var.set("")
            self.prompt_var.set("Comando:")
            return

        command, _, callback = self._clear_active_state()
        self.command_var.set("")
        self.write(f"{command}: *Cancelado*")
        if callback is not None:
            callback()
        try:
            self.app.focus_set()
        except tk.TclError:
            pass

    def complete(self, message: str | None = None) -> None:
        command, _, _ = self._clear_active_state()
        self.command_var.set("")
        if message:
            self.write(message)
        elif command:
            self.write(f"{command}: concluído.")

    def repeat_last(self) -> None:
        if self.state.active:
            self.focus_console()
            return
        if self.last_command:
            self.command_var.set(self.last_command)
            self.focus_console(select_all=True)
            return
        self.focus_console()

    def focus_console(self, select_all: bool = False) -> None:
        self.entry.focus_set()
        if select_all:
            self.entry.selection_range(0, "end")
            self.entry.icursor("end")

    def _execute_builtin(self, value: str) -> None:
        cmd = value.strip().upper()
        if not cmd:
            return
        aliases = {
            "ESC": self.cancel,
            "CANCEL": self.cancel,
            "CANCELAR": self.cancel,
            "PREVIEW": getattr(self.app, "open_preview", lambda: None),
            "VIDEO": getattr(self.app, "start_video", lambda: None),
            "ANALISAR": getattr(self.app, "start_analysis", lambda: None),
        }
        action = aliases.get(cmd)
        if action:
            action()
        else:
            self.write(f"Comando desconhecido: {value}")

    def _on_enter(self, _event: tk.Event) -> str:
        self.confirm()
        return "break"

    def _on_escape(self, _event: tk.Event) -> str:
        self.cancel()
        return "break"

    def _on_global_enter(self, event: tk.Event) -> str | None:
        if event.widget is self.entry:
            return None
        if self.state.active:
            self.confirm()
            return "break"
        return None

    def _on_global_escape(self, _event: tk.Event) -> str:
        self.cancel()
        return "break"

    def _on_right_click(self, event: tk.Event) -> None:
        try:
            self.context.tk_popup(event.x_root, event.y_root)
        finally:
            self.context.grab_release()


def install_cad_interactions(app: tk.Tk) -> CadInteractionController:
    existing = getattr(app, "cad", None)
    if isinstance(existing, CadInteractionController):
        return existing
    controller = CadInteractionController(app)
    setattr(app, "cad", controller)
    return controller
