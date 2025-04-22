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
    "C://Users//erokhina//Desktop//coding//PPEs_and_contracts_equipment//templates//template.docx",
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
        JOIN dat_ppe p ON r.school_id = p.school_id
        WHERE p.school_id = %s
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
        SELECT r."position", r.surname, r.first_name, r.second_name
        FROM dat_responsible r
        JOIN dat_ppe p ON r.school_id = p.school_id
        WHERE p.school_id = %s
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
        JOIN dat_ppe p ON r.school_id = p.school_id
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
                # Добавляем тестовую запись для отладки
                equipment_list = [{
                    "row_number": 1,
                    "equip_name": "Тестовое оборудование",
                    "count_equip": 1,
                    "inv_numbers": "TEST123",
                    "equip_price": "1000.00",
                    "total_price": "1000.00"
                }]
                
            context["equipment_list"] = equipment_list
            
            total = sum(float(row["total_price"]) for row in equipment_list)
            context["total"] = f"{total:.2f}"
            context["total_price_text"] = amount_to_text_rus(total)
            

            logger.info(f"Список оборудования в контексте: {len(context.get('equipment_list', []))} позиций")
        except Exception as e:
            logger.error(f"Ошибка при получении списка оборудования: {e}")
            import traceback
            logger.error(traceback.format_exc())
            context["equipment_list"] = [{
                "row_number": 1,
                "equip_name": "Тестовое оборудование (ошибка при загрузке)",
                "count_equip": 1,
                "inv_numbers": "ERROR",
                "equip_price": "0.00",
                "total_price": "0.00"
            }]
            context["total"] = "0.00"
            context["total_price_text"] = "Ноль рублей 00 копеек"
        
        # 8. Добавляем данные из dat_responsible
        try:
            if use_school_id:
                responsible_info = get_responsible_info_by_school_id(identifier)
                logger.info(f"Получена информация об ответственном лице по school_id {identifier}: {responsible_info}")
            else:
                responsible_info = get_responsible_info(identifier)
                logger.info(f"Получена информация об ответственном лице по ППЭ {identifier}: {responsible_info}")
            
            # Добавляем базовую информацию об ответственном лице
            context.update(responsible_info)
            
            # Добавляем инициалы и полное ФИО с инициалами
            if responsible_info["name"] and responsible_info["second_name"]:
                name_initial = responsible_info["name"][0] if responsible_info["name"] else ""
                second_name_initial = responsible_info["second_name"][0] if responsible_info["second_name"] else ""
                
                context["name_initial"] = name_initial + "." if name_initial else ""
                context["second_name_initial"] = second_name_initial + "." if second_name_initial else ""
                
                # ФИО с инициалами (Иванов И.И.)
                context["full_name_with_initials"] = (
                    f"{responsible_info['surname']} {context['name_initial']} {context['second_name_initial']}"
                ).strip()
                
                # ФИО полностью (Иванов Иван Иванович)
                context["responsible_fullname"] = (
                    f"{responsible_info['surname']} {responsible_info['name']} {responsible_info['second_name']}"
                ).strip()
            else:
                context["name_initial"] = ""
                context["second_name_initial"] = ""
                context["full_name_with_initials"] = responsible_info["surname"]
                context["responsible_fullname"] = responsible_info["surname"]

            # Добавляем версии в родительном падеже
            try:
                context["job_title_genitive"] = convert_to_genitive(responsible_info["job_title"])
                context["surname_genitive"] = convert_to_genitive(responsible_info["surname"])
                context["name_genitive"] = convert_to_genitive(responsible_info["name"])
                context["second_name_genitive"] = convert_to_genitive(responsible_info["second_name"])
                
                # Полное ФИО в родительном падеже
                context["full_name_genitive"] = f"{context['surname_genitive']} {context['name_genitive']} {context['second_name_genitive']}".strip()
                
                # ФИО с инициалами в родительном падеже
                if context.get("name_initial") and context.get("second_name_initial"):
                    context["full_name_with_initials_genitive"] = f"{context['surname_genitive']} {context['name_initial']} {context['second_name_initial']}".strip()
                else:
                    context["full_name_with_initials_genitive"] = context["surname_genitive"]
                
                # Должность и ФИО в родительном падеже
                context["job_title_and_full_name_genitive"] = f"{context.get('job_title_genitive', '')} {context.get('full_name_genitive', '')}".strip()
                context["job_title_and_full_name_with_initials_genitive"] = f"{context.get('job_title_genitive', '')} {context.get('full_name_with_initials_genitive', '')}".strip()
                
                logger.info(f"Добавлены переменные в родительном падеже: {context['job_title_genitive']}, {context['full_name_genitive']}")
            except Exception as e:
                logger.error(f"Ошибка при формировании родительного падежа: {e}")
                # Устанавливаем значения по умолчанию
                context["job_title_genitive"] = context.get("job_title", "")
                context["surname_genitive"] = context.get("surname", "")
                context["name_genitive"] = context.get("name", "")
                context["second_name_genitive"] = context.get("second_name", "")
                context["full_name_genitive"] = context.get("surname", "")
                context["full_name_with_initials_genitive"] = context.get("surname", "")
                context["job_title_and_full_name_genitive"] = f"{context.get('job_title', '')} {context.get('surname', '')}".strip()
                context["job_title_and_full_name_with_initials_genitive"] = f"{context.get('job_title', '')} {context.get('surname', '')}".strip()

        except Exception as e:
            logger.error(f"Ошибка при получении информации об ответственном: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Добавляем пустые значения для полей ответственного
            context.update({
                "job_title": "",
                "surname": "",
                "name": "",
                "second_name": "",
                "name_initial": "",
                "second_name_initial": "",
                "full_name_with_initials": "",
                "responsible_fullname": "",
                "job_title_genitive": "",
                "surname_genitive": "",
                "name_genitive": "",
                "second_name_genitive": "",
                "full_name_genitive": "",
                "full_name_with_initials_genitive": "",
                "job_title_and_full_name_genitive": "",
                "job_title_and_full_name_with_initials_genitive": ""
            })
        # 9. Генерация документа
        doc = DocxTemplate(template_path)
        
        # Выводим в лог ключи контекста для отладки
        logger.info(f"Ключи контекста: {list(context.keys())}")
        
        # Выводим информацию об ответственном лице для отладки
        logger.info("Переменные для ответственного лица:")
        for key in ['job_title', 'surname', 'name', 'second_name', 
                    'job_title_genitive', 'surname_genitive', 'name_genitive', 'second_name_genitive',
                    'full_name_with_initials', 'full_name_with_initials_genitive',
                    'job_title_and_full_name_genitive', 'job_title_and_full_name_with_initials_genitive']:
            logger.info(f"  {key}: {context.get(key, 'НЕ ЗАДАНО')}")
        
        doc.render(context)

        for table in doc.tables:
            for row in list(table.rows):                         # делаем копию, иначе skip‑прыжки
                if all(cell.text.strip() == "" for cell in row.cells):
                    row._tr.getparent().remove(row._tr)          # XML‑удаление :contentReference[oaicite:0]{index=0}
        
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

def convert_to_genitive(word_or_phrase):
    """
    Преобразует слово или фразу в родительный падеж.
    """
    if not word_or_phrase or not isinstance(word_or_phrase, str):
        return ""
    
    # Словарь для должностей
    job_titles_genitive = {
        "директор": "директора",
        "заместитель директора": "заместителя директора",
        "учитель": "учителя",
        "преподаватель": "преподавателя",
        "руководитель": "руководителя",
        "заведующий": "заведующего",
        "методист": "методиста",
        "специалист": "специалиста",
        "инженер": "инженера",
        "техник": "техника"
    }
    
    # Словарь для распространенных имен и фамилий
    names_genitive = {
        "иван": "ивана",
        "петр": "петра",
        "александр": "александра",
        "сергей": "сергея",
        "андрей": "андрея",
        "дмитрий": "дмитрия",
        "михаил": "михаила",
        "николай": "николая",
        "владимир": "владимира",
        "алексей": "алексея",
        "мария": "марии",
        "анна": "анны",
        "елена": "елены",
        "ольга": "ольги",
        "татьяна": "татьяны",
        "наталья": "натальи",
        "екатерина": "екатерины",
        "ирина": "ирины",
        "светлана": "светланы",
        "юлия": "юлии",
        # Добавляем тестовые имена
        "тест": "теста",
        "тестовый": "тестового",
        "тестович": "тестовича"
    }
    
    # Словарь для отчеств
    patronymics_genitive = {
        "иванович": "ивановича",
        "петрович": "петровича",
        "александрович": "александровича",
        "сергеевич": "сергеевича",
        "андреевич": "андреевича",
        "дмитриевич": "дмитриевича",
        "михайлович": "михайловича",
        "николаевич": "николаевича",
        "владимирович": "владимировича",
        "алексеевич": "алексеевича",
        "ивановна": "ивановны",
        "петровна": "петровны",
        "александровна": "александровны",
        "сергеевна": "сергеевны",
        "андреевна": "андреевны",
        "дмитриевна": "дмитриевны",
        "михайловна": "михайловны",
        "николаевна": "николаевны",
        "владимировна": "владимировны",
        "алексеевна": "алексеевны",
        # Добавляем тестовые отчества
        "тестович": "тестовича",
        "тестовна": "тестовны"
    }
    
    # Правила склонения фамилий
    def decline_surname(surname):
        surname_lower = surname.lower()
        
        # Если фамилия уже есть в словаре, используем готовое склонение
        if surname_lower in names_genitive:
            return names_genitive[surname_lower]
        
        # Правила склонения мужских фамилий
        if surname_lower.endswith(('ов', 'ев', 'ин', 'ын')):
            return surname + 'а'
        elif surname_lower.endswith(('ий')):
            return surname[:-2] + 'ого'
        elif surname_lower.endswith(('ый', 'ой')):
            return surname[:-2] + 'ого'
        elif surname_lower.endswith(('ь')):
            return surname[:-1] + 'я'
        
        # Если не удалось применить правила, возвращаем исходную фамилию
        return surname
    
    # Объединяем словари
    all_words_genitive = {**job_titles_genitive, **names_genitive, **patronymics_genitive}
    
    # Проверяем, есть ли фраза целиком в словаре
    lower_phrase = word_or_phrase.lower()
    if lower_phrase in all_words_genitive:
        # Сохраняем оригинальный регистр первой буквы
        if word_or_phrase[0].isupper():
            return all_words_genitive[lower_phrase].capitalize()
        return all_words_genitive[lower_phrase]
    
    # Если фразы целиком нет, пробуем разбить на слова
    words = word_or_phrase.split()
    result = []
    
    for word in words:
        lower_word = word.lower()
        if lower_word in all_words_genitive:
            # Сохраняем оригинальный регистр первой буквы
            if word[0].isupper():
                result.append(all_words_genitive[lower_word].capitalize())
            else:
                result.append(all_words_genitive[lower_word])
        else:
            # Пробуем применить правила склонения для фамилий
            if len(words) >= 2 and words.index(word) == 0:  # Предполагаем, что фамилия идет первой
                declined_surname = decline_surname(word)
                result.append(declined_surname)
            else:
                # Если слова нет в словаре и не похоже на фамилию, оставляем как есть
                result.append(word)
    
    return ' '.join(result)