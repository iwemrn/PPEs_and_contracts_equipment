from datetime import datetime

now = datetime.now()    # Текущие дата и время
print(now)              # Например, 2023-10-02 16:32:47.123456

current_day = now.day   # День месяца (число)
current_month = now.month
current_year = now.year

print(f"День: {current_day}, Месяц: {current_month}, Год: {current_year}")
