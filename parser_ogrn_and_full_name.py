import time
import psycopg2

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Инициализация драйвера
driver = webdriver.Chrome()

def get_inn_list_from_db():
    conn = psycopg2.connect(
        host='192.168.1.239',
        user='postgres',
        password='AXD54^sa',
        database='equipment_ppe'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT inn FROM dat_ppe_details WHERE fullname is NULL")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # rows — [(inn,), (inn2,), ...]
    inn_list = [row[0] for row in rows if row[0]]
    return inn_list

def update_data_in_db(inn, name, kpp, ogrn, okpo):
    conn = psycopg2.connect(
        host='192.168.1.239',
        user='postgres',
        password='AXD54^sa',
        database='equipment_ppe'
    )
    cursor = conn.cursor()
    query = """
        UPDATE dat_ppe_details
        SET fullname = %s,
            kpp = %s,
            ogrn = %s,
            okpo = %s
        WHERE inn = %s
    """
    cursor.execute(query, (name, kpp, ogrn, okpo, inn))
    conn.commit()
    cursor.close()
    conn.close()

driver.get("https://focus.kontur.ru/site")

# Явное ожидание до 20 сек.
wait = WebDriverWait(driver, 20)

def process_data_by_inn(tin):
    """
    1. Вводим ИНН, жмём поиск.
    2. Появляется вторая вкладка -> переключаемся.
    3. Ищем данные, если их нет — None.
    """
    try:
        # Ждём, пока поле для ввода станет кликабельным
        input_field = wait.until(
            EC.element_to_be_clickable((By.XPATH,
              '//*[@id="pageWrapper"]/div/main/div/div/div[2]/div[3]/section[1]/div[1]/div/div/div/div[1]/div/div/div/form/div/input'))
        )
        input_field.clear()
        input_field.send_keys(tin)

        # Кнопка поиска
        search_button = driver.find_element(
            By.XPATH,
            '//*[@id="pageWrapper"]/div/main/div/div/div[2]/div[3]/section[1]/div[1]/div/div/div/div[1]/div/div/div/form/div/span/button'
        )
        search_button.click()

        # Дадим время на переключение вкладок
        time.sleep(5)

        if len(driver.window_handles) < 2:
            print(f"Вторая вкладка не открылась для ИНН={tin}")
            return None

        # Переключаемся на вторую вкладку
        driver.switch_to.window(driver.window_handles[1])

        try:
            # Ждём появления блока org-content (или таймаут)
            wait.until(EC.presence_of_element_located((By.ID, "org-content")))
        except TimeoutException:
            print(f"Блок org-content не появился, возможно нет данных или капча. ИНН={tin}")
            return None

        # Теперь пытаемся найти нужные поля:
        try:
            name = driver.find_element(
                By.XPATH,
                '//*[@id="org-content"]/div/div/div[1]/div/div/div/div[1]/div/div/div/span[1]/span/div/div/span/h2'
            ).text
        except NoSuchElementException:
            print(f"Нет элемента name (h2). ИНН={tin}")
            return None

        try:
            kpp = driver.find_element(
                By.XPATH, 
                '//*[@id="org-content"]/div/div/div[1]/div/div/div/div[3]/div/div/div/table/tbody/tr[2]/td[2]/div/span/span/div/div/span'
            ).text
        except NoSuchElementException:
            print(f"Нет элемента kpp. ИНН={tin}")
            return None

        try:
            ogrn = driver.find_element(
                By.XPATH, 
                '//*[@id="org-content"]/div/div/div[1]/div/div/div/div[3]/div/div/div/table/tbody/tr[3]/td[2]/div/span/span/div/div/span'
            ).text
        except NoSuchElementException:
            print(f"Нет элемента ogrn. ИНН={tin}")
            return None

        # okpo может отсутствовать
        try:
            okpo = driver.find_element(
                By.XPATH,
                '//*[@id="org-content"]/div/div/div[1]/div/div/div/div[15]/div/div/div/div/table/tbody/tr[1]/td[2]/div/span/span/div/div/span'
            ).text
        except NoSuchElementException:
            okpo = '1'  # Если хотите не пропускать запись (NOT NULL), поставьте заглушку

        # Преобразуем в int
        try:
            kpp = int(kpp)
            ogrn = int(ogrn)
            okpo = int(okpo)
        except ValueError:
            print(f"Не все поля (kpp/ogrn/okpo) удалось привести к int. ИНН={tin}")
            return None

        return {"inn": tin, "name": name, "kpp": kpp, "ogrn": ogrn, "okpo": okpo}

    finally:
        # Закрываем вторую вкладку, переключаемся обратно
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)

inn_list = get_inn_list_from_db()
print("ИНН из БД:", inn_list)

for tin in inn_list:
    data = process_data_by_inn(tin)
    if data:
        print(f"Получены данные: {data}")
        update_data_in_db(tin, data['name'], data['kpp'], data['ogrn'], data['okpo'])
    else:
        print(f"Данные не получены для ИНН={tin} — пропускаем.")

driver.quit()
