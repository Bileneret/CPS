import customtkinter as ctk
import subprocess, sys, os
from User import UserApp
from Manager import ManagerApp

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Вибір ролі")
        self.geometry("450x300")
        self.init_main_ui()

    def init_main_ui(self):
        self.clear_ui()

        ctk.CTkLabel(self, text="Виберіть роль", font=("Arial", 16)).pack(pady=20)

        ctk.CTkButton(self, text="Кабінет користувача", command=self.open_user_app).pack(pady=10)
        ctk.CTkButton(self, text="Менеджер-Адміністратор", command=self.open_manager_app).pack(pady=10)
        ctk.CTkButton(self, text="Тест", command=self.test_both).pack(pady=10)

    def open_user_app(self):
        # запускає UserApp у цьому процесі
        self.destroy()
        app = UserApp()
        app.mainloop()

    def open_manager_app(self):
        # запускає ManagerApp у цьому процесі
        self.destroy()
        app = ManagerApp()
        app.mainloop()

    def test_both(self):
        # запускаємо два окремі процеси: UserApp та ManagerApp
        base = os.path.dirname(__file__)
        python = sys.executable

        subprocess.Popen([python, os.path.join(base, 'User.py')])
        subprocess.Popen([python, os.path.join(base, 'Manager.py')])

        self.destroy()

    def clear_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
