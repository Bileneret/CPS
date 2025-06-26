import customtkinter as ctk
from db import get_meter, save_meter_data_and_bill, get_meter_history, update_password
from datetime import datetime


class UserApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Кабінет користувача")
        self.geometry("450x500")

        self.logged_in = False
        self.meter_data = None

        self.init_login_ui()

    def init_login_ui(self):
        self.clear_ui()

        ctk.CTkLabel(self, text="Номер лічильника:").pack(pady=5)
        self.entry_id = ctk.CTkEntry(self)
        self.entry_id.pack()

        ctk.CTkLabel(self, text="Пароль:").pack(pady=5)
        self.entry_pass = ctk.CTkEntry(self, show="*")
        self.entry_pass.pack()

        ctk.CTkButton(self, text="Увійти", command=self.try_login).pack(pady=10)
        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack()

    def try_login(self):
        meter_id = self.entry_id.get().strip()
        password = self.entry_pass.get().strip()

        data = get_meter(meter_id)
        if data and data["password"] == password:
            self.meter_data = data
            self.logged_in = True
            self.show_main_menu()
        else:
            self.status_label.configure(text="Невірний логін або пароль", text_color="red")

    def show_main_menu(self):
        self.clear_ui()

        ctk.CTkLabel(self, text=f"Вітаємо! Ви залогінились за № {self.meter_data['meter_id']}",
                     font=("Arial", 16)).pack(pady=10)

        ctk.CTkButton(self, text="Історія", command=self.show_history).pack(pady=10)
        ctk.CTkButton(self, text="Нові показники", command=self.show_new_readings).pack(pady=10)
        ctk.CTkButton(self, text="Змінити пароль", command=self.change_password_ui).pack(pady=10)

    def show_history(self):
        self.clear_ui()

        history = get_meter_history(self.meter_data['meter_id'])

        ctk.CTkLabel(self, text="Історія показників", font=("Arial", 16)).pack(pady=5)
        text = ""
        for row in history:
            date = row['reading_time'].strftime("%Y-%m-%d")
            text += f"{date} | День: {row['day_value']} кВт | Ніч: {row['night_value']} кВт\n"

        ctk.CTkLabel(self, text=text, justify="left", wraplength=420).pack(pady=10)
        ctk.CTkButton(self, text="Назад", command=self.show_main_menu).pack(pady=10)

    def show_new_readings(self):
        self.clear_ui()

        ctk.CTkLabel(self, text="Нові денні показання:").pack()
        self.entry_day = ctk.CTkEntry(self)
        self.entry_day.pack()

        ctk.CTkLabel(self, text="Нові нічні показання:").pack()
        self.entry_night = ctk.CTkEntry(self)
        self.entry_night.pack()

        self.result_label = ctk.CTkLabel(self, text="")
        self.result_label.pack(pady=5)

        ctk.CTkButton(self, text="Оновити", command=self.submit_readings).pack(pady=10)
        ctk.CTkButton(self, text="Назад", command=self.show_main_menu).pack(pady=5)

    def submit_readings(self):
        try:
            new_day = float(self.entry_day.get())
            new_night = float(self.entry_night.get())
            prev_day = self.meter_data["day_value"]
            prev_night = self.meter_data["night_value"]

            if new_day < prev_day or new_night < prev_night:
                self.show_warning_popup(
                    "Показання не можуть бути меншими за попередні.\nБудь ласка, введіть коректні значення.")
                return

            result = save_meter_data_and_bill(self.meter_data["meter_id"], new_day, new_night)

            # Оновити локальні дані
            self.meter_data["day_value"] = new_day
            self.meter_data["night_value"] = new_night

            self.result_label.configure(text=result, text_color="green")
        except ValueError:
            self.result_label.configure(text="Некоректний ввід", text_color="red")
        except Exception as e:
            self.result_label.configure(text=f"Помилка: {e}", text_color="red")

    def show_warning_popup(self, message):
        popup = ctk.CTkToplevel(self)
        popup.title("Увага!")
        popup.geometry("300x150")
        popup.grab_set()

        ctk.CTkLabel(popup, text=message, wraplength=280, text_color="red").pack(pady=15)
        ctk.CTkButton(popup, text="ОК", command=popup.destroy).pack(pady=10)

    def change_password_ui(self):
        self.clear_ui()

        ctk.CTkLabel(self, text="Зміна паролю").pack(pady=10)

        ctk.CTkLabel(self, text="Старий пароль:").pack()
        self.old_pass_entry = ctk.CTkEntry(self, show="*")
        self.old_pass_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Новий пароль:").pack()
        self.new_pass_entry = ctk.CTkEntry(self, show="*")
        self.new_pass_entry.pack(pady=5)

        ctk.CTkButton(self, text="Змінити", command=self.submit_password_change).pack(pady=10)

        self.pass_change_status = ctk.CTkLabel(self, text="")
        self.pass_change_status.pack()

        ctk.CTkButton(self, text="Назад", command=self.show_main_menu).pack(pady=5)

    def submit_password_change(self):
        old = self.old_pass_entry.get()
        new = self.new_pass_entry.get()
        result = update_password(self.meter_data['meter_id'], old, new)
        self.pass_change_status.configure(text=result)

    def clear_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = UserApp()
    app.mainloop()