import os
from docxtpl import DocxTemplate
from datetime import datetime
import locale
import psycopg2

def connect_to_database():
    """
    Пример функции для подключения к базе.
    Настройте под ваши реквизиты.
    """
    return psycopg2.connect(
        host='192.168.1.239',
        user='postgres',
        password='AXD54^sa',
        database='equipment_ppe'
    )

def get_contract_data_from_db(contract_id):
    """
    Пример функции, которая берет информацию о договоре из БД:
    номер, дата, поставщик, заказчик, сумма и т.д.
    Возвращает словарь.
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
            "date_contract": row[1].strftime("%d.%m.%Y"),
            "name_contract": row[2]
        }
    else:
        return None
    
def get_ppe_data_from_db(contract_id):
    
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
            "date_contract": row[1].strftime("%d.%m.%Y"),
            "name_contract": row[2]
        }
    else:
        return None

def amount_to_text_rus(amount):
    """
    Простейшая функция, превращающая число
    (например, 1234.56)
    в строку "одна тысяча двести тридцать четыре рубля 56 копеек".
    Здесь дам очень упрощённую версию.
    """
    rub = int(amount)
    kop = int(round((amount - rub)*100))

    # Здесь нужна логика склонения слов "рубль"/"рубля"/"рублей", 
    # "копейка"/"копейки"/"копеек". 
    # Для упрощения возьмём самую простую форму:
    rub_word = "рублей"
    kop_word = "копеек"

    # Превращаем число rub в пропись (упрощённо).
    # Можно тут обратиться к pymorphy2, russian-num2words и т.п.
    # Пока сделаем заглушку:
    rub_str = str(rub)  # "1234"
    kop_str = f"{kop:02d}" # "05" или "56"

    return f"{rub_str} {rub_word} {kop_str} {kop_word}"


def build_month_name_rus(month_int):
    """
    Простой список месяцев по-русски. month_int: 1..12
    """
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return months[month_int - 1]

def get_equipment_list():
    """
    Выполняет запрос, возвращает список словарей,
    где каждая запись — строка в итоговой таблице (для docxtpl).
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

    # Преобразуем в список словарей:
    equipment_list = []
    for row in rows:
        equipment_list.append({
            "row_number":       row[0],  # row_num
            "equip_name":       row[1],
            "count_equip":      row[2],
            "inv_numbers":      row[3],
            "equip_price":      f"{row[4]:.2f}",
            "total_price":      f"{row[5]:.2f}"
        })
    return equipment_list


def generate_contract(contract_id):
    """
    Основная функция, которая на основе template_contract.docx
    формирует итоговый .docx-договор с подстановкой данных из БД 
    и системных переменных.
    """
    template_path = "Z://Sofia//template.docx"
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Шаблон не найден: {template_path}")

    # total_price_text = amount_to_text_rus(total_price)

    # 1) Берём данные договора из БД
    contract_data = get_contract_data_from_db(contract_id)
    if not contract_data:
        print(f"Не найден договор с ID={contract_id}")
        return

    ppe_data = get_ppe_data_from_db(contract_id)
    if not contract_data:
        print(f"Не найден ППЭ по договору с ID={contract_id}")
        return
    # 2) Формируем системную дату (сегодня) 
    #    Допустим, нужна дата в русском формате
    now = datetime.now()
    day_int = now.day
    month_int = now.month
    year_int = now.year
    month_rus = build_month_name_rus(month_int)  # «октября», «мая» и т.д.

    # 3) Заполняем контекст
    context = {
        # Поля из базы
        "num_contract": contract_data["num_contract"],
        "date_contract": contract_data["date_contract"],
        "name_contract": contract_data["name_contract"],
        # Дата договора 
        # Если хотите взять дату договора из БД, 
        # можно contract_data["contract_date"], но тогда тоже склоняйте / форматируйте
        # Для примера берем today's date
        "day": day_int,
        "month_name": month_rus,
        "year": year_int,
        "year_next": year_int + 1,
        "code_contract": " ",

        # Или contract_data["contract_date"] if you want 
    }

    equipment_list = get_equipment_list()

    # Добавляем в context, чтобы docxtpl видел
    context["equipment_list"] = equipment_list

    # 4) Загружаем шаблон docx и рендерим
    doc = DocxTemplate(template_path)
    doc.render(context)

    # 5) Сохраняем итог
    output_name = f"Договор_{contract_data['num_contract']}.docx"
    doc.save(output_name)
    print(f"Сформирован {output_name}")

if __name__ == "__main__":
    # Пример
    generate_contract(contract_id=1)  # Допустим, договор ID=101
