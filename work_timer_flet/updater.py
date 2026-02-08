import flet as ft
import requests
from packaging.version import parse as parse_version
import asyncio

VERSION_URL = "https://raw.githubusercontent.com/dmitrimailov/worktime/main/version.json"

@ft.control("updater")
class Updater(ft.Control):
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
        # Атрибуты для хранения состояния обновления
        self.release_page_url = None
        self.update_dialog = None

    def build(self):
        # Этот контрол невидимый, поэтому возвращаем пустой контейнер
        return ft.Container()

    async def check_for_updates(self):
        """Асинхронно проверяет обновления и показывает диалог."""
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.get(VERSION_URL, timeout=10)
            )
            response.raise_for_status()
            remote_data = response.json()
            remote_version_str = remote_data.get("version")
            self.release_page_url = remote_data.get("url") # Сохраняем URL в self

            if not remote_version_str or not self.release_page_url:
                print("Ошибка в файле version.json")
                return

            if parse_version(remote_version_str) > parse_version(self.current_version):
                print(f"Доступна новая версия: {remote_version_str}")

                self.update_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Доступно обновление!"),
                    content=ft.Text(f"Обнаружена новая версия: {remote_version_str}.\n\nПерейти на страницу загрузки?"),
                    actions=[
                        ft.TextButton("Перейти", on_click=self.handle_open_url),
                        ft.TextButton("Позже", on_click=self.handle_close_dialog),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )

                # --- Атомарное обновление UI ---
                # 1. Готовим все изменения
                # 2. Применяем все изменения одним вызовом
                self.page.overlay.append(self.update_dialog)
                self.page.appbar.title = ft.Text(f"Work Timer v{self.current_version} (Найдено обновление!)")
                self.update_dialog.open = True
                self.page.update() 

        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")

    def handle_open_url(self, e):
        """Обработчик для кнопки 'Перейти'."""
        if self.release_page_url:
            # Запускаем асинхронную операцию открытия URL в фоновом режиме
            self.page.run_task(self._launch_url_task)
        self.handle_close_dialog(e)

    def handle_close_dialog(self, e):
        """Обработчик для кнопки 'Позже'."""
        if self.update_dialog in self.page.overlay:
            self.update_dialog.open = False
            self.page.update()

    async def _launch_url_task(self):
        """Асинхронная обертка для вызова launch_url."""
        # Используем современный способ через UrlLauncher, чтобы избежать DeprecationWarning
        await ft.UrlLauncher().launch_url(self.release_page_url)
