import json
import os
import threading

import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog as sd

import requests

URL = "https://www.cbr-xml-daily.ru/daily_json.js"
SAVE_FILE = "save.json"


def load_rates():
    """Получаем актуальные курсы с сайта ЦБ."""
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        return response.json()["Valute"]
    except requests.exceptions.RequestException:
        return {}


def rate_line(valute):
    return (f"{valute['CharCode']} ({valute['Name']}): "
            f"{valute['Value']:.4f} руб. за {valute['Nominal']} ед.")


def load_groups():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_groups(groups):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(groups, file, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Монитор курса валют (ЦБ РФ)")
        self.geometry("700x500")

        self.rates = {}
        self.groups = load_groups()

        tk.Label(self, text="Курсы валют ЦБ РФ",
                 font=("Arial", 13, "bold")).pack(pady=4)

        # Кнопки действий
        buttons = tk.Frame(self)
        buttons.pack(pady=3)
        tk.Button(buttons, text="Обновить курсы",
                  command=self.refresh).pack(side="left", padx=3)
        tk.Button(buttons, text="Все курсы",
                  command=self.show_all).pack(side="left", padx=3)
        tk.Button(buttons, text="Курс по коду",
                  command=self.show_one).pack(side="left", padx=3)
        tk.Button(buttons, text="Создать группу",
                  command=self.create_group).pack(side="left", padx=3)
        tk.Button(buttons, text="Добавить валюту в группу",
                  command=self.add_to_group).pack(side="left", padx=3)
        tk.Button(buttons, text="Удалить валюту из группы",
                  command=self.remove_from_group).pack(side="left", padx=3)
        tk.Button(buttons, text="Мои группы",
                  command=self.show_groups).pack(side="left", padx=3)

        self.output = tk.Text(self, height=18, width=80, state="disabled")
        self.output.pack(pady=6, padx=10)

        self.status = tk.Label(self, text="", fg="gray")
        self.status.pack()

        self.refresh()

    def write(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.configure(state="disabled")

    def refresh(self):
        self.status.configure(text="Загружаю курсы...", fg="blue")
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        rates = load_rates()
        self.after(0, self._loaded, rates)

    def _loaded(self, rates):
        if rates:
            self.rates = rates
            self.status.configure(
                text=f"Курсы обновлены: {len(rates)} валют",
                fg="green")
            self.show_all()
        else:
            self.status.configure(
                text="Ошибка: нет соединения с сайтом ЦБ", fg="red")

    def show_all(self):
        if not self.rates:
            messagebox.showwarning("Внимание", "Курсы не загружены.")
            return
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.write("Текущие курсы всех валют:")
        for valute in self.rates.values():
            self.write("  " + rate_line(valute))
        self.output.configure(state="disabled")

    def show_one(self):
        if not self.rates:
            messagebox.showwarning("Внимание", "Курсы не загружены.")
            return
        code = self.ask("Введите код валюты (например USD):")
        if code is None:
            return
        code = code.strip().upper()
        if code in self.rates:
            self.output.configure(state="normal")
            self.output.delete("1.0", "end")
            self.write(f"Курс {code}:")
            self.write("  " + rate_line(self.rates[code]))
            self.output.configure(state="disabled")
        else:
            messagebox.showerror("Ошибка",
                                 f"Валюта с кодом {code} не найдена.")

    def create_group(self):
        name = self.ask("Введите название группы:")
        if name is None or not name.strip():
            messagebox.showwarning("Внимание",
                                   "Название не может быть пустым.")
            return
        name = name.strip()
        if name in self.groups:
            messagebox.showerror("Ошибка",
                                 "Группа с таким названием уже есть.")
            return
        self.groups[name] = []
        if save_groups(self.groups):
            messagebox.showinfo("Готово", f"Группа '{name}' создана.")
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить файл.")

    def add_to_group(self):
        if not self.groups:
            messagebox.showwarning("Внимание", "Сначала создайте группу.")
            return
        name = self.ask("Введите название группы:")
        if name is None or name.strip() not in self.groups:
            messagebox.showerror("Ошибка", "Такой группы нет.")
            return
        name = name.strip()
        code = self.ask("Введите код валюты (например USD):")
        if code is None:
            return
        code = code.strip().upper()
        if code not in self.rates:
            messagebox.showerror("Ошибка", "Такой валюты нет в списке ЦБ.")
            return
        if code in self.groups[name]:
            messagebox.showwarning("Внимание",
                                   "Эта валюта уже есть в группе.")
            return
        self.groups[name].append(code)
        if save_groups(self.groups):
            messagebox.showinfo("Готово",
                                f"Валюта {code} добавлена в '{name}'.")
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить файл.")

    def remove_from_group(self):
        if not self.groups:
            messagebox.showwarning("Внимание", "Созданных групп пока нет.")
            return
        name = self.ask("Введите название группы:")
        if name is None or name.strip() not in self.groups:
            messagebox.showerror("Ошибка", "Такой группы нет.")
            return
        name = name.strip()
        code = self.ask("Введите код валюты для удаления:")
        if code is None:
            return
        code = code.strip().upper()
        if code not in self.groups[name]:
            messagebox.showerror("Ошибка", "Этой валюты нет в группе.")
            return
        self.groups[name].remove(code)
        if save_groups(self.groups):
            messagebox.showinfo("Готово",
                                f"Валюта {code} удалена из '{name}'.")
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить файл.")

    def show_groups(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        if not self.groups:
            self.write("Созданных групп пока нет.")
        else:
            self.write("Ваши группы валют:")
            for name, codes in self.groups.items():
                self.write(f"\nГруппа '{name}':")
                if not codes:
                    self.write("  (пусто)")
                    continue
                for code in codes:
                    if code in self.rates:
                        self.write("  " + rate_line(self.rates[code]))
                    else:
                        self.write(f"  {code}: курс недоступен")
        self.output.configure(state="disabled")

    def ask(self, text):
        """Окно ввода. Возвращает None, если нажали Отмена."""
        return sd.askstring("Ввод", text, parent=self)


if __name__ == "__main__":
    App().mainloop()
