from ui import create_ui
from database import connect_to_database
import tkinter as tk
from tkinter import messagebox

class PPEApp:
    def __init__(self, root):
        self.root = root
        self._initialize_window()
        self.connection = connect_to_database()
        self._initialize_variables()

        # Заглушки для операций с ППЭ:
        # (Если нужно реальное добавление/редактирование/удаление в БД — сделайте в database.py)
    def add_ppe(self):
        messagebox.showinfo("Добавить ППЭ", "Функция добавления ППЭ в разработке.")

    def edit_ppe(self):
        messagebox.showinfo("Редактировать ППЭ", "Функция редактирования ППЭ в разработке.")

    def delete_ppe(self):
        messagebox.showinfo("Удалить ППЭ", "Функция удаления ППЭ в разработке.")

    def _initialize_window(self):
        """Настройка параметров главного окна приложения."""
        self.root.title("Список ППЭ")
        self.root.geometry("1920x1080")

    def _initialize_variables(self):
        """Инициализация переменных."""
        self.pdf_directory = "Z:\\_ГИА_2025\\Планы БТИ\\Планы"
        self.pdf_document = None
        self.current_pdf_path = ""
        self.ppe_list_visible = True

if __name__ == "__main__":
    app_root = tk.Tk()
    app = PPEApp(app_root)
    # Создаем UI после инициализации app
    create_ui(app)
    app_root.iconbitmap("icon.ico")
    app_root.mainloop()
