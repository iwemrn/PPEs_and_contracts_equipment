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
    pass


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
    pass

def get_responsible_info(ppe_number):
    pass

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

# def generate_contract(identifier, save_path, code_contract, contract_date):
#     """
#     Генерирует договор на основе шаблона для нескольких контрактов, используя номер ППЭ.
#     """
#     try:
#         # 1. Получение пути к шаблону
#         template_path = find_template()

#         # 2. Получение данных для всех контрактов
#         contracts_data = []
#         for contract in identifier:
#             # Извлекаем данные о контрактах из базы данных
#             contract_data = get_contract_data_from_db(contract["contract_number"])
#             contracts_data.append(contract_data)

#         # 3. Использование переданной даты или текущей
#         if contract_date:
#             contract_date = datetime.strptime(contract_date, "%d.%m.%Y")
#         else:
#             contract_date = datetime.now()

#         # 4. Подготовка контекста для шаблона
#         context = {
#             "contracts_data": contracts_data,  # Данные по всем контрактам
#             "code_contract": code_contract,
#             "day": contract_date.day,
#             "month_name": build_month_name_rus(contract_date.month),
#             "year": contract_date.year,
#             "year_next": contract_date.year + 1
#         }

#         # 5. Получение оборудования и ответственного лица по номеру ППЭ
#         equipment_list = get_equipment_list(identifier)
#         context["equipment_list"] = equipment_list

#         # 6. Генерация документа
#         doc = DocxTemplate(template_path)
#         doc.render(context)
#         doc.save(save_path)

#         return save_path
#     except Exception as e:
#         logger.error(f"Ошибка при генерации договора: {e}")
#         return None

def generate_contract(contracts_data, save_path, code_contract, contract_date, ppe_number):
    """
    Генерирует договор на основе шаблона для нескольких контрактов.
    Использует номер ППЭ для получения оборудования.
    """
    try:
        # 1. Проверка и настройка путей
        template_path = find_template()

        # 2. Создание директории для сохранения, если она не существует
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Проверка типа contract_date и преобразование в datetime, если это строка
        if isinstance(contract_date, str):
            contract_date = datetime.strptime(contract_date, "%d.%m.%Y")

        # Убедимся, что contract_date - это объект datetime
        if isinstance(contract_date, datetime):
            day_int = int(contract_date.day)
            month_int = int(contract_date.month)
            year_int = int(contract_date.year)
            month_rus = build_month_name_rus(month_int)

            # Подготовка контекста для шаблона
            context = {
                "code_contract": code_contract,
                "day": day_int,
                "month_name": month_rus,
                "year": year_int,
                "year_next": int(year_int) + 1,  # Увеличиваем год на 1
            }

        # 2. Формирование контекста для контрактов
        context["contracts"] = contracts_data 

        # Получаем school_id для ППЭ
        query_school_id = """
            SELECT school_id FROM dat_ppe
            WHERE id = %s
            LIMIT 1
        """
        school_id_result = execute_query(query_school_id, (ppe_number,))

        # Используем обновленный запрос с правильными именами полей
        query_details = """
            SELECT pd.school_id, pd.fullname, pd.address, pd.inn, pd.kpp, pd.okpo, pd.ogrn, pd.cur_acc, pd.bank_acc, pd.pers_acc
            FROM dat_ppe_details pd
            JOIN dat_ppe p ON pd.school_id = p.school_id
            WHERE p.school_id = %s
            LIMIT 1
        """
        details_result = execute_query(query_details, (school_id_result[0],))

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

            logger.info(f"Загружены реквизиты для school_id {school_id_result}: {context}")

        query_ppe_address = """
            SELECT ppe_address_fact FROM dat_ppe
            WHERE id = %s
        """
        address_result = execute_query(query_ppe_address, (ppe_number,))
        if address_result and len(address_result) > 0:
            context["ppe_address"] = address_result[0][0] if address_result[0][0] else ""

        try:
            # Используем ppe_id для получения списка оборудования
            equipment_list = get_equipment_list(ppe_number)  # Передаем номер ППЭ
            context["equipment_list"] = equipment_list

            if not equipment_list:
                logger.warning(f"Предупреждение: Список оборудования пуст для {ppe_number}")
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

        try:
            responsible_info = get_responsible_info_by_school_id(school_id_result[0])
            logger.info(f"Получена информация об ответственном лице по ППЭ {ppe_number}: {responsible_info}")

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
        #--------------------------------------
        # Имена
        #---------------------------------------
        "римма": "риммы",
        "майя": "майи",
        "юлия": "юлии",
        "ольга": "ольги",
        "нина": "нины",
        "богдан": "богдана",
        "юрий": "юрия",
        "станислав": "станислава",
        "игорь": "игоря",
        "лариса": "ларисы",
        "людмила": "людмилы",
        "любовь": "любови",
        "олеся": "олеси",
        "светлана": "светланы",
        "анжелика": "анжелики",
        "андрей": "андрея",
        "анастасия": "анастасии",
        "борис": "бориса",
        "мария": "марии",
        "владимир": "владимира",
        "ирина": "ирины",
        "елена": "елены",
        "виктория": "виктории",
        "анатолий": "анатолия",
        "лилия": "лилии",
        "вера": "веры",
        "екатерина": "екатерины",
        "олег": "олега",
        "геннадий": "геннадия",
        "евгения": "евгении",
        "александр": "александра",
        "наталия": "наталии",
        "валентина": "валентины",
        "наталья": "натальи",
        "надежда": "надежды",
        "сергей": "сергея",
        "алла": "аллы",
        "жанна": "жанны",
        "марина": "марины",
        "татьяна": "татьяны",
        "оксана": "оксаны",
        "константин": "константина",
        "дмитрий": "дмитрия",
        "галина": "галины",
        "иван": "ивана",
        "петр": "петра",
        "михаил": "михаила",
        "николай": "николая",
        "алексей": "алексея",
        "анна": "анны",
        # Добавляем тестовые имена
        "тест": "теста",
        #--------------------------
        # Фамилии
        #--------------------------
        "пшеничникова": "пшеничниковой",
        "пшеничников": "пшеничникова",
        "мыльцев": "мыльцева",
        "мыльцева": "мыльцевой",
        "кубанова": "кубановой",
        "кубанов": "кубанова",
        "пучинская": "пучинской",
        "пучинский": "пучинского",
        "воробьев": "воробьева",
        "воробьева": "воробьевой",
        "прошин": "прошина",
        "прошина": "прошиной",
        "королькова": "корольковой",
        "корольков": "королькова",
        "курдюмова": "курдюмовой",
        "курдюмов": "курдюмова",
        "плошкина": "плошкиной",
        "плошкин": "плошкина",
        "зубарев": "зубарева",
        "зубарева":"зубаревой",
        "бурцева": "бурцевой",
        "бурцев": "бурцева",
        "белоножкина": "белоножкиной",
        "белоножкин": "белоножкина",
        "глебова": "глебовой",
        "глебов": "глебова",
        "симонова": "симовновой",
        "симонов": "симонова",
        "чиркова": "чирковой",
        "чирков": "чиркова",
        "бирюкова": "бирюковой",
        "бирюков": "бирюкова",
        "сидоркина": "сидоркиной",
        "сидоркин": "сидоркина",
        "енин": "енина",
        "енина": "ениной",
        "тихонова": "тихоновой",
        "тихонов": "тихонова",
        "широкая": "широкой",
        "широкий": "широкого",
        "веденеева": "веденеевой",
        "веденеев": "веденеева",
        "гудкова": "гудковой",
        "гудков": "гудкова",
        "каракулин":"каракулина",
        "каракулина": "каракулиной",
        "балашова": "балашовой",
        "балашов": "балашова",
        "битков": "биткова",
        "биткова": "битковой",
        "иванова": "ивановой",
        "иванов": "иванова",
        "гордов": "гордова",
        "гордова": "гордовой",
        "наседкина": "наседкиной",
        "наседкин": "наседкина",
        "данилин": "данилина",
        "данилина": "данилиной",
        "данилин": "данилина",
        "камардина": "камардиной",
        "камардин": "камардина",
        "костельцова": "костельцовой",
        "костельцов": "костельцова",
        "матвеева": "матвеевой",
        "матвеев": "матвеева",
        "давыдова": "давыдовой",
        "давыдов": "давыдова",
        "филатов": "филатова",
        "филатова": "филатовой",
        "белова": "беловой",
        "белов": "белова",
        "венюкова": "венюковой",
        "венюков": "венюкова",
        "гончаров": "гончарова",
        "гончарова": "гончаровой",
        "табунникова": "табунниковой",
        "табунников": "табунникова",
        "ананьева": "ананьевой",
        "ананьев": "ананьева",
        "леонов": "леонова",
        "леонова": "леоновой",
        "лазарева": "лазаревой",
        "лазарев": "лазарева",
        "самойлова": "самойловой",
        "самойлов": "самойлова",
        "паин": "паина",
        "паина": "паиной",
        "родионов": "родионова",
        "родионова": "родионовой",
        "алитовская": "алитовской",
        "алитовский": "алитовского",
        "илюшечкин": "илюшечкина",
        "илюшечкина": "илюшечкиной",
        "николаева": "николаевой",
        "николаев": "николаева",
        "тарасова": "тарасовой",
        "тарасов": "тарасова",
        "ромашина": "ромашиной",
        "ромашин": "ромашина",
        "горелова": "гореловой",
        "горелов": "горелова",
        "артамонова": "артамоновой",
        "артамонов": "артамонова",
        "александрова": "александровой",
        "александров": "александрова",
        "себякина": "себякиной",
        "себякин": "себякина",
        "возвышаев": "возвышаева",
        "возвышаева": "возвышаевой",
        "астахова": "астаховой",
        "астахов": "астаховой",
        "сапегина": "сапегиной",
        "сапегин": "сапегина",
        "максаков": "максакова",
        "максакова": "максаковой",
        "медведева": "медведевой",
        "сурский": "сурского",
        "сурская": "сурской",
        "старченков": "старченкова",
        "старченкова": "старченковой",
        "алексеева": "алексеевой",
        "алексеев": "алексеева",
        "трофимова": "трофимовой",
        "трофимов": "трофимова",
        "маленков": "маленкова",
        "маленкова": "маленковой",
        "иванчикова": "иванчиковой",
        "иванчиков": "иванчикова",
        "денисова": "денисовой",
        "денисов": "денисова",
        "киселева": "киселевой",
        "киселев": "киселева",
        "чернышёва": "чернышёвой",
        "чернышёв": "чернышёва",
        "свальнова": "свальновой",
        "свальнов": "свальнова",
        "черемисинова": "черемисиновой",
        "черемисинов": "черемисинова",
        "бордашова": "бордашовой",
        "бордашов": "бордашова",
        "беломытцева": "беломытцевой",
        "беломытцев": "беломытцева",
        "полякова": "поляковой",
        "поляков": "полякова",
        "пономарев": "пономарева",
        "пономарева": "пономаревой",
        "кольцова": "кольцовой",
        "кольцов": "кольцова",
        "фуртова": "фуртовой",
        "фуртов": "фуртова",
        "гнидина": "гнидиной",
        "гнидин": "гнидина",
        "гомонова": "гомоновой",
        "гомонов": "гомонова",
        "гурьянова": "гурьяновой",
        "гурьянов": "гурьянова",
        "лобанова": "лобановой",
        "лобанов": "лобанова",
        "жемчугова": "жемчуговой",
        "жемчугов": "жемчугова",
        "башкирова": "башкировой",
        "башкиров": "башкирова",
        "алешина": "алешиной",
        "алешин": "алешина",
        "лисицына": "лисицыной",
        "лисицын": "лисицына",
        "макаров": "макарова",
        "макарова": "макаровой",
        "матвиевская": "матвиевской",
        "матвиевский": "матвиевского",
        "шевякова": "шевяковой",
        "шевяков": "шевякова",
        "бессуднова": "бессудновой",
        "бессуднов": "бессуднова",
        "трусова": "трусовой",
        "трусов": "трусова",
        "губанова": "губановой",
        "губанов": "губанова",
        "петрушин": "петрушина",
        "петрушина": "петрушиной",
        "галкина": "галкиной",
        "галкин": "галкина",
        "пятикопова": "пятикоповой",
        "пятикопов": "пятикопова"
    }

    # Словарь для отчеств
    patronymics_genitive = {
        "юрьевна": "юрьевны",
        "юрьевич": "юрьевича",
        "алексеевна": "алексеевны",
        "алексеевич": "алексеевича",
        "николаевич": "николаевича",
        "николаевна": "николаевны",
        "дмитриевич": "дмитриевича",
        "дмитриевна": "дмитриевны",
        "васильевна": "васильевны",
        "васильевич": "васильевича",
        "валентиновна": "валентиновны",
        "валентинович": "валентиновича",
        "андреевич": "андреевича",
        "андреевна": "андреевны",
        "григорьевна": "григорьевны",
        "григорьевич": "григорьевича",
        "михайлович": "михайловича",
        "михайловна": "михайловны",
        "викторович": "викторовича",
        "викторовна": "викторовны",
        "ильич": "ильича",
        "ильинична": "ильиничны",
        "дмитриевич": "дмитриевича",
        "дмитриевна": "дмитриевны",
        "владимирович": "владимировича",
        "владимировна": "владимировны",
        "валериевна": "валериевны",
        "валериевич": "валериевича",
        "егоровна": "егоровны",
        "егорович": "егоровича",
        "тимофеевна": "тимофеевны",
        "тимофеевич": "тимофеевича",
        "леонидовна": "леонидовны",
        "леонидович": "леонидовича",
        "аркадьевна": "аркадьевны",
        "аркадьевич": "аркадиевича",
        "игоревич": "игоровича",
        "игоревна": "игоревны",
        "вячеславовна": "вячеславовны",
        "вячеславович": "вячеславовича",
        "александрович": "александровича",
        "александровна": "александровны",
        "самиуловна": "самиуловны",
        "самиулович": "самиуловича",
        "георгичевич": "георгиевича",
        "георгиевна": "георгиевной",
        "витальевич": "витальевича",
        "витальевна": "витальевны",
        "константинович": "константиновича",
        "константиновна": "константиновны",
        "иванович": "ивановича",
        "ивановна": "ивановны",
        "владиславовна": "владиславовны",
        "владиславович": "владиславовича",
        "геннадьевич": "геннадьевича",
        "геннадьевна": "геннадьевны",
        "сергеевич": "сергеевича",
        "сергеевна": "сергеевны",
        "петрович": "петровича",
        "петровна": "петровны",
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

def delete_temp_file(temp_file):
    """
    Удаляет временный файл после его использования.
    """
    if temp_file and os.path.exists(temp_file):
        try:
            os.remove(temp_file)
            logger.info(f"Временный файл {temp_file} удален.")
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {e}")

