import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from datetime import datetime
from contracts import generate_contract
from database import check_agreement_exists

def toggle_ppe_list(app):
    """Скрытие/показ списка ППЭ"""
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
    """Скрытие/показ PDF"""
    if app.pdf_frame.winfo_ismapped():
        app.pdf_frame.pack_forget()
    else:
        app.pdf_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)

# пока не трогать, с заглушками
def add_ppe():
    """Добавление нового ППЭ"""
    messagebox.showinfo("Добавить ППЭ", "Функция добавления ППЭ в разработке.")

def edit_ppe():
    """Редактирование ППЭ"""
    messagebox.showinfo("Редактировать ППЭ", "Функция редактирования ППЭ в разработке.")

def delete_ppe():
    """Удаление ППЭ"""
    messagebox.showinfo("Удалить ППЭ", "Функция удаления ППЭ в разработке.")

def create_invisible_scrolled_area(parent):
    """
    Создаёт Canvas + Frame без видимого Scrollbar,
    но позволяет колесом мыши прокручивать содержимое.
    Возвращает (canvas, scrollable_frame), внутри которого можно размещать виджеты.
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

def on_download_contract(app):
    selected_item = app.ppe_list.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Сначала выберите ППЭ.")
        return
    ppe_id = app.ppe_list.item(selected_item, "values")[0]
    # Проверяем наличие поля agreement
    agreement_exists = check_agreement_exists(ppe_id)

    code_contract = None
    contract_date = None

    if agreement_exists:
        # Запрос номера и даты договора
        result = ask_contract_details()
        if result is None:
            messagebox.showwarning("Отмена", "Сохранение договора отменено пользователем.")
            return
        code_contract, contract_date = result

    save_path = filedialog.asksaveasfilename(
        defaultextension=".docx",
        filetypes=[("Word Document", "*.docx")],
        title="Сохранить договор"
    )

    if save_path:
        try:
            generate_contract(
                ppe_number=ppe_id,
                save_path=save_path,
                code_contract=code_contract,
                contract_date=contract_date
            )
            messagebox.showinfo("Успех", f"Файл сохранён:\n{save_path}")
            if hasattr(app, "_show_save_path"):
                app._show_save_path(save_path)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

def show_save_path(self, path):
    # Удалим старую метку, если есть
    for widget in self.pdf_buttons_frame.winfo_children():
        if getattr(widget, "tag", None) == "save_path_label":
            widget.destroy()

    label = tk.Label(self.pdf_buttons_frame, text=f"Сохранено: {path}", fg="blue")
    label.tag = "save_path_label"
    label.pack(side=tk.LEFT, padx=5)

def on_preview_contract_click(app):
    selected = app.ppe_list.selection()
    if not selected:
        messagebox.showerror("Ошибка", "Сначала выберите ППЭ.")
        return
    ppe_number = app.ppe_list.item(selected, "values")[0]
    # Делаем, например, окно Toplevel и показываем, что будет в договоре.
    # ...

def ask_contract_details():
    """
    Открывает окно для ввода номера договора и даты.
    Возвращает словарь вида:
    {
        'code_contract': 'ДОГ-123',
        'day': 1,
        'month_name': 'января',
        'year': 2025
    }
    или None, если отменено.
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
        months_rus = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        return {
            "code_contract": code_contract,
            "day": date_obj.day,
            "month_name": months_rus[date_obj.month - 1],
            "year": date_obj.year
        }
    except ValueError:
        tk.messagebox.showerror("Ошибка", "Неверный формат даты. Ожидается: ДД.ММ.ГГГГ")
        return None