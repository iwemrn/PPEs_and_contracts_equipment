import os
from docxtpl import DocxTemplate
from datetime import datetime
from database import connect_to_database

def get_equipment_list():
    """
    Запрашивает данные оборудования, агрегирует и возвращает список словарей
    для вставки в шаблон docxtpl (equipment_list).
    """
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

    equipment_list = []
    for r in rows:
        equipment_list.append({
            "row_number":   r[0],
            "equip_name":   r[1],
            "count_equip":  r[2],
            "inv_numbers":  r[3],
            "equip_price":  f"{r[4]:.2f}",
            "total_price":  f"{r[5]:.2f}"
        })
    return equipment_list

def get_ppe_details(ppe_number):
    """
    Получает данные из dat_ppe_details для указанного ппе_number:
      SELECT fullname, address, inn, kpp, okpo, ogrn, cur_acc, bank_acc, pers_acc
    И возвращает словарь для подстановки в шаблон docxtpl.
    
    Шаблонные переменные:
      school_fullname, school_address, INN, KPP, OKPO, OGRN, cur_acc, bank_acc, pers_acc
    """
    conn = connect_to_database()
    cursor = conn.cursor()
    query = """
        SELECT fullname, address, inn, kpp, okpo, ogrn, cur_acc, bank_acc, pers_acc
        FROM dat_ppe_details
        WHERE ppe_number = %s
        LIMIT 1
    """
    cursor.execute(query, (ppe_number,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        # Если нет данных, вернём пустые поля
        return {
            "school_fullname": "",
            "school_address": "",
            "INN": "",
            "KPP": "",
            "OKPO": "",
            "OGRN": "",
            "cur_acc": "",
            "bank_acc": "",
            "pers_acc": "",
        }

    return {
        "school_fullname": row[0],
        "school_address":  row[1],
        "INN":             row[2],
        "KPP":             row[3],
        "OKPO":            row[4],
        "OGRN":            row[5],
        "cur_acc":         row[6],
        "bank_acc":        row[7],
        "pers_acc":        row[8],
    }

def get_responsible_info(ppe_number):
    """
    Получает данные из dat_responsible:
      SELECT "position", surname, first_name, second_name FROM dat_responsible
      WHERE ppe_number = %s
    Возвращает словарь для шаблона:
      job_title, surname, name, second_name
    (где "name" = first_name)
    """
    conn = connect_to_database()
    cursor = conn.cursor()
    query = """
        SELECT "position", surname, first_name, second_name
        FROM dat_responsible
        WHERE ppe_number = %s
        LIMIT 1
    """
    cursor.execute(query, (ppe_number,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return {
            "job_title":  "",
            "surname":    "",
            "name":       "",
            "second_name":"",
        }

    return {
        "job_title":  row[0],
        "surname":    row[1],
        "name":       row[2],  # first_name
        "second_name":row[3],
    }

def generate_contract(ppe_number, save_path):
    """
    Формируем договор на основе template.docx,
    используя ppe_number для информации о договоре,
    и сохраняем результат в 'save_path'.
    """
    template_path = "Z://Sofia//template.docx"
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Шаблон не найден: {template_path}")

    # Данные о договоре
    contract_data = get_contract_data_from_db(ppe_number)
    if not contract_data:
        print(f"Не найден договор по № ППЭ: {ppe_number}")
        return

    now = datetime.now()
    day_int = now.day
    month_int = now.month
    year_int = now.year
    month_rus = build_month_name_rus(month_int)

    context = {
        "day": day_int,
        "month_name": month_rus,
        "year": year_int,
        "year_next": year_int + 1,
        "num_contract":   contract_data["num_contract"],
        "date_contract":  contract_data["date_contract"],
        "name_contract":  contract_data["name_contract"],
        # при необходимости - доп. поля
    }

    # Подгружаем таблицу (список оборудования) 
    equipment_list = get_equipment_list()
    context["equipment_list"] = equipment_list

    total_price = sum(float(row["total_price"]) for row in equipment_list)
    context["total_price"] = f"{total_price:.2f}"
    context["total_price_text"] = amount_to_text_rus(total_price)

    # Добавляем данные из dat_ppe_details
    ppe_details = get_ppe_details(ppe_number)
    context.update(ppe_details)  # теперь есть school_fullname, school_address, etc.

    # Добавляем данные из dat_responsible
    responsible_info = get_responsible_info(ppe_number)
    context.update(responsible_info)  # job_title, surname, name, second_name

    doc = DocxTemplate(template_path)
    doc.render(context)

    doc.save(save_path)
    print(f"Договор сформирован и сохранён: {save_path}")

def build_month_name_rus(month_int):
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return months[month_int - 1]

def amount_to_text_rus(amount):
    rub = int(amount)
    kop = int(round((amount - rub)*100))
    return f"{rub} рублей {kop:02d} копеек"

def get_contract_data_from_db(ppe_number):
    """
    Пример запроса к dat_contract
    (как раньше).
    """
    conn = connect_to_database()
    cursor = conn.cursor()
    query = """
        SELECT contract_number,
            contract_date,
            contract_name,
            ppe_id
        FROM dat_contract, equip_data
        WHERE equip_data.contract_id = dat_contract.id
          AND ppe_id = %s
        LIMIT 1
    """
    cursor.execute(query, (ppe_number,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "num_contract":   row[0],
            "date_contract":  row[1].strftime("%d.%m.%Y") if row[1] else "",
            "name_contract":  row[2]
            # row[3] = ppe_id (если нужно)
        }
    return None
