import importlib.util
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import font


# ── התקנת ספריות אוטומטית לפני הכל ──────────────────────────────────────────

# מיפוי: שם חבילה (pip) → שם מודול (import)
REQUIRED = {
    "pyautogui": "pyautogui",
    "Pillow":    "PIL",
}


# ── מסך טעינה ────────────────────────────────────────────────────────────────

class SplashScreen:
    """מסך טעינה עם קונסול מובנה."""

    STEPS = [
        "🔍 בודק ספריות...",
        "📦 מוריד חבילות...",
        "⚙️  מגדיר תצורה...",
        "🔐 בונה מנגנון נעילה...",
        "✅ הכל מוכן!",
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("טוען...")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#0d1117")
        # Alt+F4 מפורש — חייב ב-EXE כי fullscreen בולע את ברירת המחדל
        self.root.protocol("WM_DELETE_WINDOW", lambda: sys.exit())
        self.root.bind_all("<Alt-F4>", lambda e: sys.exit())

        self._done = False
        self._console_visible = False

        self._build_ui()
        threading.Thread(target=self._run_install, daemon=True).start()
        self.root.after(100, self._tick_animation)
        self.root.mainloop()

    # ── בנית ממשק ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        sw = self.root.winfo_screenwidth()

        title_font = font.Font(family="Arial", size=52, weight="bold")
        sub_font   = font.Font(family="Arial", size=20)
        step_font  = font.Font(family="Arial", size=16)
        bar_font   = font.Font(family="Arial", size=13)

        # אזור תוכן ראשי
        self.main_frame = tk.Frame(self.root, bg="#0d1117")
        self.main_frame.pack(fill="both", expand=True)

        center = tk.Frame(self.main_frame, bg="#0d1117")
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text="🎮", font=font.Font(size=72),
                 bg="#0d1117", fg="#f1c40f").pack(pady=(0, 10))
        tk.Label(center, text="תופסת מחשב", font=title_font,
                 bg="#0d1117", fg="#f1c40f").pack()
        tk.Label(center, text="מכין את הכלים...", font=sub_font,
                 bg="#0d1117", fg="#8b949e").pack(pady=(8, 30))

        self.step_label = tk.Label(center, text=self.STEPS[0], font=step_font,
                                   bg="#0d1117", fg="#58a6ff", width=36)
        self.step_label.pack(pady=(0, 14))

        BAR_W, BAR_H = min(sw - 120, 560), 14
        self.bar_canvas = tk.Canvas(center, width=BAR_W, height=BAR_H,
                                    bg="#0d1117", highlightthickness=0)
        self.bar_canvas.pack()
        r = BAR_H // 2
        self._rounded_rect(self.bar_canvas, 0, 0, BAR_W, BAR_H, r, fill="#21262d")
        self._fill_id = self.bar_canvas.create_rectangle(0, 0, 0, BAR_H, fill="#238636", outline="")
        self._bar_w = BAR_W

        self.pct_label = tk.Label(center, text="0%", font=bar_font,
                                  bg="#0d1117", fg="#8b949e")
        self.pct_label.pack(pady=(6, 0))

        self.dots_label = tk.Label(center, text="",
                                   font=font.Font(family="Arial", size=24),
                                   bg="#0d1117", fg="#f1c40f")
        self.dots_label.pack(pady=(20, 0))
        self._dot_tick = 0

        # קונסול (נסתר בהתחלה, pack לפני הסרגל)
        self.console_frame = tk.Frame(self.root, bg="#0d1117")
        console_header = tk.Frame(self.console_frame, bg="#161b22")
        console_header.pack(fill="x")
        tk.Label(console_header, text="▶ Console Output", bg="#161b22", fg="#58a6ff",
                 font=("Courier", 10, "bold")).pack(side="left", padx=8, pady=3)
        self.console_text = tk.Text(
            self.console_frame, bg="#0d1117", fg="#c9d1d9",
            font=("Courier", 10), relief="flat", state="disabled", height=8
        )
        self.console_text.pack(fill="both", expand=True, padx=4, pady=4)

        # סרגל תחתון
        self.bottom_bar = tk.Frame(self.root, bg="#161b22")
        self.bottom_bar.pack(fill="x", side="bottom")

        tk.Button(self.bottom_bar, text="SHOW CONSOLE",
                  command=self._toggle_console,
                  bg="#21262d", fg="#8b949e",
                  font=("Courier", 9), relief="flat", cursor="hand2",
                  padx=8, pady=4).pack(side="left", padx=6, pady=4)

        tk.Button(self.bottom_bar, text="✕ יציאה",
                  command=lambda: sys.exit(),
                  bg="#3a1a1a", fg="#ff6b6b",
                  font=("Courier", 9, "bold"), relief="flat", cursor="hand2",
                  padx=8, pady=4).pack(side="left", padx=2, pady=4)

        # הפנה stdout לקונסול
        sys.stdout = self
        sys.stderr = self

    def write(self, msg):
        # חייב לעבור דרך after — tkinter לא thread-safe!
        try:
            self.root.after(0, self._write_safe, msg)
        except Exception:
            pass

    def _write_safe(self, msg):
        try:
            self.console_text.configure(state="normal")
            self.console_text.insert("end", msg)
            self.console_text.see("end")
            self.console_text.configure(state="disabled")
        except Exception:
            pass

    def flush(self):
        pass

    def _toggle_console(self):
        self._console_visible = not self._console_visible
        if self._console_visible:
            self.console_frame.pack(fill="x", side="bottom", before=self.bottom_bar)
        else:
            self.console_frame.pack_forget()

    @staticmethod
    def _rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1,
        ]
        canvas.create_polygon(points, smooth=True, **kwargs)

    def _set_progress(self, pct: float, step_idx: int):
        fill_w = int(self._bar_w * pct)
        self.bar_canvas.coords(self._fill_id, 0, 0, fill_w, 14)
        self.step_label.config(text=self.STEPS[min(step_idx, len(self.STEPS)-1)])
        self.pct_label.config(text=f"{int(pct*100)}%")

    def _tick_animation(self):
        if self._done:
            return
        self._dot_tick += 1
        self.dots_label.config(text="●" * (self._dot_tick % 4))
        self.root.after(300, self._tick_animation)

    def _run_install(self):
        steps_count = len(REQUIRED) + 2
        self.root.after(0, lambda: self._set_progress(0.05, 0))
        time.sleep(0.5)

        for i, (pkg, mod) in enumerate(REQUIRED.items()):
            if importlib.util.find_spec(mod) is not None:
                print(f"✓ {pkg} כבר מותקן — דילוג\n")
            else:
                print(f"📦 מתקין {pkg}...\n")
                self.root.after(0, lambda s=1+i: self._set_progress((1+i)/steps_count, s))
                # ב-EXE מקומפל sys.executable הוא ה-EXE עצמו — חייב למצוא python אמיתי
                import shutil
                if getattr(sys, "frozen", False):
                    py = shutil.which("python") or shutil.which("python3") or shutil.which("py")
                    if not py:
                        print(f"✗ לא נמצא Python — לא ניתן להתקין {pkg}\n")
                        continue
                else:
                    py = sys.executable
                proc = subprocess.Popen(
                    [py, "-m", "pip", "install", pkg],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
                for line in proc.stdout:
                    print(line, end="")
                proc.wait()
                if proc.returncode == 0:
                    print(f"\n✓ {pkg} הותקן בהצלחה\n")
                else:
                    print(f"\n✗ שגיאה בהתקנת {pkg}\n")
            pct = (i + 1) / steps_count
            self.root.after(0, lambda p=pct, s=1+i: self._set_progress(p, s))
            time.sleep(0.4)

        for extra_pct, step_i, delay in [(0.88, 3, 0.5), (1.0, 4, 0.5)]:
            time.sleep(delay)
            self.root.after(0, lambda p=extra_pct, s=step_i: self._set_progress(p, s))

        time.sleep(0.7)
        self._done = True
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.root.after(0, self.root.destroy)


# ── האפליקציה הראשית ──────────────────────────────────────────────────────────

class ComputerCatcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("המחשב תפוס!")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#2c3e50")

        self.locked = False
        self.password = ""
        self.child_name = ""
        self.remaining_seconds = 60
        self._console_visible = False

        self.header_font = font.Font(family="Arial", size=40, weight="bold")
        self.label_font  = font.Font(family="Arial", size=18, weight="bold")

        # התחלה לא נעולה
        self._apply_unlocked_mode()
        self.setup_ui()

    # ── מצבי נעילה ───────────────────────────────────────────────────────────

    def _apply_unlocked_mode(self):
        """מסכי הגדרה – Alt+F4 ומעבר חלונות חופשיים."""
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self.root.unbind("<Alt-F4>")
        self.root.attributes("-topmost", False)

    def _apply_locked_mode(self):
        """מסך נעול – חוסם הכל."""
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.bind("<Alt-F4>", lambda e: "break")
        self.root.attributes("-topmost", True)

    def _quit(self):
        self.root.destroy()
        sys.exit()

    def clear_screen(self):
        for w in self.root.winfo_children():
            w.destroy()
        self._console_visible = False

    # ── סרגל תחתון עם קונסול ─────────────────────────────────────────────────

    def _build_bottom_bar(self, show_exit=True):
        """בונה סרגל תחתון + קונסול מובנה."""
        # קונסול (נסתר)
        self.console_frame = tk.Frame(self.root, bg="#0d1117")
        ch = tk.Frame(self.console_frame, bg="#161b22")
        ch.pack(fill="x")
        tk.Label(ch, text="▶ Console Output", bg="#161b22", fg="#58a6ff",
                 font=("Courier", 10, "bold")).pack(side="left", padx=8, pady=3)
        self.console_text = tk.Text(
            self.console_frame, bg="#0d1117", fg="#c9d1d9",
            font=("Courier", 10), relief="flat", state="disabled", height=8
        )
        self.console_text.pack(fill="both", expand=True, padx=4, pady=4)

        # סרגל
        self.bottom_bar = tk.Frame(self.root, bg="#161b22")
        self.bottom_bar.pack(fill="x", side="bottom")

        tk.Button(self.bottom_bar, text="SHOW CONSOLE",
                  command=self._toggle_console,
                  bg="#21262d", fg="#8b949e",
                  font=("Courier", 9), relief="flat", cursor="hand2",
                  padx=8, pady=4).pack(side="left", padx=6, pady=4)

        if show_exit:
            tk.Button(self.bottom_bar, text="✕ יציאה",
                      command=self._quit,
                      bg="#3a1a1a", fg="#ff6b6b",
                      font=("Courier", 9, "bold"), relief="flat", cursor="hand2",
                      padx=8, pady=4).pack(side="left", padx=2, pady=4)

    def _toggle_console(self):
        self._console_visible = not self._console_visible
        if self._console_visible:
            self.console_frame.pack(fill="x", side="bottom", before=self.bottom_bar)
        else:
            self.console_frame.pack_forget()

    # ── מסך הכניסה ────────────────────────────────────────────────────────────

    def setup_ui(self):
        self.clear_screen()
        self.root.configure(bg="#2c3e50")
        self._apply_unlocked_mode()

        main = tk.Frame(self.root, bg="#2c3e50")
        main.pack(fill="both", expand=True)

        frame = tk.Frame(main, bg="#2c3e50")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="🎮 תופסת מחשב 🎮",
                 font=self.header_font, bg="#2c3e50", fg="#f1c40f").pack(pady=30)
        tk.Label(frame, text="איך קוראים לך?",
                 font=self.label_font, bg="#2c3e50", fg="white").pack(pady=5)
        self.ent_name = tk.Entry(frame, width=20, font=("Arial", 20), justify="center")
        self.ent_name.pack(pady=10)
        tk.Label(frame, text="סיסמה סודית:",
                 font=self.label_font, bg="#2c3e50", fg="white").pack(pady=5)
        self.ent_pass1 = tk.Entry(frame, width=20, show="*", font=("Arial", 20), justify="center")
        self.ent_pass1.pack(pady=10)
        tk.Label(frame, text="שוב סיסמה:",
                 font=self.label_font, bg="#2c3e50", fg="white").pack(pady=5)
        self.ent_pass2 = tk.Entry(frame, width=20, show="*", font=("Arial", 20), justify="center")
        self.ent_pass2.pack(pady=10)
        tk.Button(frame, text="תפסתי את המחשב!", command=self.start_lock,
                  bg="#27ae60", fg="white", font=("Arial", 20, "bold"),
                  width=20, bd=0).pack(pady=40)

        self._build_bottom_bar(show_exit=True)

    # ── נעילה ────────────────────────────────────────────────────────────────

    def start_lock(self):
        p1 = self.ent_pass1.get()
        p2 = self.ent_pass2.get()
        if not p1 or p1 != p2:
            return
        self.child_name = self.ent_name.get() or "מישהו"
        self.password = p1
        self.locked = True
        self._apply_locked_mode()
        threading.Thread(target=self.mouse_lock_loop, daemon=True).start()
        threading.Thread(target=self.cooldown_timer,  daemon=True).start()
        self.show_locked_ui()

    def mouse_lock_loop(self):
        import pyautogui
        pyautogui.FAILSAFE = False
        while self.locked:
            try:
                pyautogui.moveTo(0, 0)
            except Exception:
                pass
            time.sleep(0.02)

    def cooldown_timer(self):
        while self.locked:
            time.sleep(59 * 60)
            if self.locked:
                self.root.after(0, self.ask_still_needed)

    # ── חלון "עדיין פה?" ──────────────────────────────────────────────────────

    def ask_still_needed(self):
        self.remaining_seconds = 60
        self.ask_win = tk.Toplevel(self.root)
        self.ask_win.attributes("-topmost", True)
        self.ask_win.overrideredirect(True)
        self.ask_win.configure(bg="#f39c12", highlightbackground="white", highlightthickness=3)
        x = (self.root.winfo_screenwidth()  // 2) - 250
        y = (self.root.winfo_screenheight() // 2) - 150
        self.ask_win.geometry(f"500x300+{x}+{y}")

        tk.Label(self.ask_win, text="עדיין פה?",
                 font=("Arial", 30, "bold"), bg="#f39c12", fg="white").pack(pady=20)
        tk.Label(self.ask_win, text=f"{self.child_name}, המחשב עדיין תפוס?",
                 font=("Arial", 16), bg="#f39c12", fg="white").pack()
        tk.Label(self.ask_win, text="הקש Y להמשך | הקש N לשחרור",
                 font=("Arial", 14, "bold"), bg="#f39c12", fg="#2c3e50").pack(pady=15)
        self.timer_label = tk.Label(self.ask_win,
                                    text=f"המחשב ישתחרר בעוד: {self.remaining_seconds}",
                                    font=("Arial", 16, "bold"), bg="#f39c12", fg="#c0392b")
        self.timer_label.pack(pady=10)

        self.update_countdown()
        self.ask_win.bind("<Key>", self.handle_cooldown_input)
        self.ask_win.focus_set()

    def update_countdown(self):
        if hasattr(self, "ask_win") and self.ask_win.winfo_exists():
            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
                self.timer_label.config(text=f"המחשב ישתחרר בעוד: {self.remaining_seconds}")
                self.root.after(1000, self.update_countdown)
            else:
                self.exit_program()

    def handle_cooldown_input(self, event):
        if event.char.lower() in ["n", "מ"]:
            self.exit_program()
        else:
            self.cancel_ask()

    def cancel_ask(self):
        if hasattr(self, "ask_win"):
            self.ask_win.destroy()

    # ── מסך נעול ─────────────────────────────────────────────────────────────

    def show_locked_ui(self):
        self.clear_screen()
        self.root.configure(bg="#c0392b")

        main = tk.Frame(self.root, bg="#c0392b")
        main.pack(fill="both", expand=True)

        frame = tk.Frame(main, bg="#c0392b")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="🚫 המחשב תפוס! 🚫",
                 font=self.header_font, bg="#c0392b", fg="white").pack(pady=40)
        tk.Label(frame, text=f"{self.child_name} תפס את המחשב!",
                 font=("Arial", 30), bg="#c0392b", fg="#f1c40f").pack(pady=10)
        tk.Label(frame, text="הקש סיסמה לשחרור:",
                 font=self.label_font, bg="#c0392b", fg="white").pack(pady=10)

        self.key_var = tk.StringVar()
        self.key_var.trace_add("write", self.auto_check)
        self.ent_unlock = tk.Entry(frame, textvariable=self.key_var, show="*",
                                   width=15, font=("Arial", 40), justify="center")
        self.ent_unlock.pack(pady=30)
        self.ent_unlock.focus_set()

        # סרגל תחתון: רק SHOW CONSOLE, ללא יציאה
        self._build_bottom_bar(show_exit=False)

    def auto_check(self, *args):
        if self.key_var.get() == self.password:
            self.exit_program()

    # ── יציאה ────────────────────────────────────────────────────────────────

    def exit_program(self):
        self.locked = False
        self.root.destroy()
        sys.exit()


# ── נקודת כניסה ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SplashScreen()
    app = ComputerCatcher()
    app.root.mainloop()