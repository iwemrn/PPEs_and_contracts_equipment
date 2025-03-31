import os
from docxtpl import DocxTemplate
from datetime import datetime
from database import connect_to_database

def get_equipment_list():
    # Ваш запрос к БД
    conn = connect_to_database()
    cursor = conn.cursor()
    query = """
        SELECT 
          row_number() OVER (ORDER BY "name_in_1C") AS row_num,
          "name_in_1C"                   AS equip_name,
          COUNT(*)                       AS equip_count,
          string_agg(DISTINCT inv_number::text, '; ') AS inv_numbers,
          equip_price                    AS price,
          equip_price * COUNT(*)         AS total_price
        FROM equip_data
        JOIN "dat_equip" 
            ON "dat_equip"."id" = equip_data.equip_id
        GROUP BY "name_in_1C", equip_price
        ORDER BY "name_in_1C";
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Преобразуем
    equipment_list = []
    for r in rows:
        equipment_list.append({
            "row_number": r[0],
            "equip_name": r[1],
            "count_equip": r[2],
            "inv_numbers": r[3],
            "equip_price": f"{r[4]:.2f}",
            "total_price": f"{r[5]:.2f}"
        })
    return equipment_list

def generate_contract(contract_id):
    """
    Формируем договор на основе template.docx,
    используя contract_id для информации о договоре.
    """
    template_path = "Z://Sofia//template.docx"  # ваш путь
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Шаблон не найден: {template_path}")

    # Допустим, contract_data берём из dat_contract
    contract_data = get_contract_data_from_db(contract_id)
    if not contract_data:
        print(f"Не найден договор ID={contract_id}")
        return

    # Дата «сегодня»
    now = datetime.now()
    day_int = now.day
    month_int = now.month
    year_int = now.year
    month_rus = build_month_name_rus(month_int)

    # Собираем context
    context = {
        "day": day_int,
        "month_name": month_rus,
        "year": year_int,
        "num_contract": contract_data["num_contract"],
        "date_contract": contract_data["date_contract"],
        "name_contract": contract_data["name_contract"],
        # ...
    }

    # Подгружаем таблицу (список оборудования) 
    equipment_list = get_equipment_list()
    context["equipment_list"] = equipment_list

    # Итоговая сумма
    total_price = sum(float(row["total_price"]) for row in equipment_list)
    context["total_price"] = f"{total_price:.2f}"
    context["total_price_text"] = amount_to_text_rus(total_price)

    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(f"Договор_{contract_data['num_contract']}.docx")
    print("Договор сформирован.")

def build_month_name_rus(month_int):
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return months[month_int - 1]

def amount_to_text_rus(amount):
    # Упрощённая конвертация
    rub = int(amount)
    kop = int(round((amount - rub)*100))
    # ... примитивный вариант:
    return f"{rub} рублей {kop:02d} копеек"

def get_contract_data_from_db(contract_id):
    """
    Пример запроса к dat_contract.
    """
    conn = connect_to_database()
    cursor = conn.cursor()
    query = """
        SELECT contract_number,
               contract_date,
               contract_name
        FROM dat_contract
        WHERE id = %s
    """
    cursor.execute(query, (contract_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
          "num_contract": row[0],
          "date_contract": row[1].strftime("%d.%m.%Y") if row[1] else "",
          "name_contract": row[2]
        }
    return None
