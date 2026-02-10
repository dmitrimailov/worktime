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
                    content=ft.Text(f"Обнаружена новая версия: {remote_version_str}.\n\nПерейти на страницу загрузки?"),
                    actions=[
                        ft.FilledButton("Обновить", on_click=self.handle_start_download),
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

    def handle_start_download(self, e):
        """Обработчик для кнопки 'Обновить'. Начинает загрузку APK."""
        # 1. Меняем вид диалогового окна на индикатор загрузки
        self.update_dialog.actions = [] # Убираем кнопки
        self.update_dialog.content = ft.Column([
            ft.Text("Идет загрузка обновления..."),
            ft.ProgressBar(width=400, color="amber", bgcolor="#eeeeee"),
        ])
        self.page.update()

        # 2. Запускаем асинхронную задачу загрузки
        self.page.run_task(self._download_and_install_task)

    def handle_close_dialog(self, e):
        """Обработчик для кнопки 'Позже'."""
        if self.update_dialog in self.page.overlay:
            self.update_dialog.open = False
            self.page.update()
    
    async def _download_and_install_task(self):
        """Асинхронная задача для загрузки и установки APK."""
        try:
            # 1. Определяем путь для сохранения файла
            # Используем FLET_APP_DATA_DIR, так как это гарантированно доступная для записи папка
            app_data_dir = os.getenv("FLET_APP_DATA_DIR")
            apk_path = os.path.join(app_data_dir, "update.apk")

            # 2. Скачиваем файл
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.get(self.apk_direct_url, stream=True, timeout=300)
            )
            response.raise_for_status()

            with open(apk_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Обновление успешно скачано в: {apk_path}")

            # 3. Запускаем системный установщик
            await ft.UrlLauncher().launch_url(f"file://{apk_path}")

            # 4. Закрываем диалог после запуска установщика
            self.handle_close_dialog(None)

        except Exception as e:
            print(f"Ошибка при загрузке обновления: {e}")
            self.update_dialog.content = ft.Text(f"Ошибка загрузки:\n{e}", max_lines=3)
            self.update_dialog.actions = [ft.TextButton("Закрыть", on_click=self.handle_close_dialog)]
            self.page.update()
