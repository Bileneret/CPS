import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from db import get_all_meters, get_meter_history, add_meter, delete_meter


class ManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Менеджер-Адміністратор")
        self.geometry("600x500")

        self.admin_password = "123123"
        self.init_login_ui()

    def init_login_ui(self):
        self.clear_ui()
        ctk.CTkLabel(self, text="Вхід для адміністратора", font=("Arial", 16)).pack(pady=10)
        self.pass_entry = ctk.CTkEntry(self, show="*")
        self.pass_entry.pack(pady=5)
        ctk.CTkButton(self, text="Увійти", command=self.try_login).pack(pady=10)
        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack()

    def try_login(self):
        if self.pass_entry.get() == self.admin_password:
            self.show_main_menu()
        else:
            self.status_label.configure(text="Невірний пароль", text_color="red")

    def show_main_menu(self):
        self.clear_ui()
        ctk.CTkLabel(self, text="Панель адміністратора", font=("Arial", 16)).pack(pady=10)

        table_frame = self.create_meter_table()
        table_frame.pack(pady=10, fill="both", expand=True)

        ctk.CTkButton(self, text="Переглянути історію", command=self.display_selected_meter_history).pack(pady=5)
        ctk.CTkButton(self, text="Видалити лічильник", command=self.delete_selected_meter).pack(pady=5)
        ctk.CTkButton(self, text="Додати лічильник", command=self.add_meter_ui).pack(pady=5)
        ctk.CTkButton(self, text="Редагувати тарифи", command=self.edit_tariffs_ui).pack(pady=5)

    def edit_tariffs_ui(self):
        from db import get_tariffs, update_tariff

        self.clear_ui()
        ctk.CTkLabel(self, text="Редагування тарифів", font=("Arial", 16)).pack(pady=10)

        tariffs = get_tariffs()

        self.day_tariff_entry = ctk.CTkEntry(self, placeholder_text="Тариф день")
        self.day_tariff_entry.insert(0, str(tariffs["day_tariff"]))
        self.day_tariff_entry.pack(pady=5)

        self.night_tariff_entry = ctk.CTkEntry(self, placeholder_text="Тариф ніч")
        self.night_tariff_entry.insert(0, str(tariffs["night_tariff"]))
        self.night_tariff_entry.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack()

        def save():
            try:
                update_tariff("day_tariff", float(self.day_tariff_entry.get()))
                update_tariff("night_tariff", float(self.night_tariff_entry.get()))
                self.status_label.configure(text="Тарифи оновлено", text_color="green")
            except Exception as e:
                self.status_label.configure(text=f"Помилка: {e}", text_color="red")

        ctk.CTkButton(self, text="Зберегти", command=save).pack(pady=5)
        ctk.CTkButton(self, text="Назад", command=self.show_main_menu).pack(pady=5)


    def create_meter_table(self):
        meters = get_all_meters()

        frame = tk.Frame(self)
        columns = ("meter_id", "day_value", "night_value")

        self.meter_table = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        self.meter_table.heading("meter_id", text="ID")
        self.meter_table.heading("day_value", text="День")
        self.meter_table.heading("night_value", text="Ніч")

        for meter in meters:
            self.meter_table.insert("", "end", values=(meter["meter_id"], meter["day_value"], meter["night_value"]))

        self.meter_table.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.meter_table.yview)
        scrollbar.pack(side="right", fill="y")
        self.meter_table.configure(yscrollcommand=scrollbar.set)

        return frame

    def display_selected_meter_history(self):
        selected = self.meter_table.selection()
        if not selected:
            return
        item = self.meter_table.item(selected[0])
        meter_id = item["values"][0]

        history = get_meter_history(meter_id)
        self.clear_ui()
        ctk.CTkLabel(self, text=f"Історія для лічильника {meter_id}", font=("Arial", 16)).pack(pady=5)

        text = ""
        for row in history:
            date = row['reading_time'].strftime("%Y-%m-%d")
            text += f"{date} | День: {row['day_value']} | Ніч: {row['night_value']}\n"

        ctk.CTkLabel(self, text=text, justify="left", wraplength=550).pack(pady=10)

        ctk.CTkButton(self, text="Очистити історію", command=lambda: self.clear_meter_history_ui(meter_id)).pack(pady=5)
        ctk.CTkButton(self, text="Назад", command=self.show_main_menu).pack(pady=5)


    def delete_selected_meter(self):
        selected = self.meter_table.selection()
        if not selected:
            return
        item = self.meter_table.item(selected[0])
        meter_id = item["values"][0]

        try:
            delete_meter(meter_id)
            self.show_main_menu()
        except Exception as e:
            self.clear_ui()
            ctk.CTkLabel(self, text=f"Помилка: {e}", text_color="red").pack(pady=5)
            ctk.CTkButton(self, text="Назад", command=self.show_main_menu).pack(pady=5)

    def add_meter_ui(self):
        self.clear_ui()
        ctk.CTkLabel(self, text="Додати новий лічильник").pack(pady=5)

        self.new_id = ctk.CTkEntry(self, placeholder_text="ID")
        self.new_id.pack()
        self.new_pass = ctk.CTkEntry(self, placeholder_text="Пароль")
        self.new_pass.pack()
        self.new_day = ctk.CTkEntry(self, placeholder_text="Денні показання")
        self.new_day.pack()
        self.new_night = ctk.CTkEntry(self, placeholder_text="Нічні показання")
        self.new_night.pack()

        self.status = ctk.CTkLabel(self, text="")
        self.status.pack()

        ctk.CTkButton(self, text="Додати", command=self.submit_add_meter).pack(pady=5)
        ctk.CTkButton(self, text="Назад", command=self.show_main_menu).pack()

    def submit_add_meter(self):
        try:
            existing_ids = [m["meter_id"] for m in get_all_meters()]
            if self.new_id.get() in existing_ids:
                self.status.configure(text="Такий ID вже існує", text_color="red")
                return

            add_meter(
                self.new_id.get(),
                self.new_pass.get(),
                float(self.new_day.get()),
                float(self.new_night.get())
            )
            self.status.configure(text="Лічильник додано", text_color="green")
        except Exception as e:
            self.status.configure(text=f"Помилка: {e}", text_color="red")

    def clear_meter_history_ui(self, meter_id):
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Підтвердження")
        confirm_window.geometry("300x150")
        confirm_window.grab_set()

        ctk.CTkLabel(confirm_window, text=f"Очистити історію лічильника {meter_id}?", font=("Arial", 14)).pack(pady=20)

        def confirm():
            try:
                from db import clear_meter_history
                clear_meter_history(meter_id)
                confirm_window.destroy()

                # Після очищення історії — показати знову історію, оновлену
                self.show_main_menu()
                self.display_specific_meter_history(meter_id)
            except Exception as e:
                confirm_window.destroy()
                self.clear_ui()
                ctk.CTkLabel(self, text=f"Помилка при очищенні: {e}", text_color="red").pack(pady=5)
                ctk.CTkButton(self, text="Назад", command=self.show_main_menu).pack(pady=5)

        ctk.CTkButton(confirm_window, text="Так, очистити", command=confirm).pack(pady=5)
        ctk.CTkButton(confirm_window, text="Скасувати", command=confirm_window.destroy).pack(pady=5)


    def display_specific_meter_history(self, meter_id):
        history = get_meter_history(meter_id)
        self.clear_ui()
        ctk.CTkLabel(self, text=f"Історія для лічильника {meter_id}", font=("Arial", 16)).pack(pady=5)

        text = ""
        for row in history:
            date = row['reading_time'].strftime("%Y-%m-%d")
            text += f"{date} | День: {row['day_value']} | Ніч: {row['night_value']}\n"

        ctk.CTkLabel(self, text=text, justify="left", wraplength=550).pack(pady=10)

        ctk.CTkButton(self, text="Очистити історію", command=lambda: self.clear_meter_history_ui(meter_id)).pack(pady=5)
        ctk.CTkButton(self, text="Назад", command=self.show_main_menu).pack(pady=5)


    def clear_ui(self):
        for widget in self.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    app = ManagerApp()
    app.mainloop()
