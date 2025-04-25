"""
Модуль для создания пользовательского интерфейса приложения.
"""

import tkinter as tk
import logging
from tkinter import ttk, messagebox
from utils import (
    toggle_ppe_list, toggle_pdf_visibility, create_invisible_scrolled_area,
    on_download_contract
)
from database import show_equipment, get_ppe_list, execute_query

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger('ui')

def create_ui(app):
    """Создание пользовательского интерфейса приложения."""
    _create_menu_bar(app)
    _create_ppe_list_frame(app)
    _create_details_frame(app)
    _create_pdf_frame(app)

def _create_menu_bar(app):
    """Создание меню-бара."""
    menubar = tk.Menu(app.root)
    app.root.config(menu=menubar)

    # Меню "Управление ППЭ"
    ppe_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Управление ППЭ", menu=ppe_menu)
    ppe_menu.add_command(label="Добавить ППЭ", command=app.add_ppe)
    ppe_menu.add_command(label="Редактировать ППЭ", command=app.edit_ppe)
    ppe_menu.add_command(label="Удалить ППЭ", command=app.delete_ppe)

    # Меню "Отображение"
    view_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Отображение", menu=view_menu)
    view_menu.add_command(
        label="Скрыть список ППЭ",
        command=lambda: toggle_ppe_list(app)
    )
    view_menu.add_command(
        label="Скрыть/Показать PDF",
        command=lambda: toggle_pdf_visibility(app)
    )

    # Меню "Действия"
    action_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Действия", menu=action_menu)
    action_menu.add_command(label="Обновить список ППЭ", command=lambda: refresh_ppe_list(app))
    action_menu.add_separator()
    action_menu.add_command(label="Просмотр договора", command=lambda: on_preview_contract_click(app))
    action_menu.add_command(label="Скачать договор", command=lambda: on_download_contract(app))

def _create_ppe_list_frame(app):
    """Создание фрейма для списка ППЭ."""
    app.frame_ppe_list = tk.Frame(app.root)
    app.frame_ppe_list.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    tk.Label(app.frame_ppe_list, text="Список ППЭ", font=("Arial", 14)).pack()
    
    # Создаем Treeview для списка ППЭ
    app.ppe_list = ttk.Treeview(
        app.frame_ppe_list,
        columns=("ppe_number", "ppe_address"),
        show="headings",
        height=35
    )
    app.ppe_list.heading("ppe_number", text="№ ППЭ")
    app.ppe_list.heading("ppe_address", text="Адрес ППЭ")
    app.ppe_list.column("ppe_number", width=80, anchor="center")
    app.ppe_list.column("ppe_address", width=400, anchor="w")
    
    # Привязываем обработчик двойного клика
    app.ppe_list.bind("<Double-1>", lambda e: show_ppe_details(app, e))

    # Добавляем полосу прокрутки
    scrollbar = ttk.Scrollbar(app.frame_ppe_list, orient="vertical", command=app.ppe_list.yview)
    app.ppe_list.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    
    app.ppe_list.pack(fill=tk.BOTH, expand=True)
    
    # Загружаем данные в список
    load_ppe_list(app)

def _create_details_frame(app):
    """Создание фрейма для отображения деталей ППЭ."""
    app.details_frame = tk.Frame(app.root)
    app.details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Создаем прокручиваемую область
    app.canvas = tk.Canvas(app.details_frame)
    app.scrollbar = tk.Scrollbar(app.details_frame, orient="vertical", command=app.canvas.yview)
    app.scrollable_frame = tk.Frame(app.canvas)

    # Настраиваем прокрутку
    app.scrollable_frame.bind(
        "<Configure>",
        lambda e: app.canvas.configure(scrollregion=app.canvas.bbox("all"))
    )

    app.canvas.create_window((0, 0), window=app.scrollable_frame, anchor="nw")
    app.canvas.configure(yscrollcommand=app.scrollbar.set)

    # Размещаем элементы
    app.canvas.pack(side="left", fill="both", expand=True)
    app.scrollbar.pack(side="right", fill="y")

def _create_pdf_frame(app):
    """Создание фрейма для отображения PDF с вертикальным скроллом."""
    app.pdf_frame = tk.Frame(app.root)
    app.pdf_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)

    # Создаем прокручиваемую область для PDF
    app.pdf_canvas = tk.Canvas(app.pdf_frame)
    app.pdf_scrollbar_y = ttk.Scrollbar(app.pdf_frame, orient="vertical", command=app.pdf_canvas.yview)
    app.pdf_canvas.configure(yscrollcommand=app.pdf_scrollbar_y.set)

    app.scrollable_pdf_frame = ttk.Frame(app.pdf_canvas)
    app.scrollable_pdf_frame.bind(
        "<Configure>",
        lambda e: app.pdf_canvas.configure(scrollregion=app.pdf_canvas.bbox("all"))
    )

    # Создаем область для кнопок управления PDF
    app.pdf_buttons_frame = ttk.Frame(app.pdf_frame)
    app.pdf_buttons_frame.pack(side="top", fill="x", padx=5, pady=5)

    # Размещаем элементы
    app.pdf_canvas.create_window((0, 0), window=app.scrollable_pdf_frame, anchor="nw")
    app.pdf_canvas.pack(side="left", fill=tk.BOTH, expand=True)
    app.pdf_scrollbar_y.pack(side="right", fill="y")

def load_ppe_list(app):
    """Загрузка списка ППЭ из базы."""
    try:
        rows = get_ppe_list()
        for row in rows:
            app.ppe_list.insert("", tk.END, values=row)
        logger.info(f"Загружено {len(rows)} записей ППЭ")
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка ППЭ: {e}")
        messagebox.showerror("Ошибка", f"Не удалось загрузить список ППЭ: {str(e)}")

def show_ppe_details(app, event):
    """Показ деталей ППЭ."""
    # Очищаем предыдущие данные
    for widget in app.scrollable_frame.winfo_children():
        widget.destroy()

    # Получаем выбранный элемент
    selected_item = app.ppe_list.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Выберите ППЭ для просмотра деталей.")
        return

    ppe_number, ppe_address = app.ppe_list.item(selected_item, "values")

    # Отображаем заголовок и адрес
    tk.Label(app.scrollable_frame, text=f"Детали ППЭ № {ppe_number}", font=("Arial", 16)).pack(anchor="w", pady=5)
    tk.Label(app.scrollable_frame, text=f"Адрес: {ppe_address}", font=("Arial", 14)).pack(anchor="w", pady=5)

    try:
        # Загружаем данные об оборудовании
        show_equipment(app, ppe_number)

        # Загружаем PDF
        from pdf_handler import show_ppe_pdf
        show_ppe_pdf(app, str(ppe_number))

        # Загружаем контракты
        from database import show_contracts
        show_contracts(app, ppe_number)
        
        logger.info(f"Загружены детали для ППЭ {ppe_number}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке деталей ППЭ {ppe_number}: {e}")
        messagebox.showerror("Ошибка", f"Не удалось загрузить детали ППЭ: {str(e)}")

def refresh_ppe_list(app):
    """Обновляет список ППЭ."""
    # Очищаем текущий список
    for item in app.ppe_list.get_children():
        app.ppe_list.delete(item)

    try:
        # Загружаем свежие данные
        load_ppe_list(app)
        messagebox.showinfo("Оповещение", "Список обновлён!")
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка ППЭ: {e}")
        messagebox.showerror("Ошибка", f"Не удалось обновить список ППЭ: {str(e)}")
