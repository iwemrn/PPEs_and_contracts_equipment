import os
from docxtpl import DocxTemplate
from datetime import datetime
from database import connect_to_database
from num2words import num2words

def get_equipment_list(ppe_number):
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
        string_agg(DISTINCT inv_number::text, '\n ') AS inv_numbers,
        equip_price                    AS price,
        equip_price * COUNT(*)         AS total_price
        FROM equip_data
        JOIN "dat_equip" 
            ON "dat_equip"."id" = equip_data.equip_id
        WHERE ppe_id = %s
        GROUP BY "name_in_1C", equip_price
        ORDER BY "name_in_1C";
    """
    cursor.execute(query, (ppe_number, ))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    equipment_list = []
    for row in rows:
        equipment_list.append({
            "row_number":   row[0],
            "equip_name":   row[1],
            "count_equip":  row[2],
            "inv_numbers":  row[3],
            "equip_price":  f"{row[4]:.2f}",
            "total_price":  f"{row[5]:.2f}"
        })
        print(equipment_list)
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

def generate_contract(ppe_number, save_path, code_contract, contract_date):
    """
    Формируем договор на основе template.docx,
    используя ppe_number для информации о договоре,
    и сохраняем результат в 'save_path'.
    """
    # 1. Проверка и настройка путей
    template_path = "Z://Sofia//template.docx"
    if not os.path.exists(template_path):
        alternative_path = os.path.join(os.path.dirname(__file__), "templates", "template.docx")
        if os.path.exists(alternative_path):
            template_path = alternative_path
        else:
            raise FileNotFoundError(f"Шаблон не найден: {template_path} или {alternative_path}")
    
    # 2. Создание директории для сохранения, если она не существует
    save_dir = os.path.dirname(save_path)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    try:
        # 3. Данные о договоре
        contract_data = get_contract_data_from_db(ppe_number)
        if not contract_data:
            print(f"Не найден договор по № ППЭ: {ppe_number}")
            return None
        
        # 4. Использование переданной даты или текущей
        if contract_date:
            # Если передана строка, преобразуем в datetime
            if isinstance(contract_date, str):
                try:
                    contract_date = datetime.strptime(contract_date, "%d.%m.%Y")
                except ValueError:
                    print(f"Неверный формат даты: {contract_date}. Используем текущую дату.")
                    contract_date = datetime.now()
        else:
            contract_date = datetime.now()
        
        day_int = contract_date.day
        month_int = contract_date.month
        year_int = contract_date.year
        month_rus = build_month_name_rus(month_int)
        
        # 5. Формирование контекста
        context = {
            "code_contract": code_contract,
            "day": day_int,
            "month_name": month_rus,
            "year": year_int,
            "year_next": year_int + 1,
            "num_contract": contract_data["num_contract"],
            "date_contract": contract_data["date_contract"],
            "name_contract": contract_data["name_contract"],
        }
        
        # 6. Подгружаем таблицу (список оборудования)
        try:
            equipment_list = get_equipment_list(ppe_number)
            if not equipment_list:
                print(f"Предупреждение: Список оборудования пуст для ППЭ {ppe_number}")
                equipment_list = []
                
            context["equipment_list"] = equipment_list
            
            total = sum(float(row["total_price"]) for row in equipment_list)
            context["total"] = f"{total:.2f}"
            context["total_price_text"] = amount_to_text_rus(total)
        except Exception as e:
            print(f"Ошибка при получении списка оборудования: {e}")
            context["equipment_list"] = []
            context["total"] = "0.00"
            context["total_price_text"] = "Ноль рублей 00 копеек"
        
        # 7. Добавляем данные из dat_ppe_details
        try:
            ppe_details = get_ppe_details(ppe_number)
            context.update(ppe_details)
        except Exception as e:
            print(f"Ошибка при получении деталей ППЭ: {e}")
        
        # 8. Добавляем данные из dat_responsible
        try:
            responsible_info = get_responsible_info(ppe_number)
            context.update(responsible_info)
        except Exception as e:
            print(f"Ошибка при получении информации об ответственном: {e}")
        
        # 9. Генерация документа
        doc = DocxTemplate(template_path)
        doc.render(context)
        
        # 10. Сохранение результата
        doc.save(save_path)
        print(f"Договор сформирован и сохранён: {save_path}")
        return save_path
        
    except Exception as e:
        print(f"Ошибка при генерации договора: {e}")
        import traceback
        traceback.print_exc()
        return None

def build_month_name_rus(month_int):
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return months[month_int - 1]

def get_ruble_suffix(n):
    """Возвращает правильное окончание для 'рубль'."""
    if 11 <= n % 100 <= 14:
        return "рублей"
    elif n % 10 == 1:
        return "рубль"
    elif 2 <= n % 10 <= 4:
        return "рубля"
    else:
        return "рублей"

def amount_to_text_rus(amount):
    rub = int(amount)
    kop = int(round((amount - rub) * 100))

    rub_text = num2words(rub, lang='ru')
    rub_suffix = get_ruble_suffix(rub)
    kop_text = f"{kop:02d}"

    return f"{rub_text.capitalize()} {rub_suffix} {kop_text} копеек"


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
