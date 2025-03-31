import sqlite3
import pandas as pd
from openpyxl import load_workbook

def create_database():
    connection = sqlite3.connect("ppe_database.db")
    cursor = connection.cursor()

    # Создание таблицы PPE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PPE (
            ppe_id INTEGER PRIMARY KEY,
            address TEXT NOT NULL,
            exam_type TEXT,
            auditory_count INTEGER,
            distance_to_rcoi_km REAL
        )
    ''')

    # Создание таблиц для оборудования
    equipment_tables = {
        "Camera": """
            CREATE TABLE IF NOT EXISTS Camera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppe_id INTEGER,
                brand TEXT,
                model TEXT,
                year INTEGER,
                quantity INTEGER,
                note TEXT,
                replacement_needed INTEGER,
                planned_purchase TEXT,
                FOREIGN KEY (ppe_id) REFERENCES PPE(ppe_id)
            )
        """,
        "Switch": """
            CREATE TABLE IF NOT EXISTS Switch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppe_id INTEGER,
                brand TEXT,
                model TEXT,
                year INTEGER,
                quantity INTEGER,
                note TEXT,
                replacement_needed INTEGER,
                planned_purchase TEXT,
                FOREIGN KEY (ppe_id) REFERENCES PPE(ppe_id)
            )
        """,
        "ARM": """
            CREATE TABLE IF NOT EXISTS ARM (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppe_id INTEGER,
                pc_count INTEGER,
                win7_count INTEGER,
                win10_count INTEGER,
                other_os_count INTEGER,
                kog_station_need INTEGER,
                replacement_needed INTEGER,
                planned_purchase TEXT,
                FOREIGN KEY (ppe_id) REFERENCES PPE(ppe_id)
            )
        """,
        "Printer": """
            CREATE TABLE IF NOT EXISTS Printer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppe_id INTEGER,
                brand TEXT,
                model TEXT,
                year INTEGER,
                quantity INTEGER,
                note TEXT,
                replacement_needed INTEGER,
                planned_purchase TEXT,
                FOREIGN KEY (ppe_id) REFERENCES PPE(ppe_id)
            )
        """,
        "Scanner": """
            CREATE TABLE IF NOT EXISTS Scanner (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppe_id INTEGER,
                brand TEXT,
                model TEXT,
                year INTEGER,
                quantity INTEGER,
                note TEXT,
                replacement_needed INTEGER,
                planned_purchase TEXT,
                FOREIGN KEY (ppe_id) REFERENCES PPE(ppe_id)
            )
        """,
        "MFP": """
            CREATE TABLE IF NOT EXISTS MFP (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppe_id INTEGER,
                brand TEXT,
                model TEXT,
                year INTEGER,
                quantity INTEGER,
                note TEXT,
                replacement_needed INTEGER,
                planned_purchase TEXT,
                FOREIGN KEY (ppe_id) REFERENCES PPE(ppe_id)
            )
        """,
        "Calculator": """
            CREATE TABLE IF NOT EXISTS Calculator (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppe_id INTEGER,
                brand TEXT,
                model TEXT,
                year INTEGER,
                quantity INTEGER,
                note TEXT,
                replacement_needed INTEGER,
                planned_purchase TEXT,
                FOREIGN KEY (ppe_id) REFERENCES PPE(ppe_id)
            )
        """,
        "Headset": """
            CREATE TABLE IF NOT EXISTS Headset (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppe_id INTEGER,
                brand TEXT,
                model TEXT,
                year INTEGER,
                quantity INTEGER,
                note TEXT,
                replacement_needed INTEGER,
                planned_purchase TEXT,
                FOREIGN KEY (ppe_id) REFERENCES PPE(ppe_id)
            )
        """
    }

    for table_name, create_statement in equipment_tables.items():
        cursor.execute(create_statement)

    connection.commit()
    connection.close()

def process_sheet(sheet_name, file_path):
    connection = sqlite3.connect("ppe_database.db")
    cursor = connection.cursor()

    workbook = load_workbook(filename=file_path, data_only=True)
    sheet = workbook[sheet_name]
    data = sheet.values
    columns = next(data)
    df = pd.DataFrame(data, columns=columns)

    if sheet_name == "Реестр ППЭ":
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO PPE (ppe_id, address, exam_type, auditory_count, distance_to_rcoi_km)
                VALUES (?, ?, ?, ?, ?)
            ''', (row["№ ППЭ"], row["Адрес ППЭ"], row["Вид ГИА"], row["Количество аудиторий"], row["Расстояние до РЦОИ, км"]))

    elif sheet_name == "Камера":
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO Camera (ppe_id, brand, model, year, quantity, note, replacement_needed, planned_purchase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row["№ ППЭ"], row["Марка"], row["Модель"], row["Год"], row["Количество"], row["Примечание"], row["Требуется замена"], row["Планируется к закупке за счет средств МОУО/ОО до начала экзаменационного периода"]))

    elif sheet_name == "Коммутатор":
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO Switch (ppe_id, brand, model, year, quantity, note, replacement_needed, planned_purchase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row["№ ППЭ"], row["Марка"], row["Модель"], row["Год"], row["Количество"], row["Примечание"], row["Требуется замена"], row["Планируется к закупке за счет средств МОУО/ОО до начала экзаменационного периода"]))

    elif sheet_name == "АРМ":
        print(f"Processing sheet: {sheet_name}")
        print(f"Columns found in sheet: {df.columns.tolist()}")  # Выводит список колонок
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO ARM (ppe_id, pc_count, win7_count, win10_count, other_os_count, kog_station_need, replacement_needed, planned_purchase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row["№ ППЭ"], 
                row["Количество ПК и ноутбуков, используемых для проведения ГИА (в штабе и аудиториях, включая резерв)"], 
                row["Количество ПК и ноутбуков с Windows 7"], 
                row["Количество ПК и ноутбуков с Windows 10"], 
                row["Количество ПК и ноутбуков с иными ОС"], 
                row["Потребность в станциях КОГЭ (сколько не хватает)"], 
                row["Количество ПК и ноутбуков, требующих замены"], 
                row["Планируется к закупке за счет средств МОУО/ОО до начала экзаменационного периода"]
            ))

    elif sheet_name == "Принтер":
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO Printer (ppe_id, brand, model, year, quantity, note, replacement_needed, planned_purchase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row["№ ППЭ"], row["Марка"], row["Модель"], row["Год"], row["Количество"], row["Примечание"], row["Требуется замена"], row["Планируется к закупке за счет средств МОУО/ОО до начала экзаменационного периода"]))

    elif sheet_name == "Сканер":
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO Scanner (ppe_id, brand, model, year, quantity, note, replacement_needed, planned_purchase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row["№ ППЭ"], row["Марка"], row["Модель"], row["Год"], row["Количество"], row["Примечание"], row["Требуется замена"], row["Планируется к закупке за счет средств МОУО/ОО до начала экзаменационного периода"]))

    elif sheet_name == "МФУ":
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO MFP (ppe_id, brand, model, year, quantity, note, replacement_needed, planned_purchase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row["№ ППЭ"], row["Марка"], row["Модель"], row["Год"], row["Количество"], row["Примечание"], row["Требуется замена"], row["Планируется к закупке за счет средств МОУО/ОО до начала экзаменационного периода"]))

    elif sheet_name == "Калькулятор":
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO Calculator (ppe_id, brand, model, year, quantity, note, replacement_needed, planned_purchase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row["№ ППЭ"], row["Марка"], row["Модель"], row["Год"], row["Количество"], row["Примечание"], row["Требуется замена"], row["Планируется к закупке за счет средств МОУО/ОО до начала экзаменационного периода"]))

    elif sheet_name == "Гарнитура":
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO Headset (ppe_id, brand, model, year, quantity, note, replacement_needed, planned_purchase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row["№ ППЭ"], row["Марка"], row["Модель"], row["Год"], row["Количество"], row["Примечание"], row["Требуется замена"], row["Планируется к закупке за счет средств МОУО/ОО до начала экзаменационного периода"]))

    connection.commit()
    connection.close()

