"""
Модуль с утилитами для работы с пользовательским интерфейсом.
"""

import os
import tkinter as tk
import logging
from tkinter import messagebox, filedialog, simpledialog, ttk
from datetime import datetime
from database import update_equipment_agreement, check_agreement_exists, get_contract_data_by_id, get_contract_id_for_ppe
import shutil
import platform
import subprocess

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger('utils')

def toggle_ppe_list(app):
    """Скрытие/показ списка ППЭ."""
    if not hasattr(app, 'ppe_list_visible'):
        app.ppe_list_visible = True  # инициализация, если нет атрибута

    if app.ppe_list_visible:
        app.frame_ppe_list.pack_forget()
        app.ppe_list_visible = False
    else:
        app.frame_ppe_list.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        app.ppe_list_visible = True

    # Меняем надпись в меню
    menubar = app.root.nametowidget(app.root.winfo_children()[0])
    view_menu = menubar.winfo_children()[1]  # второй элемент в меню
    view_menu.entryconfig(0, label="Показать список ППЭ" if not app.ppe_list_visible else "Скрыть список ППЭ")

def toggle_pdf_visibility(app):
    """Скрытие/показ PDF."""
    if app.pdf_frame.winfo_ismapped():
        app.pdf_frame.pack_forget()
    else:
        app.pdf_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)

def create_invisible_scrolled_area(parent):
    """
    Создаёт Canvas + Frame без видимого Scrollbar,
    но позволяет колесом мыши прокручивать содержимое.
    
    Returns:
        tuple: (canvas, scrollable_frame)
    """
    canvas = tk.Canvas(parent, highlightthickness=0)  # нет рамки
    canvas.pack(fill="both", expand=True)

    scrollable_frame = tk.Frame(canvas)
    # Размещаем фрейм в Canvas
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Обновляем scrollregion при изменении размеров scrollable_frame
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", on_configure)

    # Прокрутка колесиком (Windows вариант)
    def on_mousewheel(event):
        # Умножаем delta на -1,  /120 обычно (±120), /60, /90 — экспериментально
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # Чтобы ловить колесико, нужно, чтобы фрейм имел фокус
    scrollable_frame.bind("<MouseWheel>", on_mousewheel)
    scrollable_frame.focus_set()

    return canvas, scrollable_frame

def validate_contract_details(code_contract, contract_date):
    """Проверяет правильность введённого номера договора и даты."""
    if not code_contract or not code_contract.strip():
        messagebox.showerror("Ошибка", "Номер договора не может быть пустым.")
        return False

    try:
        datetime.strptime(contract_date, "%d.%m.%Y")
    except ValueError:
        messagebox.showerror("Ошибка", "Дата должна быть в формате ДД.ММ.ГГГГ.")
        return False
    
    return True

