"""
Модуль для работы с договорами.
Содержит функции для генерации договоров и получения данных из БД.
"""

import os
import logging
from docxtpl import DocxTemplate
from datetime import datetime
from database import connect_to_database, execute_query, get_ppe_details
from num2words import num2words

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger('contracts')

# Константы
TEMPLATE_PATHS = [
    "Z://Sofia//template.docx",
    os.path.join(os.path.dirname(__file__), "templates", "template.docx")
]

def get_equipment_list(ppe_number):
    """
    Запрашивает данные оборудования, агрегирует и возвращает список словарей
    для вставки в шаблон docxtpl (equipment_list).
    Учитывает только оборудование с пустым полем agreement.
    Теперь принимает ИНН вместо номера ППЭ.
    """
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
        AND (agreement IS NULL OR agreement = '')
        GROUP BY "name_in_1C", equip_price
        ORDER BY "name_in_1C";
    """
    
    rows = execute_query(query, (ppe_number,))
    
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
    
    logger.info(f"Получено {len(equipment_list)} позиций оборудования для организации для ППЭ {ppe_number}")
    return equipment_list

def get_equipment_list_by_inn(inn):
    """
    Запрашивает данные оборудования по ИНН организации, агрегирует и возвращает список словарей
    для вставки в шаблон docxtpl (equipment_list).
    Учитывает только оборудование с пустым полем agreement.
    """
    query = """
        SELECT 
        row_number() OVER (ORDER BY "name_in_1C") AS row_num,
        "name_in_1C"                   AS equip_name,
        COUNT(*)                       AS equip_count,
        string_agg(DISTINCT inv_number::text, '\n ') AS inv_numbers,
        equip_price                    AS price,
        equip_price * COUNT(*)         AS total_price
        FROM equip_data
        JOIN "dat_equip" ON "dat_equip"."id" = equip_data.equip_id
        JOIN dat_ppe ON dat_ppe.id = equip_data.ppe_id
        JOIN dat_ppe_details ON dat_ppe_details.ppe_number = dat_ppe.id
        WHERE dat_ppe_details.inn = %s
        AND (agreement IS NULL OR agreement = '')
        GROUP BY "name_in_1C", equip_price
        ORDER BY "name_in_1C";
    """
    
    rows = execute_query(query, (inn,))
    
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
    
    logger.info(f"Получено {len(equipment_list)} позиций оборудования для организации с ИНН {inn}")
    return equipment_list

def get_equipment_list_by_school_id(school_id):
    """
    Запрашивает данные оборудования по school_id организации, агрегирует и возвращает список словарей
    для вставки в шаблон docxtpl (equipment_list).
    Учитывает только оборудование с пустым полем agreement.
    """
    query = """
        SELECT 
        row_number() OVER (ORDER BY "name_in_1C") AS row_num,
        "name_in_1C"                   AS equip_name,
        COUNT(*)                       AS equip_count,
        string_agg(DISTINCT inv_number::text, '\n ') AS inv_numbers,
        equip_price                    AS price,
        equip_price * COUNT(*)         AS total_price
        FROM equip_data
        JOIN "dat_equip" ON "dat_equip"."id" = equip_data.equip_id
        JOIN dat_ppe ON dat_ppe.id = equip_data.ppe_id
        WHERE dat_ppe.school_id = %s
        AND (agreement IS NULL OR agreement = '')
        GROUP BY "name_in_1C", equip_price
        ORDER BY "name_in_1C";
    """
    
    rows = execute_query(query, (school_id,))
    
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
    
    logger.info(f"Получено {len(equipment_list)} позиций оборудования для организации с school_id {school_id}")
    return equipment_list

def get_responsible_info_by_inn(inn):
    """
    Получает данные ответственного лица по ИНН организации.
    """
    query = """
        SELECT r."position", r.surname, r.first_name, r.second_name
        FROM dat_responsible r
        JOIN dat_ppe p ON r.ppe_number = p.id
        JOIN dat_ppe_details pd ON pd.ppe_number = p.id
        WHERE pd.inn = %s
        LIMIT 1
    """
    
    rows = execute_query(query, (inn,))
    
    if not rows:
        return {
            "job_title":  "",
            "surname":    "",
            "name":       "",
            "second_name":"",
        }

    row = rows[0]
    return {
        "job_title":  row[0],
        "surname":    row[1],
        "name":       row[2],  # first_name
        "second_name":row[3],
    }

def get_responsible_info(ppe_number):
    """
    Получает данные из dat_responsible для указанного ППЭ.
    """
    query = """
        SELECT "position", surname, first_name, second_name
        FROM dat_responsible
        WHERE ppe_number = %s
        LIMIT 1
    """
    
    rows = execute_query(query, (ppe_number,))
    
    if not rows:
        return {
            "job_title":  "",
            "surname":    "",
            "name":       "",
            "second_name":"",
        }

    row = rows[0]
    return {
        "job_title":  row[0],
        "surname":    row[1],
        "name":       row[2],  # first_name
        "second_name":row[3],
    }

def get_responsible_info_by_school_id(school_id):
    """
    Получает данные ответственного лица по school_id организации.
    """
    query = """
        SELECT r."position", r.surname, r.first_name, r.second_name
        FROM dat_responsible r
        JOIN dat_ppe p ON r.ppe_number = p.id
        WHERE p.school_id = %s
        LIMIT 1
    """
    
    rows = execute_query(query, (school_id,))
    
    if not rows:
        return {
            "job_title":  "",
            "surname":    "",
            "name":       "",
            "second_name":"",
        }

    row = rows[0]
    return {
        "job_title":  row[0],
        "surname":    row[1],
        "name":       row[2],  # first_name
        "second_name":row[3],
    }

def find_template():
    """Находит путь к шаблону договора."""
    for path in TEMPLATE_PATHS:
        if os.path.exists(path):
            return path
    
    # Если ни один из путей не существует, ищем в текущей директории
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(current_dir):
        if file.endswith(".docx") and "template" in file.lower():
            return os.path.join(current_dir, file)
    
    raise FileNotFoundError("Шаблон договора не найден")

def generate_contract(identifier, save_path, code_contract, contract_date, use_inn=False, use_school_id=False):
    """
    Формирует договор на основе шаблона,
    используя identifier для информации о договоре,
    и сохраняет результат в 'save_path'.
    """
    try:
        # 1. Проверка и настройка путей
        template_path = find_template()
        
        # 2. Создание директории для сохранения, если она не существует
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 3. Данные о договоре
        contract_data = get_contract_data_from_db(identifier, use_school_id=use_school_id)
        if not contract_data:
            logger.warning(f"Не удалось получить данные контракта для {'school_id' if use_school_id else 'ППЭ'}: {identifier}")
            # Используем пустые значения вместо возврата None
            contract_data = {
                "num_contract": "",
                "date_contract": "",
                "name_contract": ""
            }
        
        # 4. Использование переданной даты или текущей
        if contract_date:
            # Если передана строка, преобразуем в datetime
            if isinstance(contract_date, str):
                try:
                    contract_date = datetime.strptime(contract_date, "%d.%m.%Y")
                except ValueError:
                    logger.warning(f"Неверный формат даты: {contract_date}. Используем текущую дату.")
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
        
        # 6. Подгружаем данные ППЭ и реквизиты
        try:
            if use_school_id:
                # Получаем school_id для идентификатора
                school_id = identifier
            else:
                # Получаем school_id для ППЭ
                query_school_id = """
                    SELECT school_id FROM dat_ppe
                    WHERE id = %s
                """
                school_id_result = execute_query(query_school_id, (identifier,))
                if school_id_result and len(school_id_result) > 0:
                    school_id = school_id_result[0][0]
                else:
                    logger.warning(f"Не найден school_id для ППЭ: {identifier}")
                    school_id = None
            
            # Если school_id найден, получаем все реквизиты
            if school_id:
                # Используем обновленный запрос с правильными именами полей
                query_details = """
                    SELECT pd.school_id, pd.fullname, pd.address, pd.inn, pd.kpp, pd.okpo, pd.ogrn, pd.cur_acc, pd.bank_acc, pd.pers_acc
                    FROM dat_ppe_details pd
                    JOIN dat_ppe p ON pd.school_id = p.school_id
                    WHERE p.school_id = %s
                    LIMIT 1
                """
                details_result = execute_query(query_details, (school_id,))
                
                if details_result and len(details_result) > 0:
                    # Добавляем все реквизиты в контекст с правильными именами полей
                    context["school_id"] = details_result[0][0] if details_result[0][0] else ""
                    context["school_fullname"] = details_result[0][1] if details_result[0][1] else ""
                    context["school_address"] = details_result[0][2] if details_result[0][2] else ""
                    context["INN"] = details_result[0][3] if details_result[0][3] else ""
                    context["KPP"] = details_result[0][4] if details_result[0][4] else ""
                    context["OKPO"] = details_result[0][5] if details_result[0][5] else ""
                    context["OGRN"] = details_result[0][6] if details_result[0][6] else ""
                    context["cur_acc"] = details_result[0][7] if details_result[0][7] else ""
                    context["bank_acc"] = details_result[0][8] if details_result[0][8] else ""
                    context["pers_acc"] = details_result[0][9] if details_result[0][9] else ""
                    
                    # Сохраняем ИНН для дальнейшего использования
                    inn = context["INN"]
                    
                    # Дублируем некоторые поля с разными именами для совместимости с шаблоном
                    context["fullname"] = context["school_fullname"]
                    context["address"] = context["school_address"]
                    
                    logger.info(f"Загружены реквизиты для school_id {school_id}: {context}")
                else:
                    logger.warning(f"Не найдены реквизиты для school_id: {school_id}")
                    inn = ""
            else:
                logger.warning("Не удалось определить school_id для получения реквизитов")
                inn = ""
                
            # Получаем адрес ППЭ, если он еще не загружен
            if not use_school_id and identifier:
                query_ppe_address = """
                    SELECT ppe_address_fact FROM dat_ppe
                    WHERE id = %s
                """
                address_result = execute_query(query_ppe_address, (identifier,))
                if address_result and len(address_result) > 0:
                    context["ppe_address"] = address_result[0][0] if address_result[0][0] else ""
            
        except Exception as e:
            logger.error(f"Ошибка при получении реквизитов: {e}")
            import traceback
            logger.error(traceback.format_exc())
            inn = ""
            
        # 7. Подгружаем таблицу (список оборудования)
        try:
            if use_school_id:
                equipment_list = get_equipment_list_by_school_id(identifier)
            elif use_inn and inn:
                equipment_list = get_equipment_list_by_inn(inn)
            else:
                equipment_list = get_equipment_list(identifier)
            
            if not equipment_list:
                type_id = "school_id" if use_school_id else ("ИНН" if use_inn and inn else "ППЭ")
                logger.warning(f"Предупреждение: Список оборудования пуст для {type_id} {identifier}")
                equipment_list = []
                
            context["equipment_list"] = equipment_list
            
            total = sum(float(row["total_price"]) for row in equipment_list)
            context["total"] = f"{total:.2f}"
            context["total_price_text"] = amount_to_text_rus(total)
        except Exception as e:
            logger.error(f"Ошибка при получении списка оборудования: {e}")
            import traceback
            logger.error(traceback.format_exc())
            context["equipment_list"] = []
            context["total"] = "0.00"
            context["total_price_text"] = "Ноль рублей 00 копеек"
        
        # 8. Добавляем данные из dat_responsible
        try:
            if use_school_id:
                responsible_info = get_responsible_info_by_school_id(identifier)
            else:
                responsible_info = get_responsible_info(identifier)
            context.update(responsible_info)
        except Exception as e:
            logger.error(f"Ошибка при получении информации об ответственном: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Добавляем пустые значения для полей ответственного
            context.update({
                "job_title": "",
                "surname": "",
                "name": "",
                "second_name": ""
            })
        
        # 9. Генерация документа
        doc = DocxTemplate(template_path)
        
        # Выводим в лог все ключи контекста для отладки
        logger.info(f"Ключи контекста: {list(context.keys())}")
        logger.info(f"Значения контекста: {context}")
        
        doc.render(context)
        
        # 10. Сохранение результата
        doc.save(save_path)
        logger.info(f"Договор сформирован и сохранён: {save_path}")
        return save_path
        
    except Exception as e:
        logger.error(f"Ошибка при генерации договора: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def build_month_name_rus(month_int):
    """Возвращает название месяца в родительном падеже на русском языке."""
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
    """Преобразует числовую сумму в текстовое представление на русском языке."""
    rub = int(amount)
    kop = int(round((amount - rub) * 100))

    rub_text = num2words(rub, lang='ru')
    rub_suffix = get_ruble_suffix(rub)
    kop_text = f"{kop:02d}"

    return f"{rub_text.capitalize()} {rub_suffix} {kop_text} копеек"

def get_contract_data_from_db(identifier, use_school_id=False):
    """Получает данные контракта из базы данных."""
    if use_school_id:
        # Запрос для получения данных контракта по school_id
        query = """
            SELECT c.contract_number,
                c.contract_date,
                c.contract_name
            FROM dat_contract c
            JOIN equip_data ed ON ed.contract_id = c.id
            JOIN dat_ppe p ON p.id = ed.ppe_id
            WHERE p.school_id = %s
            LIMIT 1
        """
    else:
        # Стандартный запрос для получения данных контракта по ppe_id
        query = """
            SELECT contract_number,
                contract_date,
                contract_name
            FROM dat_contract c
            JOIN equip_data ed ON ed.contract_id = c.id
            WHERE ed.ppe_id = %s
            LIMIT 1
        """
    
    rows = execute_query(query, (identifier,))
    
    if rows and len(rows) > 0:
        row = rows[0]
        return {
            "num_contract":   row[0] if row[0] else "",
            "date_contract":  row[1].strftime("%d.%m.%Y") if row[1] else "",
            "name_contract":  row[2] if row[2] else ""
        }
    
    # Если контракт не найден, возвращаем пустые значения
    return {
        "num_contract": "",
        "date_contract": "",
        "name_contract": ""
    }

def validate_contract_date(date_str):
    """Проверяет корректность формата даты договора (ДД.ММ.ГГГГ)."""
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False

def get_default_contract_number(ppe_id):
    """Возвращает стандартный номер договора для ППЭ."""
    return f"ППЭ-{ppe_id}"

def create_temp_contract_directory():
    """Создает временную директорию для договоров."""
    temp_dir = os.path.join(os.path.expanduser("~"), "Documents", "TempContracts")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir
