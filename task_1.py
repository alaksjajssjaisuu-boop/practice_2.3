import tkinter as tk
from tkinter import messagebox
import threading

import requests

# Сайты из задания 2.2
URLS = [
    "https://github.com/",
    "https://www.binance.com/en",
    "https://tomtit.tomsk.ru/",
    "https://jsonplaceholder.typicode.com/",
    "https://moodle.tomtit-tomsk.ru/",
]

HEADERS = {"User-Agent": "Mozilla/5.0"}


def status_text(code):
    """Переводим код ответа в понятный статус."""
    if 200 <= code < 300:
        return "доступен"
    if code in (401, 403):
        return "вход запрещен"
    if code == 404:
        return "не найден"
    return "не доступен"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Проверка доступности сайтов")
        self.geometry("650x400")

        tk.Label(self, text="Список сайтов из задания",
                 font=("Arial", 12, "bold")).pack(pady=5)

        # Список сайтов с чекбоксами — можно выбрать, какие проверять
        self.vars = {}
        box = tk.Frame(self)
        box.pack(pady=5)
        for url in URLS:
            var = tk.BooleanVar(value=True)
            self.vars[url] = var
            tk.Checkbutton(box, text=url, variable=var, anchor="w",
                           width=45).pack(anchor="w")

        self.button = tk.Button(self, text="Проверить сайты",
                                command=self.start_check, width=20,
                                bg="#4CAF50", fg="white")
        self.button.pack(pady=8)

        self.output = tk.Text(self, height=12, width=80, state="disabled")
        self.output.pack(pady=5, padx=10)

    def write(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def start_check(self):
        selected = [url for url, var in self.vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("Внимание", "Выберите хотя бы один сайт.")
            return
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")
        self.button.configure(state="disabled", text="Проверяю...")
        # Проверяем в отдельном потоке, чтобы окно не зависало
        threading.Thread(target=self.check_all, args=(selected,),
                         daemon=True).start()

    def check_all(self, urls):
        results = []
        for url in urls:
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                line = f"{url} – {status_text(response.status_code)} – {response.status_code}"
            except requests.exceptions.Timeout:
                line = f"{url} – не доступен – нет ответа (таймаут)"
            except requests.exceptions.ConnectionError:
                line = f"{url} – не доступен – нет соединения с сайтом"
            except requests.exceptions.RequestException as error:
                line = f"{url} – не доступен – ошибка запроса ({error})"
            results.append(line)
        # Вывод в интерфейс делаем в главном потоке
        self.after(0, self.show_results, results)

    def show_results(self, results):
        for line in results:
            self.write(line)
        self.button.configure(state="normal", text="Проверить сайты")


if __name__ == "__main__":
    App().mainloop()
