import tkinter as tk
from tkinter import ttk, messagebox
from utils import toggle_ppe_list, toggle_pdf_visibility, create_invisible_scrolled_area
from database import show_equipment
from pdf_handler import show_ppe_pdf, show_fullscreen_image
# show_contracts, load_equipment_data можно тоже импортировать при необходимости

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
        command=lambda: toggle_ppe_list(app)  # Из utils.py
    )
    view_menu.add_command(
        label="Скрыть/Показать PDF",
        command=lambda: toggle_pdf_visibility(app)  # Из utils.py
    )

    refresh_menu = tk.Menu(menubar,tearoff=0)
    menubar.add_cascade(label="Действия", menu=refresh_menu)
    refresh_menu.add_command(label="Обновить список ППЭ", command=lambda: refresh_ppe_list(app))

def _create_ppe_list_frame(app):
    """Создание фрейма для списка ППЭ."""
    app.frame_ppe_list = tk.Frame(app.root)
    app.frame_ppe_list.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    tk.Label(app.frame_ppe_list, text="Список ППЭ", font=("Arial", 14)).pack()
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
    # Вместо app.show_ppe_details -> свободная функция show_ppe_details(app, event)
    app.ppe_list.bind("<Double-1>", lambda e: show_ppe_details(app, e))

    app.ppe_list.pack(fill=tk.BOTH, expand=True)
    load_ppe_list(app)  # Так как load_ppe_list - свободная функция ниже

def _create_details_frame(app):
    """Создание фрейма для отображения деталей ППЭ."""
    app.details_frame = tk.Frame(app.root)
    app.details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    app.canvas = tk.Canvas(app.details_frame)
    app.scrollbar = tk.Scrollbar(app.details_frame, orient="vertical", command=app.canvas.yview)
    app.scrollable_frame = tk.Frame(app.canvas)

    app.scrollable_frame.bind(
        "<Configure>",
        lambda e: app.canvas.configure(scrollregion=app.canvas.bbox("all"))
    )

    app.canvas.create_window((0, 0), window=app.scrollable_frame, anchor="nw")
    app.canvas.configure(yscrollcommand=app.scrollbar.set)

    app.canvas.pack(side="left", fill="both", expand=True)
    app.scrollbar.pack(side="right", fill="y")

def _create_pdf_frame(app):
    """Создание фрейма для отображения PDF с вертикальным скроллом."""
    app.pdf_frame = tk.Frame(app.root)
    app.pdf_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)

    app.pdf_canvas = tk.Canvas(app.pdf_frame)
    app.pdf_scrollbar_y = ttk.Scrollbar(app.pdf_frame, orient="vertical", command=app.pdf_canvas.yview)
    app.pdf_canvas.configure(yscrollcommand=app.pdf_scrollbar_y.set)

    app.scrollable_pdf_frame = ttk.Frame(app.pdf_canvas)
    app.scrollable_pdf_frame.bind(
        "<Configure>",
        lambda e: app.pdf_canvas.configure(scrollregion=app.pdf_canvas.bbox("all"))
    )

    app.pdf_canvas.create_window((0, 0), window=app.scrollable_pdf_frame, anchor="nw")
    app.pdf_canvas.pack(side="left", fill=tk.BOTH, expand=True)
    app.pdf_scrollbar_y.pack(side="right", fill="y")

def load_ppe_list(app):
    """Загрузка списка ППЭ из базы"""
    cursor = app.connection.cursor()
    cursor.execute("SELECT ppe_number, ppe_address FROM dat_ppe ORDER BY ppe_number")
    rows = cursor.fetchall()
    for row in rows:
        app.ppe_list.insert("", tk.END, values=row)

def show_ppe_details(app, event):
    """Показ деталей ППЭ"""
    for widget in app.scrollable_frame.winfo_children():
        widget.destroy()

    selected_item = app.ppe_list.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Выберите ППЭ для просмотра деталей.")
        return

    ppe_number, ppe_address = app.ppe_list.item(selected_item, "values")

    tk.Label(app.scrollable_frame, text=f"Детали ППЭ № {ppe_number}", font=("Arial", 16)).pack(anchor="w", pady=5)
    tk.Label(app.scrollable_frame, text=f"Адрес: {ppe_address}", font=("Arial", 14)).pack(anchor="w", pady=5)

    # Создаем вкладки
    equipment_tabs = ttk.Notebook(app.scrollable_frame)
    equipment_tabs.pack(fill=tk.BOTH, expand=True)

    # Для вкладки "Оборудование"
    equipment_tab = ttk.Frame(equipment_tabs)
    equipment_tabs.add(equipment_tab, text="Оборудование")

    # Создаем "скрытый" скролл
    canvas_equipment, frame_equipment = create_invisible_scrolled_area(equipment_tab)

    # Теперь внутри frame_equipment размещаем Treeview
    equipment_tree = ttk.Treeview(
        frame_equipment,
        columns=("Тип", "Марка", "Модель", "Год", "Кол-во"),
        show="headings",
    )
    equipment_tree.pack(fill=tk.BOTH, expand=True)

    # Загружаем данные
    from database import load_equipment_data
    load_equipment_data(app, equipment_tree, ppe_number)

    equipment_tabs = ttk.Notebook(app.scrollable_frame)
    contract_tab = ttk.Frame(equipment_tabs)
    equipment_tabs.add(contract_tab, text="Контракты")

    canvas_contract, frame_contract = create_invisible_scrolled_area(contract_tab)

    contract_tree = ttk.Treeview(
        frame_contract,
        columns=("Дата", "Номер", "Поставщик", "ИНН", "Описание"),
        show="headings"
    )
    contract_tree.pack(fill=tk.BOTH, expand=True)
    # Заполнение contract_tree

    # PDF
    from pdf_handler import show_ppe_pdf
    show_ppe_pdf(app, str(ppe_number))

    # Контракты
    from database import show_contracts
    show_contracts(app, ppe_number)

# обновить список ППЭ
def refresh_ppe_list(app):
    """
    Очищает treeview со списком всех ППЭ и загружает новые данные из БД
    """
    for item in app.ppe_list.get_children():
        app.ppe_list.delete(item)

    cursor = app.connection.cursor()
    cursor.execute("SELECT ppe_number, ppe_address FROm dat_ppe ORDER BY ppe_number")
    rows = cursor.fetchall()

    messagebox.showinfo("Оповещение", "Список обновлён!")

    for row in rows:
        app.ppe_list.insert("", tk.END, values=row)