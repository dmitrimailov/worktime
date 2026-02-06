import flet as ft
import requests
import threading
import json
from packaging.version import parse as parse_version
from pathlib import Path

class Updater:
    VERSION_URL = "https://raw.githubusercontent.com/dmitrimailov/worktime/main/version.json"
    
    def __init__(self, page: ft.Page, current_version: str):
        self.page = page
        self.current_version = current_version
        self.update_dialog = None

    def check_for_updates(self):
        """Проверяет наличие новой версии на GitHub в отдельном потоке."""
        thread = threading.Thread(target=self._check_worker, daemon=True)
        thread.start()

    def _check_worker(self):
        """Рабочая функция, выполняющая запрос и сравнение версий."""
        try:
            response = requests.get(self.VERSION_URL, timeout=10)
            response.raise_for_status()
            
            remote_data = response.json()
            remote_version_str = remote_data.get("version")
            apk_url = remote_data.get("url")

            if not remote_version_str or not apk_url:
                print("В удаленном файле версии отсутствуют необходимые ключи 'version' или 'url'.")
                return

            if parse_version(remote_version_str) > parse_version(self.current_version):
                print(f"Доступна новая версия: {remote_version_str}")
                # Показываем диалог обновления только на Android
                if self.page.platform == "android":
                    self.page.run_task(self.show_update_dialog, remote_version_str, apk_url)
                else:
                    print("Обновление доступно, но автоматическая установка поддерживается только на Android.")

        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")

    async def show_update_dialog(self, new_version, apk_url):
        """Показывает диалог обновления."""
        self.progress_ring = ft.ProgressRing()
        self.progress_text = ft.Text()

        self.update_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Доступно обновление!"),
            content=ft.Column([
                ft.Text(f"Обнаружена новая версия: {new_version}.\nХотите скачать и установить ее?"),
                self.progress_ring,
                self.progress_text,
            ], tight=True),
            actions=[
                ft.TextButton("Обновить", on_click=lambda e: self.start_download(apk_url)),
                ft.TextButton("Позже", on_click=self.close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = self.update_dialog
        self.update_dialog.open = True
        self.progress_ring.visible = False # Скрываем прогресс до начала загрузки
        self.page.update()

    def start_download(self, apk_url):
        """Запускает скачивание APK в отдельном потоке."""
        self.update_dialog.actions[0].disabled = True # Блокируем кнопку "Обновить"
        self.progress_ring.visible = True
        self.progress_text.value = "Скачивание..."
        self.page.update()

        thread = threading.Thread(target=self._download_worker, args=(apk_url,), daemon=True)
        thread.start()

    def _download_worker(self, apk_url):
        """Рабочая функция, скачивающая и запускающая установку APK."""
        try:
            # Используем временную директорию для сохранения файла
            download_path = Path(self.page.get_upload_url("update.apk", 600).split('?')[0])
            
            with requests.get(apk_url, stream=True) as r:
                r.raise_for_status()
                with open(download_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            print(f"Файл успешно скачан: {download_path}")
            self.page.run_task(self.launch_installer, str(download_path))

        except Exception as e:
            print(f"Ошибка при скачивании или установке: {e}")
            self.page.run_task(self.download_failed)

    async def launch_installer(self, file_path):
        """Запускает системный установщик."""
        self.progress_text.value = "Запуск установщика..."
        self.page.update()
        await self.page.launch_url(f"file://{file_path}")
        await self.close_dialog()

    async def download_failed(self):
        self.progress_text.value = "Ошибка скачивания!"
        self.progress_ring.visible = False
        self.update_dialog.actions[0].disabled = False
        self.page.update()

    async def close_dialog(self, e=None):
        if self.update_dialog:
            self.update_dialog.open = False
            self.page.update()