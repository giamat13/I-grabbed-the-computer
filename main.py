import pyautogui
import tkinter as tk
from tkinter import font
import threading
import time
import sys

class ComputerCatcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("המחשב תפוס!")
        
        # הגדרות מסך מלא וביטחון
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#2c3e50")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Alt-F4>", lambda e: "break")
        
        self.locked = False
        self.password = ""
        self.child_name = ""
        self.remaining_seconds = 60 # דקה אחת לתגובה
        
        # פונטים לעיצוב
        self.header_font = font.Font(family="Arial", size=40, weight="bold")
        self.label_font = font.Font(family="Arial", size=18, weight="bold")
        
        self.setup_ui()

    def on_closing(self):
        # חוסם סגירה של החלון
        pass

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def setup_ui(self):
        self.clear_screen()
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(main_frame, text="🎮 תופסת מחשב 🎮", font=self.header_font, bg="#2c3e50", fg="#f1c40f").pack(pady=30)
        
        tk.Label(main_frame, text="איך קוראים לך?", font=self.label_font, bg="#2c3e50", fg="white").pack(pady=5)
        self.ent_name = tk.Entry(main_frame, width=20, font=("Arial", 20), justify="center")
        self.ent_name.pack(pady=10)
        
        tk.Label(main_frame, text="סיסמה סודית:", font=self.label_font, bg="#2c3e50", fg="white").pack(pady=5)
        self.ent_pass1 = tk.Entry(main_frame, width=20, show="*", font=("Arial", 20), justify="center")
        self.ent_pass1.pack(pady=10)
        
        tk.Label(main_frame, text="שוב סיסמה:", font=self.label_font, bg="#2c3e50", fg="white").pack(pady=5)
        self.ent_pass2 = tk.Entry(main_frame, width=20, show="*", font=("Arial", 20), justify="center")
        self.ent_pass2.pack(pady=10)
        
        tk.Button(main_frame, text="תפסתי את המחשב!", command=self.start_lock, bg="#27ae60", fg="white", font=("Arial", 20, "bold"), width=20, bd=0).pack(pady=40)

    def start_lock(self):
        p1 = self.ent_pass1.get()
        p2 = self.ent_pass2.get()
        if not p1 or p1 != p2: return
        
        self.child_name = self.ent_name.get() or "מישהו"
        self.password = p1
        self.locked = True
        
        # הפעלת נעילת עכבר וטיימר בדיקה ברקע
        threading.Thread(target=self.mouse_lock_loop, daemon=True).start()
        threading.Thread(target=self.cooldown_timer, daemon=True).start()
        self.show_locked_ui()

    def mouse_lock_loop(self):
        pyautogui.FAILSAFE = False
        while self.locked:
            try: 
                pyautogui.moveTo(0, 0)
            except: 
                pass
            time.sleep(0.02)

    def cooldown_timer(self):
        while self.locked:
            time.sleep(59 * 60) # המתנה של 59 דקות
            if self.locked:
                self.root.after(0, self.ask_still_needed)

    def ask_still_needed(self):
        self.remaining_seconds = 60 # איפוס הטיימר לדקה אחת
        
        self.ask_win = tk.Toplevel(self.root)
        self.ask_win.attributes("-topmost", True)
        self.ask_win.geometry("500x350")
        self.ask_win.overrideredirect(True) # ללא מסגרת חלון
        self.ask_win.configure(bg="#f39c12", highlightbackground="white", highlightthickness=3)
        
        # מרכוז החלון הקופץ
        x = (self.root.winfo_screenwidth() // 2) - 250
        y = (self.root.winfo_screenheight() // 2) - 175
        self.ask_win.geometry(f"+{x}+{y}")

        tk.Label(self.ask_win, text="עדיין פה?", font=("Arial", 30, "bold"), bg="#f39c12", fg="white").pack(pady=20)
        tk.Label(self.ask_win, text=f"{self.child_name}, המחשב עדיין תפוס?", font=("Arial", 16), bg="#f39c12", fg="white").pack()
        tk.Label(self.ask_win, text="הקש Y להמשך | הקש N לשחרור", font=("Arial", 14, "bold"), bg="#f39c12", fg="#2c3e50").pack(pady=15)
        
        self.timer_label = tk.Label(self.ask_win, text=f"המחשב ישתחרר בעוד: {self.remaining_seconds}", font=("Arial", 16, "bold"), bg="#f39c12", fg="#c0392b")
        self.timer_label.pack(pady=10)
        
        self.update_countdown()
        self.ask_win.bind("<Key>", self.handle_cooldown_input)
        self.ask_win.focus_set()

    def update_countdown(self):
        if hasattr(self, 'ask_win') and self.ask_win.winfo_exists():
            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
                self.timer_label.config(text=f"המחשב ישתחרר בעוד: {self.remaining_seconds}")
                self.root.after(1000, self.update_countdown)
            else:
                self.exit_program()

    def handle_cooldown_input(self, event):
        key = event.char.lower()
        if key in ['n', 'מ']:
            self.exit_program()
        else:
            # כל מקש אחר נחשב כאישור שהמחשב עדיין תפוס
            self.cancel_ask()

    def cancel_ask(self):
        if hasattr(self, 'ask_win'):
            self.ask_win.destroy()

    def show_locked_ui(self):
        self.clear_screen()
        self.root.configure(bg="#c0392b")
        lock_frame = tk.Frame(self.root, bg="#c0392b")
        lock_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(lock_frame, text="🚫 המחשב תפוס! 🚫", font=self.header_font, bg="#c0392b", fg="white").pack(pady=40)
        tk.Label(lock_frame, text=f"{self.child_name} תפס את המחשב!", font=("Arial", 30), bg="#c0392b", fg="#f1c40f").pack(pady=10)
        
        tk.Label(lock_frame, text="הקש סיסמה לשחרור:", font=self.label_font, bg="#c0392b", fg="white").pack(pady=10)
        
        self.key_var = tk.StringVar()
        self.key_var.trace_add("write", self.auto_check)
        self.ent_unlock = tk.Entry(lock_frame, textvariable=self.key_var, show="*", width=15, font=("Arial", 40), justify="center")
        self.ent_unlock.pack(pady=30)
        self.ent_unlock.focus_set()

    def auto_check(self, *args):
        if self.key_var.get() == self.password:
            self.exit_program()

    def exit_program(self):
        self.locked = False
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    app = ComputerCatcher()
    app.root.mainloop()