def display_table_and_wait(table_name):
    connection = sqlite3.connect("ppe_database.db")
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, connection)
    print(df)
    input("Press Enter to continue...")
    connection.close()


def main():
    file_path = "3C0AC710.xlsx"  # Замените на путь к вашему файлу
    sheet_names = ["Реестр ППЭ", "Камера", "Коммутатор", "АРМ", "Принтер", "Сканер", "МФУ", "Калькулятор", "Гарнитура"]

    create_database()

    for sheet_name in sheet_names:
        process_sheet(sheet_name, file_path)

        table_mapping = {
            "Реестр ППЭ": "PPE",
            "Камера": "Camera",
            "Коммутатор": "Switch",
            "АРМ": "ARM",
            "Принтер": "Printer",
            "Сканер": "Scanner",
            "МФУ": "MFP",
            "Калькулятор": "Calculator",
            "Гарнитура": "Headset"
        }

        table_name = table_mapping[sheet_name]
        display_table_and_wait(table_name)

if __name__ == "__main__":
    main()

# def find_duplicates_and_wait():
#     connection = sqlite3.connect("ppe_database.db")
#     cursor = connection.cursor()

#     equipment_tables = [
#         "Camera",
#         "Switch",
#         "ARM",
#         "Printer",
#         "Scanner",
#         "MFP",
#         "Calculator",
#         "Headset"
#     ]

#     for table in equipment_tables:
#         print(f"Checking duplicates in table: {table}")

#         # Генерация SQL-запроса для поиска дубликатов
#         query = f"""
#         SELECT *, COUNT(*) as duplicate_count
#         FROM {table}
#         GROUP BY ppe_id, brand, model, year, quantity, note, replacement_needed, planned_purchase
#         HAVING COUNT(*) > 1
#         """
#         cursor.execute(query)
#         duplicates = cursor.fetchall()

#         if duplicates:
#             print(f"Duplicates found in {table}:")
#             for row in duplicates:
#                 print(row)
#         else:
#             print(f"No duplicates found in {table}.")

#         input("Press Enter to continue to the next table...")

#     connection.close()

# if __name__ == "__main__":
#     find_duplicates_and_wait()
