import os
from docxtpl import DocxTemplate
from datetime import datetime
import locale
import psycopg2

conn = psycopg2.connect(
    host='192.168.1.239',
    user='postgres',
    password='AXD54^sa',
    database='equipment_ppe'
)
cursor = conn.cursor()

# 1) Получаем данные из dat_ppe
query = """
    SELECT ppe_number, ppe_address, school_inn 
    FROM public.dat_ppe
    ORDER BY id ASC
"""
cursor.execute(query)
rows = cursor.fetchall()
cursor.close()

print("Всего строк из dat_ppe:", len(rows))

# 2) Переносим данные в dat_responsible
for row in rows:
    try:
        # row: (ppe_number, ppe_address, school_inn)
        number = row[0]
        add = row[1]
        inn = row[2]

        # Если какие-то поля int или text, будьте внимательны.
        # Допустим, ppe_number - int, ppe_address - text, school_inn - text.

        cursor_insert = conn.cursor()
        insert_query = """
            INSERT INTO dat_ppe_details (ppe_number, address, inn)
            VALUES (%s, %s, %s)
        """
        cursor_insert.execute(insert_query, (number, add, inn))
        cursor_insert.close()

        print(f"Добавлен ppe_number={number} inn={inn}")

    except Exception as e:
        print("Ошибка при вставке:", e)

# 3) Подтверждаем изменения
conn.commit()
conn.close()
