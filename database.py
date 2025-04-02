import psycopg2
import tkinter as tk
from tkinter import ttk

def connect_to_database():
    """Установка соединения с базой данных PostgreSQL."""
    return psycopg2.connect(
        host='192.168.1.239',
        user='postgres',
        password='AXD54^sa',
        database='equipment_ppe'
    )

def show_contracts(app, ppe_number):
    """Отображение контрактов"""
    rows = _fetch_contracts(app, ppe_number)
    if not rows:
        tk.Label(
            app.scrollable_frame,
            text="Контракты: не найдены",
            font=("Arial", 12, "italic")
        ).pack(anchor="w", pady=5)
        return
    _display_contracts(app, rows)

def _fetch_contracts(app, ppe_number):
    """Получение данных контрактов из базы данных"""
    cursor = app.connection.cursor()
    query = """
        SELECT contract_date, contract_number, supplier, supplier_inn, contract_name 
        FROM dat_contract 
        WHERE id IN (SELECT contract_id FROM equip_data WHERE ppe_id = %s)
    """
    cursor.execute(query, (ppe_number,))
    rows = cursor.fetchall()
    print(f"Контракты для ППЭ {ppe_number}: {rows}")
    return rows

def _display_contracts(app, contracts):
    """Отображение данных контрактов"""
    equipment_tabs = ttk.Notebook(app.scrollable_frame)
    equipment_tabs.pack(fill=tk.BOTH, expand=True)

    contract_tab = ttk.Frame(equipment_tabs)
    equipment_tabs.add(contract_tab, text="Контракты")

    contract_tree = ttk.Treeview(
        contract_tab,
        columns=("Дата", "Номер", "Поставщик", "ИНН", "Описание"),
        show="headings"
    )

    columns_settings = [
        ("Дата", 120, "center"),
        ("Номер", 150, "center"),
        ("Поставщик", 200, "w"),
        ("ИНН", 120, "center"),
        ("Описание", 400, "w")
    ]

    for col, width, anchor in columns_settings:
        contract_tree.heading(col, text=col)
        contract_tree.column(col, width=width, anchor=anchor)

    for row in contracts:
        contract_tree.insert("", tk.END, values=row)

    contract_tree.pack(fill=tk.BOTH, expand=True)

def _fetch_equipment(app, ppe_number):
    """
    Получение данных об оборудовании для указанного ППЭ.
    Возвращает список кортежей (equip_type, equip_mark, equip_mod, release_year, amount).
    """
    cursor = app.connection.cursor()
    query = """
        SELECT de.equip_type, de.equip_mark, de.equip_mod, de.release_year, ed.amount
        FROM equip_data ed
        JOIN dat_equip de ON ed.equip_id = de.id::INTEGER
        WHERE ed.ppe_id = %s;
    """
    cursor.execute(query, (ppe_number,))
    rows = cursor.fetchall()
    return rows

def _display_equipment(app, rows):
    """
    Отображение данных оборудования в табличном виде (как _display_contracts).
    Создаем вкладку 'Оборудование' в Notebook и рисуем Treeview.
    """
    # Создаем Notebook (если нужно отдельное место) или используем уже имеющийся
    # Но по аналогии с _display_contracts:
    equipment_tabs = ttk.Notebook(app.scrollable_frame)
    equipment_tabs.pack(fill=tk.BOTH, expand=True)

    equip_tab = ttk.Frame(equipment_tabs)
    equipment_tabs.add(equip_tab, text="Оборудование")

    equipment_tree = ttk.Treeview(
        equip_tab,
        columns=("Тип", "Марка", "Модель", "Год", "Кол-во"),
        show="headings"
    )

    columns_settings = [
        ("Тип", 150, "center"),
        ("Марка", 120, "center"),
        ("Модель", 150, "center"),
        ("Год", 100, "center"),
        ("Кол-во", 100, "center")
    ]
    for col, width, anchor in columns_settings:
        equipment_tree.heading(col, text=col)
        equipment_tree.column(col, width=width, anchor=anchor)

    # Заполняем таблицу
    for row in rows:
        equipment_tree.insert("", tk.END, values=row)

    equipment_tree.pack(fill=tk.BOTH, expand=True)

def show_equipment(app, ppe_number):
    """
    Аналог 'show_contracts', но для оборудования.
    Если нет данных, выводим Label 'Оборудование: не найдено'
    Иначе передаем в _display_equipment(app, rows)
    """
    rows = _fetch_equipment(app, ppe_number)
    if not rows:
        tk.Label(
            app.scrollable_frame,
            text="Оборудование: не найдено",
            font=("Arial", 12, "italic")
        ).pack(anchor="w", pady=5)
        return

    _display_equipment(app, rows)

def check_agreement_exists(ppe_id):
    """
    Проверяет, есть ли значение agreement для указанного ППЭ в таблице equip_data.
    Возвращает True, если значение существует (не NULL), иначе False.
    """
    conn = connect_to_database()
    cursor = conn.cursor()
    query = """
        SELECT EXISTS (
            SELECT 1
            FROM equip_data
            WHERE ppe_id = %s AND agreement IS NOT NULL
            LIMIT 1
        )
    """
    cursor.execute(query, (ppe_id,))
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result