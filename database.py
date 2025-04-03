"""
Модуль для работы с базой данных PostgreSQL.
Содержит функции для подключения к БД и выполнения запросов.
"""

import psycopg2
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger('database')

# Константы для подключения к БД
DB_CONFIG = {
    'host': '192.168.1.239',
    'user': 'postgres',
    'password': 'AXD54^sa',
    'database': 'equipment_ppe'
}

def connect_to_database():
    """Установка соединения с базой данных PostgreSQL."""
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection
    except psycopg2.Error as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise

def execute_query(query, params=None, fetch=True):
    """
    Выполняет SQL-запрос к базе данных.
    
    Args:
        query (str): SQL-запрос
        params (tuple, optional): Параметры запроса
        fetch (bool, optional): Нужно ли возвращать результат запроса
        
    Returns:
        list: Результат запроса или None в случае ошибки
    """
    conn = None
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
            
        return result
    except psycopg2.Error as e:
        logger.error(f"Ошибка выполнения запроса: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def get_ppe_list():
    """Получает список всех ППЭ из базы данных."""
    query = "SELECT id, ppe_address_fact FROM dat_ppe ORDER BY ppe_number"
    return execute_query(query)

def show_contracts(app, ppe_number):
    """Отображение контрактов для указанного ППЭ."""
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
    """Получение данных контрактов из базы данных."""
    query = """
        SELECT contract_date, contract_number, supplier, supplier_inn, contract_name 
        FROM dat_contract 
        WHERE id IN (SELECT contract_id FROM equip_data WHERE ppe_id = %s)
    """
    try:
        cursor = app.connection.cursor()
        cursor.execute(query, (ppe_number,))
        rows = cursor.fetchall()
        logger.info(f"Контракты для ППЭ {ppe_number}: {len(rows)} записей")
        return rows
    except Exception as e:
        logger.error(f"Ошибка при получении контрактов: {e}")
        return []

def _display_contracts(app, contracts):
    """Отображение данных контрактов в интерфейсе."""
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
    query = """
        SELECT de.equip_type, de.equip_mark, de.equip_mod, de.release_year, ed.amount
        FROM equip_data ed
        JOIN dat_equip de ON ed.equip_id = de.id::INTEGER
        WHERE ed.ppe_id = %s;
    """
    try:
        cursor = app.connection.cursor()
        cursor.execute(query, (ppe_number,))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        logger.error(f"Ошибка при получении оборудования: {e}")
        return []

def _display_equipment(app, rows):
    """
    Отображение данных оборудования в табличном виде.
    """
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

    for row in rows:
        equipment_tree.insert("", tk.END, values=row)

    equipment_tree.pack(fill=tk.BOTH, expand=True)

def show_equipment(app, ppe_number):
    """
    Отображает оборудование для указанного ППЭ.
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

def update_equipment_agreement(ppe_id, contract_number, contract_year):
    """
    Обновляет поле agreement в таблице equip_data для указанного ППЭ.
    Формат agreement: "<номер договора>/<год заключения договора>"
    
    Returns:
        int: Количество обновленных записей
    """
    agreement_value = f"{contract_number}/{contract_year}"
    
    query = """
        UPDATE equip_data
        SET agreement = %s
        WHERE ppe_id = %s AND (agreement IS NULL OR agreement = '')
    """
    
    return execute_query(query, (agreement_value, ppe_id), fetch=False)

def get_ppe_details(ppe_id):
    """Получает детальную информацию о ППЭ."""
    query = """
        SELECT p.id, p.ppe_address_fact, 
            pd.fullname, pd.inn
        FROM dat_ppe p
        LEFT JOIN dat_ppe_details pd ON p.school_id = pd.school_id
        WHERE p.id = %s
    """
    
    result = execute_query(query, (ppe_id,))
    return result[0] if result else None

def get_responsible_person(ppe_id):
    """Получает информацию об ответственном лице ППЭ."""
    query = """
        SELECT position, surname, first_name, second_name
        FROM dat_responsible
        WHERE ppe_number = %s
    """
    
    result = execute_query(query, (ppe_id,))
    return result[0] if result else None

def save_contract_data(ppe_id, contract_number, contract_date, contract_name=None):
    """Сохраняет информацию о договоре в базу данных."""
    if not contract_name:
        contract_name = f"Договор {contract_number} от {contract_date}"
    
    # Проверяем, существует ли уже договор для этого ППЭ
    check_query = """
        SELECT id FROM dat_contract
        WHERE contract_number = %s
    """
    existing_contract = execute_query(check_query, (contract_number,))
    
    if existing_contract:
        # Обновляем существующий договор
        update_query = """
            UPDATE dat_contract
            SET contract_date = %s, contract_name = %s
            WHERE id = %s
            RETURNING id
        """
        result = execute_query(update_query, (
            datetime.strptime(contract_date, "%d.%m.%Y"),
            contract_name,
            existing_contract[0][0]
        ))
        contract_id = result[0][0]
    else:
        # Создаем новый договор
        insert_query = """
            INSERT INTO dat_contract (contract_number, contract_date, contract_name)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        result = execute_query(insert_query, (
            contract_number,
            datetime.strptime(contract_date, "%d.%m.%Y"),
            contract_name
        ))
        contract_id = result[0][0]
    
    # Связываем договор с ППЭ
    try:
        link_query = """
            UPDATE equip_data
            SET contract_id = %s
            WHERE ppe_id = %s
        """
        execute_query(link_query, (contract_id, ppe_id), fetch=False)
    except Exception as e:
        logger.error(f"Ошибка при связывании договора с ППЭ: {e}")
    
    return contract_id
