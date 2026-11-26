import threading

import tkinter as tk
from tkinter import messagebox

import requests

API_URL = "https://api.github.com"


def get_json(url):
    """GET-запрос к GitHub API с обработкой ошибок. None при ошибке."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            return "not_found"
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Работа с GitHub API")
        self.geometry("780x520")

        tk.Label(self, text="GitHub API",
                 font=("Arial", 13, "bold")).pack(pady=4)

        top = tk.Frame(self)
        top.pack(pady=3)
        tk.Label(top, text="Имя пользователя / запрос:").pack(side="left")
        self.entry = tk.Entry(top, width=35)
        self.entry.pack(side="left", padx=5)
        self.entry.bind("<Return>", lambda event: self.show_profile())

        buttons = tk.Frame(self)
        buttons.pack(pady=3)
        tk.Button(buttons, text="Профиль пользователя",
                  command=self.show_profile).pack(side="left", padx=3)
        tk.Button(buttons, text="Репозитории пользователя",
                  command=self.show_repos).pack(side="left", padx=3)
        tk.Button(buttons, text="Поиск репозиториев",
                  command=self.search_repos).pack(side="left", padx=3)

        self.output = tk.Text(self, height=22, width=95, state="disabled")
        self.output.pack(pady=6, padx=10)

        self.status = tk.Label(self, text="", fg="gray")
        self.status.pack()

    def write(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def get_login(self):
        login = self.entry.get().strip()
        if not login:
            messagebox.showwarning("Внимание",
                                   "Введите имя пользователя или запрос.")
            return None
        return login

    def run_in_thread(self, func):
        self.status.configure(text="Загружаю данные...", fg="blue")
        self.clear()
        threading.Thread(target=func, daemon=True).start()

    def show_profile(self):
        login = self.get_login()
        if not login:
            return
        self.run_in_thread(lambda: self._profile(login))

    def _profile(self, login):
        user = get_json(f"{API_URL}/users/{login}")
        self.after(0, self._profile_done, user, login)

    def _profile_done(self, user, login):
        if user is None:
            self.status.configure(text="Ошибка соединения", fg="red")
            return
        if user == "not_found":
            self.status.configure(
                text=f"Пользователь {login} не найден", fg="red")
            return
        self.status.configure(text="Готово", fg="green")
        self.write("=== Профиль пользователя ===")
        self.write(f"Имя: {user.get('name') or 'не указано'}")
        self.write(f"Ссылка на профиль: {user.get('html_url')}")
        self.write(f"Количество репозиториев: {user.get('public_repos')}")
        self.write("Количество обсуждений: недоступно без токена доступа")
        self.write(f"Количество подписок: {user.get('following')}")
        self.write(f"Количество подписчиков: {user.get('followers')}")

    def show_repos(self):
        login = self.get_login()
        if not login:
            return
        self.run_in_thread(lambda: self._repos(login))

    def _repos(self, login):
        repos = get_json(f"{API_URL}/users/{login}/repos")
        self.after(0, self._repos_done, repos, login)

    def _repos_done(self, repos, login):
        if repos is None:
            self.status.configure(text="Ошибка соединения", fg="red")
            return
        if repos == "not_found":
            self.status.configure(
                text=f"Пользователь {login} не найден", fg="red")
            return
        if not repos:
            self.status.configure(
                text="У пользователя нет публичных репозиториев", fg="green")
            return
        self.status.configure(text=f"Найдено репозиториев: {len(repos)}",
                              fg="green")
        self.write(f"Репозитории пользователя {login}:")
        for repo in repos:
            # количество просмотров API не отдаёт, показываем звёзды
            self.write(
                f"- {repo['name']} | {repo['html_url']} | "
                f"звёзды: {repo['stargazers_count']} | "
                f"язык: {repo.get('language') or 'не указан'} | "
                f"видимость: {repo.get('visibility', 'public')} | "
                f"ветка по умолчанию: {repo.get('default_branch', 'main')}")

    def search_repos(self):
        query = self.entry.get().strip()
        if not query:
            messagebox.showwarning("Внимание",
                                   "Введите название для поиска.")
            return
        self.run_in_thread(lambda: self._search(query))

    def _search(self, query):
        data = get_json(
            f"{API_URL}/search/repositories?q={query}&per_page=10")
        self.after(0, self._search_done, data, query)

    def _search_done(self, data, query):
        if data is None:
            self.status.configure(text="Ошибка соединения", fg="red")
            return
        found = data.get("items", [])
        if not found:
            self.status.configure(text="Ничего не найдено", fg="red")
            return
        self.status.configure(text=f"Найдено: {data.get('total_count')}",
                              fg="green")
        self.write(f"Найдено репозиториев: {data.get('total_count')} "
                   f"(показаны первые {len(found)}):")
        for repo in found:
            self.write(f"- {repo['full_name']} | {repo['html_url']}")


if __name__ == "__main__":
    App().mainloop()
