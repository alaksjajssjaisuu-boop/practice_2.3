import tkinter as tk

import psutil


class MonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Системный монитор")
        self.geometry("420x260")
        self.resizable(False, False)

        tk.Label(self, text="Системный монитор",
                 font=("Arial", 14, "bold")).pack(pady=5)

        self.labels = {}
        for name in ("cpu", "mem", "disk"):
            self.labels[name] = tk.Label(self, text="...", font=("Consolas", 12),
                                         justify="left")
            self.labels[name].pack(pady=6, anchor="w", padx=30)

        self.button = tk.Button(self, text="Остановить мониторинг",
                                command=self.toggle, width=25)
        self.button.pack(pady=10)

        self.running = True
        self.update_data()
        # Обновление каждые 3 секунды
        self.after(3000, self.loop)

    def loop(self):
        if self.running:
            self.update_data()
        self.after(3000, self.loop)

    def update_data(self):
        cpu = psutil.cpu_percent(interval=0.2)
        memory = psutil.virtual_memory()
        mem_used = memory.used / (1024 ** 3)
        mem_total = memory.total / (1024 ** 3)
        disk = psutil.disk_usage("/")
        disk_used = disk.used / (1024 ** 3)
        disk_total = disk.total / (1024 ** 3)

        self.labels["cpu"].configure(text=f"Загрузка CPU: {cpu:.1f} %")
        self.labels["mem"].configure(
            text=(f"Оперативная память: {mem_used:.1f} ГБ из "
                  f"{mem_total:.1f} ГБ ({memory.percent:.1f} % занято)"))
        self.labels["disk"].configure(
            text=(f"Диск: {disk_used:.1f} ГБ из {disk_total:.1f} ГБ "
                  f"({disk.percent:.1f} % занято)"))

    def toggle(self):
        self.running = not self.running
        if self.running:
            self.button.configure(text="Остановить мониторинг")
            self.update_data()
        else:
            self.button.configure(text="Продолжить мониторинг")


if __name__ == "__main__":
    MonitorApp().mainloop()