def on_download_contract(app):
    """Обработчик для скачивания договора."""
    selected_item = app.ppe_list.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Сначала выберите ППЭ.")
        return
    
    ppe_id = app.ppe_list.item(selected_item, "values")[0]
    
    # Проверяем наличие поля agreement через contract_id в таблице equip_data
    agreement_exists = check_agreement_exists(ppe_id)

    code_contract = None
    contract_date = None

    if agreement_exists:
        # Если договор существует, извлекаем его данные с использованием contract_id
        contract_id = get_contract_id_for_ppe(ppe_id)  # Функция для получения contract_id из equip_data
        if contract_id:
            contract_data = get_contract_data_by_id(contract_id)  # Функция для получения данных о контракте по contract_id
            if contract_data:
                code_contract = contract_data['num_contract']
                contract_date = contract_data['date_contract']
                # Показываем существующий договор
                messagebox.showinfo("Предпросмотр договора", f"Номер договора: {code_contract}\nДата договора: {contract_date}")
            else:
                messagebox.showerror("Ошибка", "Не удалось получить данные о договоре.")
                return
        else:
            messagebox.showerror("Ошибка", "Не найден contract_id для ППЭ.")
            return
    else:
        # Запрос номера и даты договора
        contract_details = ask_contract_details()
        if contract_details is None:
            messagebox.showwarning("Отмена", "Сохранение договора отменено пользователем.")
            return

        code_contract = contract_details["code_contract"]
        contract_date = contract_details["date"]
        
        # Валидация данных
        if not validate_contract_details(code_contract, contract_date):
            return

        # Обновляем поле agreement в базе данных
        agreement_exists = update_equipment_agreement(ppe_id, code_contract, datetime.strptime(contract_date, "%d.%m.%Y").year)

    save_path = filedialog.asksaveasfilename(
        defaultextension=".docx",
        filetypes=[("Word Document", "*.docx")],
        title="Сохранить договор"
    )

    if save_path:
        # Создаем окно с прогресс-баром
        loading_window = tk.Toplevel(app.root)
        loading_window.title("Генерация договора")
        loading_window.geometry("300x150")
        loading_window.transient(app.root)
        loading_window.grab_set()

        # Центрируем окно
        loading_window.update_idletasks()
        width = loading_window.winfo_width()
        height = loading_window.winfo_height()
        x = (loading_window.winfo_screenwidth() // 2) - (width // 2)
        y = (loading_window.winfo_screenheight() // 2) - (height // 2)
        loading_window.geometry(f"{width}x{height}+{x}+{y}")

        # Прогрессбар
        progress = ttk.Progressbar(loading_window, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20, pady=10)
        progress.start()

        # Функция для завершения
        def finish_generation():
            progress.stop()
            loading_window.destroy()
            messagebox.showinfo("Успех", f"Файл сохранён:\n{save_path}")

        try:
            from contracts import generate_contract
            result = generate_contract(
                [{"num_contract": code_contract, "date_contract": contract_date, "name_contract": contract_name}],  # Передаем данные о контракте как список
                save_path,
                code_contract,
                contract_date,
                ppe_id
            )

            # Завершаем процесс
            if result:
                finish_generation()
            else:
                messagebox.showerror("Ошибка", "Не удалось сгенерировать договор")
                loading_window.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при генерации договора: {str(e)}")
            loading_window.destroy()

def show_save_path(self, path):
    """Показывает путь сохранения файла в интерфейсе."""
    # Удалим старую метку, если есть
    for widget in self.pdf_buttons_frame.winfo_children():
        if getattr(widget, "tag", None) == "save_path_label":
            widget.destroy()

    label = tk.Label(self.pdf_buttons_frame, text=f"Сохранено: {path}", fg="blue")
    label.tag = "save_path_label"
    label.pack(side=tk.LEFT, padx=5)

def open_document(file_path):
    """Открывает документ в системном приложении без блокировки."""
    import subprocess
    import os
    import platform
    
    try:
        if platform.system() == 'Windows':
            # Используем subprocess вместо os.startfile для неблокирующего открытия
            subprocess.Popen(f'start "" "{file_path}"', shell=True)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', file_path])
        else:  # Linux
            subprocess.Popen(['xdg-open', file_path])
        return True
    except Exception as e:
        print(f"Ошибка при открытии файла: {str(e)}")
        return False

def show_save_dialog(app, ppe_id, temp_file):
    """Показывает диалог с вопросом о сохранении договора."""
    save_dialog = tk.Toplevel(app.root)
    save_dialog.title("Сохранение договора")
    save_dialog.geometry("300x120")
    save_dialog.resizable(False, False)
    save_dialog.transient(app.root)
    save_dialog.grab_set()
    
    # Центрируем окно
    center_window(save_dialog)
    
    # Текст вопроса
    tk.Label(save_dialog, text="Сохранить договор?", font=("Arial", 12)).pack(pady=15)
    
    # Кнопки "Да" и "Нет"
    button_frame = tk.Frame(save_dialog)
    button_frame.pack(pady=10)
    
    yes_button = tk.Button(
        button_frame, 
        text="Да", 
        font=("Arial", 12), 
        command=lambda: handle_save_yes(app, ppe_id, temp_file, save_dialog), 
        width=8
    )
    yes_button.pack(side=tk.LEFT, padx=10)
    
    no_button = tk.Button(
        button_frame, 
        text="Нет", 
        font=("Arial", 12), 
        command=lambda: handle_save_no(temp_file, save_dialog), 
        width=8
    )
    no_button.pack(side=tk.LEFT, padx=10)

def handle_save_yes(app, ppe_id, temp_file, dialog):
    """Обработчик нажатия кнопки 'Да' в диалоге сохранения."""
    dialog.destroy()
    show_contract_details_dialog(app, ppe_id, temp_file)

def handle_save_no(temp_file, dialog):
    """Обработчик нажатия кнопки 'Нет' в диалоге сохранения."""
    dialog.destroy()
    # Удаляем временный файл
    try:
        os.remove(temp_file)
    except Exception as e:
        logger.error(f"Ошибка при удалении временного файла: {e}")

def center_window(window):
    """Центрирует окно на экране."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def show_contract_details_dialog(app, ppe_id, temp_file):
    """Показывает диалог для ввода деталей договора."""
    dialog = tk.Toplevel(app.root)
    dialog.title("Данные договора")
    dialog.geometry("400x200")
    dialog.resizable(False, False)
    dialog.transient(app.root)
    dialog.grab_set()
    
    # Центрируем окно
    center_window(dialog)
    
    # Создаем и размещаем элементы формы
    tk.Label(dialog, text="Номер договора:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    contract_number_entry = tk.Entry(dialog, font=("Arial", 12), width=20)
    contract_number_entry.grid(row=0, column=1, padx=10, pady=10)
    contract_number_entry.insert(0, f"ППЭ-{ppe_id}")
    
    tk.Label(dialog, text="Дата договора:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
    
    today = datetime.now().strftime("%d.%m.%Y")
    contract_date_entry = tk.Entry(dialog, font=("Arial", 12), width=20)
    contract_date_entry.grid(row=1, column=1, padx=10, pady=10)
    contract_date_entry.insert(0, today)
    
    # Кнопки "Сохранить" и "Отмена"
    button_frame = tk.Frame(dialog)
    button_frame.grid(row=2, column=0, columnspan=2, pady=20)
    
    save_button = tk.Button(
        button_frame, 
        text="Сохранить", 
        font=("Arial", 12), 
        command=lambda: save_contract_details(
            app, ppe_id, temp_file, dialog, 
            contract_number_entry.get().strip(), 
            contract_date_entry.get().strip()
        ), 
        width=10
    )
    save_button.pack(side=tk.LEFT, padx=10)
    
    cancel_button = tk.Button(
        button_frame, 
        text="Отмена", 
        font=("Arial", 12), 
        command=dialog.destroy, 
        width=10
    )
    cancel_button.pack(side=tk.LEFT, padx=10)
    
    # Фокус на первое поле ввода
    contract_number_entry.focus_set()

def save_contract_details(app, ppe_id, temp_file, dialog, contract_number, contract_date):
    """Проверяет и сохраняет детали договора."""
    # Проверка ввода
    if not contract_number:
        messagebox.showerror("Ошибка", "Введите номер договора", parent=dialog)
        return
    
    # Проверка формата даты
    from contracts import validate_contract_date
    if not validate_contract_date(contract_date):
        messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ", parent=dialog)
        return
    
    # Закрываем диалог
    dialog.destroy()
    
    # Запрашиваем путь для сохранения и сохраняем файл
    save_contract_file(app, ppe_id, temp_file, contract_number, contract_date)

def save_contract_file(app, ppe_id, temp_file, contract_number, contract_date):
    """Запрашивает путь и сохраняет файл договора."""
    # Запрашиваем путь для сохранения
    save_path = filedialog.asksaveasfilename(
        defaultextension=".docx",
        filetypes=[("Word Documents", "*.docx")],
        initialfile=f"Договор_{contract_number}.docx"
    )
    
    if not save_path:
        return  # Пользователь отменил
    
    try:
        # Копируем временный файл
        shutil.copy2(temp_file, save_path)
        
        # Получаем год из даты договора
        contract_year = datetime.strptime(contract_date, "%d.%m.%Y").year
        
        affected_rows = update_equipment_agreement(ppe_id, contract_number, contract_year)
        
        # Сохраняем данные договора в базу данных
        from database import save_contract_data
        save_contract_data(ppe_id, contract_number, contract_date)
        
        messagebox.showinfo(
            "Успех", 
            f"Договор сохранен: {save_path}\n"
            f"Обновлено записей оборудования: {affected_rows}"
        )
        
        # Удаляем временный файл
        try:
            os.remove(temp_file)
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {e}")
            
    except Exception as e:
        logger.error(f"Ошибка при сохранении договора: {e}")
        messagebox.showerror("Ошибка", f"Ошибка при сохранении договора: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def ask_contract_details():
    """
    Открывает окно для ввода номера договора и даты.
    
    Returns:
        dict: Словарь с данными договора или None, если отменено
    """
    root = tk.Tk()
    root.withdraw()  # Скрыть главное окно

    code_contract = simpledialog.askstring("Номер договора", "Введите номер договора:")
    if not code_contract:
        return None

    date_str = simpledialog.askstring("Дата договора", "Введите дату договора в формате ДД.ММ.ГГГГ:")
    if not date_str:
        return None

    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
        return {
            "code_contract": code_contract,
            "date": date_str,
            "name": name,
        }
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат даты. Ожидается: ДД.ММ.ГГГГ")
        return None

def show_contract_input_dialog(app, ppe_id):
    """
    Показывает диалоговое окно для ввода данных договора.
    
    Returns:
        dict: Словарь с данными договора или None, если отменено
    """
    dialog = tk.Toplevel(app.root)
    dialog.title("Данные договора")
    dialog.geometry("400x200")
    dialog.resizable(False, False)
    dialog.transient(app.root)
    dialog.grab_set()
    
    # Центрируем окно
    center_window(dialog)
    
    # Переменная для хранения результата
    result = {"confirmed": False, "number": "", "date": ""}
    
    # Создаем и размещаем элементы формы
    tk.Label(dialog, text="Номер договора:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    contract_number_entry = tk.Entry(dialog, font=("Arial", 12), width=20)
    contract_number_entry.grid(row=0, column=1, padx=10, pady=10)
    contract_number_entry.insert(0, f"ППЭ-{ppe_id}")
    
    tk.Label(dialog, text="Дата договора:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
    
    today = datetime.now().strftime("%d.%m.%Y")
    contract_date_entry = tk.Entry(dialog, font=("Arial", 12), width=20)
    contract_date_entry.grid(row=1, column=1, padx=10, pady=10)
    contract_date_entry.insert(0, today)
    
    def on_confirm():
        number = contract_number_entry.get().strip()
        date = contract_date_entry.get().strip()
        
        # Проверка ввода
        if not number:
            messagebox.showerror("Ошибка", "Введите номер договора", parent=dialog)
            return
        
        # Проверка формата даты
        from contracts import validate_contract_date
        if not validate_contract_date(date):
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ", parent=dialog)
            return
        
        # Сохраняем результат и закрываем диалог
        result["confirmed"] = True
        result["number"] = number
        result["date"] = date
        dialog.destroy()
    
    def on_cancel():
        dialog.destroy()
    
    # Кнопки "Подтвердить" и "Отмена"
    button_frame = tk.Frame(dialog)
    button_frame.grid(row=2, column=0, columnspan=2, pady=20)
    
    confirm_button = tk.Button(button_frame, text="Подтвердить", font=("Arial", 12), command=on_confirm, width=12)
    confirm_button.pack(side=tk.LEFT, padx=10)
    
    cancel_button = tk.Button(button_frame, text="Отмена", font=("Arial", 12), command=on_cancel, width=10)
    cancel_button.pack(side=tk.LEFT, padx=10)
    
    # Фокус на первое поле ввода
    contract_number_entry.focus_set()
    
    # Ждем, пока пользователь закроет диалоговое окно
    app.root.wait_window(dialog)
    
    # Возвращаем результат
    return result if result["confirmed"] else None

def show_loading_indicator(app, message="Загрузка..."):
    """Показывает индикатор загрузки."""
    label = tk.Label(app.root, text=message, font=("Arial", 10, "italic"))
    label.pack(side=tk.BOTTOM, pady=5)
    app.root.update()  # Обновляем UI
    return label

def hide_loading_indicator(label):
    """Скрывает индикатор загрузки."""
    if label:
        label.destroy()
