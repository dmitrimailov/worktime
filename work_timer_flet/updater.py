import flet as ft
import requests
from packaging.version import parse as parse_version
import asyncio
import os

# URL для проверки версии и получения прямой ссылки на APK
VERSION_URL = "https://raw.githubusercontent.com/dmitrimailov/worktime/main/version.json"

@ft.control("updater")
class Updater(ft.Control):
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
        # Атрибуты для хранения состояния обновления
        self.release_page_url = None
        self.apk_direct_url = None # Прямая ссылка на APK
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
            # Сохраняем обе ссылки: на страницу релиза и прямую на APK
            self.release_page_url = remote_data.get("url") 
            self.apk_direct_url = remote_data.get("apk_url")

            if not remote_version_str or not self.apk_direct_url:
                print("Ошибка в файле version.json: отсутствует 'version' или 'apk_url'")
                return

            if parse_version(remote_version_str) > parse_version(self.current_version):
                print(f"Доступна новая версия: {remote_version_str}")

                self.update_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Доступно обновление!"),
                    content=ft.Text(f"Обнаружена новая версия: {remote_version_str}.\n\nНачать загрузку?"),
                    actions=[
                        ft.FilledButton("Загрузить", on_click=self.handle_open_download_url),
                        ft.TextButton("Позже", on_click=self.handle_close_dialog),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )

                # --- Атомарное обновление UI ---
                # 1. Готовим все изменения
                # 2. Применяем все изменения одним вызовом
                self.page.overlay.append(self.update_dialog)
                self.update_dialog.open = True
                self.page.update() 

        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")

    def handle_close_dialog(self, e):
        """Обработчик для кнопки 'Позже'."""
        if self.update_dialog:
            self.update_dialog.open = False
            self.page.update()
    
    async def handle_open_download_url(self, e):
        """Обработчик для кнопки 'Загрузить'. Открывает прямую ссылку на APK."""
        if self.apk_direct_url:
            await self.page.launch_url(self.apk_direct_url)
            # Сразу закрываем диалог, так как дальнейшие действия происходят в браузере
            self.handle_close_dialog(None)
