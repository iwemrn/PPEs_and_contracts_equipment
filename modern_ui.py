"""
модуль нового интерфейса для работы с ППЭ
"""

import tkinter as tk
import logging
import io
from tkinter import ttk, messagebox
import ttkthemes
from PIL import Image, ImageTk
import os
from database import connect_to_database, get_ppe_list, show_equipment, show_contracts
from contracts import generate_contract, get_contract_data_from_db
from utils import show_contract_input_dialog, open_document, show_save_dialog

# Настройка логирования
logger = logging.getLogger('contracts')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ModernPPEApp:
    def __init__(self, root):
        self.root = root
        self._initialize_window()
        self.connection = connect_to_database()
        self._initialize_variables()
        self._create_ui()

        # self.contracts_tree = ttk.Treeview(self.root, columns=("Дата", "Номер", "Наименование", "Поставщик", "ИНН", "Описание"), show="headings")
        # self.contracts_tree.heading("Дата", text="Дата")
        # self.contracts_tree.heading("Номер", text="Номер")
        # self.contracts_tree.heading("Наименование", text="Наименование")
        # self.contracts_tree.heading("Поставщик", text="Поставщик")
        # self.contracts_tree.heading("ИНН", text="ИНН")
        # self.contracts_tree.heading("Описание", text="Описание")


    """Настройка параметров главного окна приложения."""        
    def _initialize_window(self):
        self.root.title("Система управления ППЭ")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 768)
        
        self.style = ttkthemes.ThemedStyle(self.root)
        self.style.set_theme("arc")  # либо adapta, либо arc.
        
        # Настраиваем стили
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("Subheader.TLabel", font=("Segoe UI", 12))
        self.style.configure("Sidebar.TFrame", background="#f0f0f0")
        self.style.configure("Content.TFrame", background="#ffffff")

    """Создание современного пользовательского интерфейса."""          
    def _create_ui(self):
        # Основной контейнер с разделением на области
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель (сайдбар)
        self.sidebar = ttk.Frame(self.main_paned, style="Sidebar.TFrame")
        self.main_paned.add(self.sidebar, weight=1)
        
        # Правая панель (основной контент)
        self.content_frame = ttk.Frame(self.main_paned, style="Content.TFrame")
        self.main_paned.add(self.content_frame, weight=3)
        
        # Создаем компоненты интерфейса
        self._create_sidebar()
        self._create_content_area()

    def _initialize_variables(self):
        self.pdf_directory = "Z:\\_ГИА_2025\\Планы БТИ\\Планы"
        self.pdf_document = None
        self.current_pdf_path = ""
        self.current_ppe = None
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_ppe_list)
        
        # Добавляем переменную для фильтра по типу ГИА
        self.gia_filter = tk.IntVar(value=0)  # 0 - все, 1 - ЕГЭ, 3 - ОГЭ, 2 - ГВЭ (в разработке)

    """Создание боковой панели с поиском и списком ППЭ."""
    def _create_sidebar(self):
        # Заголовок
        ttk.Label(self.sidebar, text="Пункты проведения экзаменов", 
                style="Header.TLabel").pack(pady=10, padx=10)
        
        # Фильтр по типу ГИА
        filter_frame = ttk.LabelFrame(self.sidebar, text="Фильтр по типу ГИА")
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Radiobutton(
            filter_frame, 
            text="Все ППЭ", 
            variable=self.gia_filter, 
            value=0,
            command=self._refresh_ppe_list
        ).pack(anchor="w", padx=10, pady=2)
        
        ttk.Radiobutton(
            filter_frame, 
            text="Только ЕГЭ", 
            variable=self.gia_filter, 
            value=1,
            command=self._refresh_ppe_list
        ).pack(anchor="w", padx=10, pady=2)
        
        ttk.Radiobutton(
            filter_frame, 
            text="Только ОГЭ", 
            variable=self.gia_filter, 
            value=3,
            command=self._refresh_ppe_list
        ).pack(anchor="w", padx=10, pady=2)
        
        # Поле поиска
        search_frame = ttk.Frame(self.sidebar)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Кнопки управления
        btn_frame = ttk.Frame(self.sidebar)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Добавить", command=self.add_ppe).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Изменить", command=self.edit_ppe).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_ppe).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить", command=self._refresh_ppe_list).pack(side=tk.LEFT, padx=2)
        
        # Список ППЭ
        list_frame = ttk.Frame(self.sidebar)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Создаем Treeview для списка ППЭ с улучшенным стилем
        columns = ("ppe_number", "ppe_address")
        self.ppe_list = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Настраиваем заголовки и колонки
        self.ppe_list.heading("ppe_number", text="№ ППЭ")
        self.ppe_list.heading("ppe_address", text="Адрес ППЭ")
        self.ppe_list.column("ppe_number", width=80, anchor="center")
        self.ppe_list.column("ppe_address", width=250, anchor="w")
        
        # Добавляем скроллбары
        y_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.ppe_list.yview)
        self.ppe_list.configure(yscrollcommand=y_scrollbar.set)
        
        # Размещаем элементы
        self.ppe_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязываем обработчик выбора
        self.ppe_list.bind("<<TreeviewSelect>>", self._on_ppe_select)
        
        # Загружаем данные
        self._load_ppe_list()

    """Загрузка списка ППЭ из базы с учетом фильтра по типу ГИА."""
    def _load_ppe_list(self):
        # Очищаем текущий список
        for item in self.ppe_list.get_children():
            self.ppe_list.delete(item)
            
        try:
            # Получаем выбранный фильтр
            gia_filter = self.gia_filter.get()
            
            if gia_filter == 0:  # Все ППЭ
                # Используем стандартную функцию получения всех ППЭ
                rows = get_ppe_list()
            else:
                # Запрос с фильтрацией по типу ГИА
                query = """
                    SELECT id, ppe_address_fact 
                    FROM dat_ppe 
                    WHERE gia_type = %s
                    ORDER BY id
                """
                from database import execute_query
                rows = execute_query(query, (gia_filter,))
            
            for row in rows:
                self.ppe_list.insert("", tk.END, values=row)
                
            # Обновляем заголовок с количеством ППЭ
            gia_type_text = "Все ППЭ"
            if int(gia_filter) == 1:
                gia_type_text = "ППЭ ЕГЭ"
            elif int(gia_filter) == 3:
                gia_type_text = "ППЭ ОГЭ"
                
            count = len(rows)
            ttk.Label(self.sidebar, text=f"{gia_type_text}: {count}", 
                    style="Subheader.TLabel").pack(pady=5, padx=10, before=self.ppe_list.master)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список ППЭ: {str(e)}")

    """Фильтрация списка ППЭ по поисковому запросу с учетом типа ГИА."""
    def _filter_ppe_list(self, *args):
        search_term = self.search_var.get().lower()
        gia_filter = self.gia_filter.get()
        
        # Очищаем текущий список
        for item in self.ppe_list.get_children():
            self.ppe_list.delete(item)
            
        try:
            if gia_filter == 0:
                # Базовый запрос без фильтра по типу ГИА
                base_query = """
                    SELECT id, ppe_address_fact 
                    FROM dat_ppe 
                    ORDER BY id
                """
                from database import execute_query
                rows = execute_query(base_query)
            else:
                # Запрос с фильтром по типу ГИА
                filtered_query = """
                    SELECT id, ppe_address_fact 
                    FROM dat_ppe 
                    WHERE gia_type = %s
                    ORDER BY id
                """
                from database import execute_query
                rows = execute_query(filtered_query, (gia_filter,))
            
            # Применяем поисковый фильтр
            for row in rows:
                # Проверяем, содержит ли номер или адрес ППЭ поисковый запрос
                if (search_term in str(row[0]).lower() or 
                    search_term in str(row[1]).lower()):
                    self.ppe_list.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при фильтрации списка: {str(e)}")
    
    """Обновление списка ППЭ с учетом текущего фильтра."""
    def _refresh_ppe_list(self):
        # Удаляем предыдущую метку с количеством ППЭ, если она есть
        for widget in self.sidebar.winfo_children():
            if isinstance(widget, ttk.Label) and widget.cget("text").startswith(("Все ППЭ:", "ППЭ ЕГЭ:", "ППЭ ОГЭ:")):
                widget.destroy()
        
        self._load_ppe_list()
    
        # Сбрасываем поисковый запрос
        self.search_var.set("")

    """Создание основной области контента с вкладками."""
    def _create_content_area(self):
        # Создаем вкладки для разных типов информации
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка "Общая информация"
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="Общая информация")
        
        # Вкладка "Оборудование"
        self.equipment_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.equipment_frame, text="Оборудование")
        
        # Вкладка "Контракты"
        self.contracts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.contracts_frame, text="Контракты")
        
        # Вкладка "Планы помещений"
        self.plans_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.plans_frame, text="Планы помещений")
        
        # # Создаем заглушку для начального экрана
        # self._create_welcome_screen()
        
    def _on_ppe_select(self, event):
        selected_items = self.ppe_list.selection()
        if not selected_items:
            return
        
        # Получаем данные выбранного ППЭ
        item = selected_items[0]
        ppe_number, ppe_address = self.ppe_list.item(item, "values")
        self.current_ppe = ppe_number
        
        # Получаем school_id для этого ППЭ
        school_id = self._get_school_id_by_ppe_number(ppe_number)
        
        # Обновляем информацию на вкладках, передавая school_id
        self._update_info_tab(ppe_number, ppe_address, school_id)
        self._update_equipment_tab(ppe_number)
        self._update_contracts_tab(ppe_number)
        self._update_plans_tab(ppe_number)

    def _get_school_id_by_ppe_number(self, ppe_number):
        """Получает school_id для выбранного ППЭ из базы данных."""
        query = """
            SELECT school_id 
            FROM dat_ppe 
            WHERE ppe_number = %s
        """
        from database import execute_query
        result = execute_query(query, (ppe_number,))
        
        if result and len(result) > 0:
            return result[0][0]  # Возвращаем school_id
        else:
            return None  # Если не найден, возвращаем None

    """Преобразует числовой код типа ГИА в текстовое представление."""
    def _get_gia_type_name(self, gia_type):
        if int(gia_type) == 1:
            return "ЕГЭ"
        elif int(gia_type) == 3:
            return "ОГЭ"
        elif int(gia_type) == 2:
            return f"ГВЭ (в разработке)"
        else:
            return f"Неизвестный тип ({gia_type})"

    """Обновление вкладки с общей информацией."""
    def _update_info_tab(self, ppe_number, ppe_address, school_id):
        # Очищаем текущее содержимое
        for widget in self.info_frame.winfo_children():
            widget.destroy()
                
        # Создаем прокручиваемую область
        canvas = tk.Canvas(self.info_frame)
        scrollbar = ttk.Scrollbar(self.info_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
            
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
            
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
            
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
            
        # Заголовок
        ttk.Label(
            scrollable_frame, 
            text=f"ППЭ №{ppe_number}", 
            style="Header.TLabel"
        ).pack(anchor="w", padx=20, pady=(20, 10))
            
        ttk.Label(
            scrollable_frame, 
            text=f"Адрес: {ppe_address}", 
            style="Subheader.TLabel"
        ).pack(anchor="w", padx=20, pady=(0, 20))
            
        # Получаем дополнительную информацию из БД
        try:
            from database import get_ppe_details, get_responsible_person
                
            details = get_ppe_details(school_id)
            responsible = get_responsible_person(school_id)
            
            # Получаем тип ГИА
            try:
                # Запрос типа ГИА из базы данных
                query = """
                    SELECT gia_type FROM dat_ppe
                    WHERE id = %s
                """
                from database import execute_query
                result = execute_query(query, (ppe_number,))
                
                if result and len(result) > 0:
                    gia_type = result[0][0]
                    gia_type_name = self._get_gia_type_name(gia_type)
                    
                    # Отображаем тип ГИА
                    gia_frame = ttk.LabelFrame(scrollable_frame, text="Тип ГИА")
                    gia_frame.pack(fill="x", expand=True, padx=20, pady=10)
                    
                    ttk.Label(
                        gia_frame, 
                        text=gia_type_name,
                        font=("Arial", 12, "bold")
                    ).pack(padx=10, pady=10)
                else:
                    # Если тип ГИА не найден
                    gia_frame = ttk.LabelFrame(scrollable_frame, text="Тип ГИА")
                    gia_frame.pack(fill="x", expand=True, padx=20, pady=10)
                    
                    ttk.Label(
                        gia_frame, 
                        text="Не указан",
                        foreground="gray"
                    ).pack(padx=10, pady=10)
            except Exception as e:
                # В случае ошибки при получении типа ГИА
                gia_frame = ttk.LabelFrame(scrollable_frame, text="Тип ГИА")
                gia_frame.pack(fill="x", expand=True, padx=20, pady=10)
                
                ttk.Label(
                    gia_frame, 
                    text=f"Ошибка при получении типа ГИА: {str(e)}",
                    foreground="red"
                ).pack(padx=10, pady=10)
                
            # Информация об организации
            org_frame = ttk.LabelFrame(scrollable_frame, text="Информация об организации")
            org_frame.pack(fill="x", expand=True, padx=20, pady=10)
                
            if details:
                # Проверяем, является ли details кортежем или словарем
                if isinstance(details, tuple):
                    fullname = details[0] if len(details) > 0 and details[0] else "Не указано"
                    address = details[1] if len(details) > 1 and details[1] else "Не указано"
                    inn = details[2] if len(details) > 2 and details[2] else "Не указано"
                    kpp = details[3] if len(details) > 3 and details[3] else "Не указано"
                    okpo = details[4] if len(details) > 4 and details[4] else "Не указано"
                    ogrn = details[5] if len(details) > 5 and details[5] else "Не указано"
                else:
                    # Если словарь, используем ключи
                    fullname = details.get("fullname", "Не указано")
                    address = details.get("address", "Не указано")
                    inn = details.get("INN", "Не указано")
                    kpp = details.get("KPP", "Не указано")
                    okpo = details.get("OKPO", "Не указано")
                    ogrn = details.get("OGRN", "Не указано")
                    
                info_grid = [
                    ("Полное наименование:", fullname),
                    ("Юр. адрес:", address),
                    ("ИНН:", inn),
                    ("КПП:", kpp),
                    ("ОКПО:", okpo),
                    ("ОГРН:", ogrn)
                ]
                    
                for i, (label, value) in enumerate(info_grid):
                    ttk.Label(org_frame, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=5)
                    ttk.Label(org_frame, text=value).grid(row=i, column=1, sticky="w", padx=10, pady=5)

            else:
                ttk.Label(org_frame, text="Информация отсутствует").pack(padx=10, pady=10)
                
            # Информация об ответственном лице
            resp_frame = ttk.LabelFrame(scrollable_frame, text="Ответственное лицо")
            resp_frame.pack(fill="x", expand=True, padx=20, pady=10)
                
            if responsible:
                position = responsible[0] if responsible[0] else "Не указано"
                surname = responsible[1] if responsible[1] else ""
                first_name = responsible[2] if responsible[2] else ""
                second_name = responsible[3] if responsible[3] else ""
                full_name = f"{surname} {first_name} {second_name}".strip()
                    
                ttk.Label(resp_frame, text="Должность:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
                ttk.Label(resp_frame, text=position).grid(row=0, column=1, sticky="w", padx=10, pady=5)
                    
                ttk.Label(resp_frame, text="ФИО:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
                ttk.Label(resp_frame, text=full_name if full_name else "Не указано").grid(row=1, column=1, sticky="w", padx=10, pady=5)
            else:
                ttk.Label(resp_frame, text="Информация отсутствует").pack(padx=10, pady=10)
                    
        except Exception as e:
            ttk.Label(
                scrollable_frame, 
                text=f"Ошибка при загрузке данных: {str(e)}", 
                foreground="red"
            ).pack(padx=20, pady=20)

    """Обновление вкладки с оборудованием."""
    def _update_equipment_tab(self, ppe_number):
        # Очищаем текущее содержимое
        for widget in self.equipment_frame.winfo_children():
            widget.destroy()
            
        # Создаем таблицу для отображения оборудования
        columns = ("Тип", "Марка", "Модель", "Год", "Кол-во")
        equipment_tree = ttk.Treeview(
            self.equipment_frame,
            columns=columns,
            show="headings"
        )
        
        # Настраиваем заголовки и колонки
        column_settings = [
            ("Тип", 150, "center"),
            ("Марка", 120, "center"),
            ("Модель", 150, "center"),
            ("Год", 100, "center"),
            ("Кол-во", 100, "center")
        ]
        
        for col, width, anchor in column_settings:
            equipment_tree.heading(col, text=col)
            equipment_tree.column(col, width=width, anchor=anchor)
        
        # Добавляем скроллбары
        y_scrollbar = ttk.Scrollbar(self.equipment_frame, orient="vertical", command=equipment_tree.yview)
        x_scrollbar = ttk.Scrollbar(self.equipment_frame, orient="horizontal", command=equipment_tree.xview)
        equipment_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Размещаем элементы
        equipment_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Загружаем данные оборудования
        try:
            from database import _fetch_equipment
            print(ppe_number)
            rows = _fetch_equipment(self, ppe_number)
            
            if rows:
                for row in rows:
                    equipment_tree.insert("", tk.END, values=row)
            else:
                # Если нет данных, показываем сообщение
                for widget in self.equipment_frame.winfo_children():
                    widget.destroy()
                    
                ttk.Label(
                    self.equipment_frame, 
                    text="Оборудование для данного ППЭ не найдено", 
                    style="Subheader.TLabel"
                ).pack(expand=True)
                
        except Exception as e:
            for widget in self.equipment_frame.winfo_children():
                widget.destroy()
                
            ttk.Label(
                self.equipment_frame, 
                text=f"Ошибка при загрузке данных оборудования: {str(e)}", 
                foreground="red"
            ).pack(expand=True)
        
    def _view_selected_contract(self, contracts_tree, ppe_number):
        """Просмотр выбранного контракта."""
        selected_items = contracts_tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите контракт для просмотра")
            return
            
        # Получаем данные выбранного контракта
        item = selected_items[0]
        contract_values = contracts_tree.item(item, "values")
        
        if len(contract_values) >= 2:
            contract_date, contract_number = contract_values[:2]
            supplier = contract_values[2] if len(contract_values) > 2 else "Не указан"
            
            # Спрашиваем пользователя, что он хочет сделать с выбранным контрактом
            action = messagebox.askyesno(
                "Действие с контрактом", 
                f"Контракт №{contract_number} от {contract_date}\n"
                f"Поставщик: {supplier}\n\n"
                "Хотите открыть предпросмотр договора для текущего ППЭ?"
            )
            
            if action:
                # Пользователь выбрал "Да" - вызываем функцию предпросмотра договора
                self._preview_contract(ppe_number)
        else:
            messagebox.showwarning("Предупреждение", "Не удалось получить данные контракта")

    logger = logging.getLogger('contracts')

    def _preview_contract(self, ppe_number):
        if not self.current_ppe:
            messagebox.showwarning("Предупреждение", "Выберите ППЭ для просмотра договора")
            return
        
        try:
             # Используем фиксированные значения для предпросмотра договора
            from datetime import datetime
            contract_details = {
                "number": "1",  # Фиксированный номер для предпросмотра
                "date": datetime.now().strftime("%d.%m.%Y")  # Текущая дата
            }

            # Создаем временный файл для договора
            from contracts import create_temp_contract_directory
            import os
            
            temp_dir = create_temp_contract_directory()
            temp_file = os.path.join(temp_dir, f"preview_contract_{self.current_ppe}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx")
            
            # Создаем окно загрузки
            loading_window = tk.Toplevel(self.root)
            loading_window.title("Генерация договора")
            loading_window.geometry("300x150")
            loading_window.transient(self.root)
            loading_window.grab_set()
            
            # Центрируем окно
            loading_window.update_idletasks()
            width = loading_window.winfo_width()
            height = loading_window.winfo_height()
            x = (loading_window.winfo_screenwidth() // 2) - (width // 2)
            y = (loading_window.winfo_screenheight() // 2) - (height // 2)
            loading_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Добавляем сообщение и прогресс-бар
            tk.Label(
                loading_window, 
                text=f"Генерация предпросмотра договора для ППЭ №{self.current_ppe}...",
                wraplength=280
            ).pack(pady=(20, 10))
            
            # Создаем прогресс-бар в определенном режиме (determinate)
            progress = ttk.Progressbar(loading_window, mode="determinate", maximum=100)
            progress.pack(fill=tk.X, padx=20, pady=10)

            # Добавляем метку для отображения оставшегося времени
            time_label = ttk.Label(loading_window, text="Осталось: 10 секунд")
            time_label.pack(pady=5)

            # Функция для обновления прогресс-бара
            def update_progress(remaining_time):
                if remaining_time <= 0:
                    # Если время вышло, но генерация еще не завершена,
                    # переключаемся на неопределенный режим
                    progress.configure(mode="indeterminate")
                    progress.start(10)
                    time_label.configure(text="Завершение...")
                    return
                
                # Обновляем значение прогресс-бара (от 0 до 100)
                progress_value = 100 - (remaining_time * 10)
                progress.configure(value=progress_value)
                
                # Обновляем текст с оставшимся временем
                time_label.configure(text=f"Осталось: {remaining_time} секунд")
                
                # Планируем следующее обновление через 1 секунду
                loading_window.after(1000, update_progress, remaining_time - 1)

            # Запускаем обновление прогресс-бара
            update_progress(10)

            # Обновляем окно, чтобы показать прогресс-бар
            loading_window.update()

            try:
                """Предпросмотр нескольких контрактов."""
                selected_items = self.contracts_tree.selection()
                
                if not selected_items:
                    messagebox.showwarning("Предупреждение", "Выберите хотя бы один контракт для предпросмотра")
                    return
                
                # Сбор информации о контрактах
                contracts_data = []
                for item in selected_items:
                    contract_values = self.contracts_tree.item(item, "values")
                    contract_date = contract_values[0]
                    contract_number = contract_values[1]
                    contract_name = contract_values[4]
                    contracts_data.append({
                        "num_contract": contract_number,
                        "date_contract": contract_date,
                        "name_contract": contract_name,
                    })

                # Логируем информацию о выбранных контрактах
                logger.info(f"Выбрано {len(contracts_data)} контрактов для предпросмотра.")
                for contract in contracts_data:
                    logger.info(f"Контракт: {contract['num_contract']}, Дата: {contract['date_contract']}, Наименование: {contract['name_contract']}")
                
                try:
                    from contracts import generate_contract
                    from utils import open_document

                    result = generate_contract(
                        contracts_data,  # Передаем все контракты
                        temp_file, 
                        contract_details["number"], 
                        contract_details["date"],
                        ppe_number
                    )
                    
                    # Закрываем окно загрузки
                    loading_window.destroy()

                    if result:
                        messagebox.showinfo(
                            "Предпросмотр договора", 
                            f"Договор для ППЭ №{self.current_ppe} успешно сгенерирован.\n\n"
                            f"Номер договора: {contract_details['number']}\n"
                            f"Дата договора: {contract_details['date']}\n\n"
                            "Сейчас документ будет открыт для предпросмотра."
                        )
                        
                        # Открываем файл для предпросмотра
                        open_document(temp_file)

                    else:
                        messagebox.showerror("Ошибка", "Не удалось сгенерировать договор для предпросмотра")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Произошла ошибка при генерации договора: {str(e)}")
                    import traceback
                    traceback.print_exc()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Произошла ошибка при подготовке предпросмотра договора: {str(e)}")
                import traceback
                traceback.print_exc() 

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при подготовке предпросмотра договора: {str(e)}")
            import traceback
            traceback.print_exc() 

    def _update_contracts_tab(self, ppe_number):
        """Обновление вкладки с контрактами напрямую по ppe_number."""
        # Очищаем текущее содержимое
        for widget in self.contracts_frame.winfo_children():
            widget.destroy()
            
        # Настроим заголовки и колонки только один раз при создании окна
        columns = ("Дата", "Номер", "Поставщик", "ИНН", "Описание")
        
        # Добавляем кнопки для работы с контрактами
        button_frame = ttk.Frame(self.contracts_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame, 
            text="Создать договор", 
            command=self._download_contract  # Используем функцию создания договора
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="Просмотреть договор", 
            command=lambda: self._view_selected_contract(self.contracts_tree, ppe_number)  # Правильный вызов функции
        ).pack(side=tk.LEFT, padx=5)

        # Используем уже созданное дерево contracts_tree
        self.contracts_tree = ttk.Treeview(self.contracts_frame, columns=columns, show="headings")
        column_settings = [
            ("Дата", 120, "center"),
            ("Номер", 150, "center"),
            ("Поставщик", 200, "w"),
            ("ИНН", 120, "center"),
            ("Описание", 400, "w")
        ]

        for col, width, anchor in column_settings:
            self.contracts_tree.heading(col, text=col)
            self.contracts_tree.column(col, width=width, anchor=anchor)

        # Добавляем скроллбары
        y_scrollbar = ttk.Scrollbar(self.contracts_frame, orient="vertical", command=self.contracts_tree.yview)
        x_scrollbar = ttk.Scrollbar(self.contracts_frame, orient="horizontal", command=self.contracts_tree.xview)
        self.contracts_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # Размещаем элементы
        self.contracts_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Загружаем данные контрактов напрямую по ppe_number
        try:
            query_contracts = """
                SELECT c.contract_date, c.contract_number, c.supplier, c.supplier_inn, c.contract_name 
                FROM dat_contract c
                JOIN equip_data ed ON ed.contract_id = c.id
                JOIN dat_ppe p ON p.id = ed.ppe_id
                WHERE p.id = %s
                GROUP BY c.id, c.contract_date, c.contract_number, c.supplier, c.supplier_inn, c.contract_name
            """
            from database import execute_query
            rows = execute_query(query_contracts, (ppe_number,))
            
            if rows:
                for row in rows:
                    formatted_row = list(row)
                    # Форматируем дату, если она есть
                    if row[0] and hasattr(row[0], 'strftime'):
                        formatted_row[0] = row[0].strftime('%d.%m.%Y')
                    self.contracts_tree.insert("", tk.END, values=formatted_row)
            else:
                ttk.Label(
                    button_frame, 
                    text=f"Контракты для ППЭ №{ppe_number} не найдены", 
                    foreground="#666666"
                ).pack(side=tk.RIGHT, padx=10)
                    
        except Exception as e:
            ttk.Label(
                button_frame, 
                text=f"Ошибка при загрузке данных контрактов: {str(e)}", 
                foreground="red"
            ).pack(side=tk.RIGHT, padx=10)

    def _update_plans_tab(self, ppe_number):
        """Обновление вкладки с планами помещений."""
        # Очищаем текущее содержимое
        for widget in self.plans_frame.winfo_children():
            widget.destroy()
            
        # Создаем фрейм для отображения PDF с вертикальной прокруткой
        pdf_canvas = tk.Canvas(self.plans_frame)
        pdf_scrollbar = ttk.Scrollbar(self.plans_frame, orient="vertical", command=pdf_canvas.yview)
        pdf_display_frame = ttk.Frame(pdf_canvas)
        
        # Настраиваем прокрутку
        pdf_display_frame.bind(
            "<Configure>",
            lambda e: pdf_canvas.configure(scrollregion=pdf_canvas.bbox("all"))
        )
        
        pdf_canvas.create_window((0, 0), window=pdf_display_frame, anchor="nw")
        pdf_canvas.configure(yscrollcommand=pdf_scrollbar.set)
        
        # Размещаем элементы
        pdf_canvas.pack(side="left", fill="both", expand=True)
        pdf_scrollbar.pack(side="right", fill="y")
        
        # Пытаемся загрузить PDF план
        try:
            from pdf_handler import show_ppe_pdf
            
            # Создаем необходимые атрибуты для совместимости с существующим кодом
            self.scrollable_pdf_frame = pdf_display_frame
            
            # Загружаем PDF
            result = show_ppe_pdf(self, str(ppe_number))
            
            if not result:
                ttk.Label(
                    pdf_display_frame, 
                    text="План помещения для данного ППЭ не найден", 
                    style="Subheader.TLabel"
                ).pack(expand=True)
                
            # Добавляем обработчик прокрутки колесиком мыши
            def _on_mousewheel(event):
                pdf_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            pdf_display_frame.bind("<MouseWheel>", _on_mousewheel)
            pdf_canvas.bind("<MouseWheel>", _on_mousewheel)
                
        except Exception as e:
            ttk.Label(
                pdf_display_frame, 
                text=f"Ошибка при загрузке плана помещения: {str(e)}", 
                foreground="red"
            ).pack(expand=True)
  
    def _download_contract(self):
        """Скачивание договора."""
        if not self.current_ppe:
            messagebox.showwarning("Предупреждение", "Выберите ППЭ для скачивания договора")
            return
            
        # Используем существующую логику из utils.py
        from utils import on_download_contract
        on_download_contract(self)
    
    def _show_help(self):
        """Показ справочной информации."""
        help_window = tk.Toplevel(self.root)
        help_window.title("Справка")
        help_window.geometry("600x400")
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Центрируем окно
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Создаем текстовое поле с информацией
        text = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(text, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Заполняем справочную информацию
        help_text = """
        # Справка по работе с системой управления ППЭ
        
        ## Основные функции
        
        ### Работа со списком ППЭ
        - Для просмотра информации о ППЭ выберите его в списке слева
        - Для поиска ППЭ введите номер или часть адреса в поле поиска
        - Для обновления списка нажмите кнопку "Обновить"
        
        ### Работа с договорами
        - Для создания нового договора выберите ППЭ и нажмите "Просмотр договора" в верхней панели
        - Для скачивания договора выберите ППЭ и нажмите "Скачать договор"
        - Для просмотра существующих договоров перейдите на вкладку "Контракты"
        
        ### Просмотр информации
        - Общая информация о ППЭ доступна на вкладке "Общая информация"
        - Список оборудования доступен на вкладке "Оборудование"
        - Список контрактов доступен на вкладке "Контракты"
        - Планы помещений доступны на вкладке "Планы помещений"
        
        ## Техническая поддержка
        
        При возникновении проблем обращайтесь в службу технической поддержки:
        - Телефон: +7 (XXX) XXX-XX-XX
        - Email: support@example.com
        """
        
        text.insert(tk.END, help_text)
        text.configure(state="disabled")  # Делаем текст только для чтения

    def add_ppe(self):
        """Добавление нового ППЭ."""
        # Создаем диалоговое окно для ввода данных нового ППЭ
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление нового ППЭ")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрируем окно
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Создаем и размещаем элементы формы
        tk.Label(dialog, text="Номер ППЭ:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ppe_number_entry = tk.Entry(dialog, font=("Arial", 12), width=20)
        ppe_number_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Адрес ППЭ:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ppe_address_entry = tk.Entry(dialog, font=("Arial", 12), width=40)
        ppe_address_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Кнопки "Сохранить" и "Отмена"
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def on_save():
            # Проверка ввода
            ppe_number = ppe_number_entry.get().strip()
            ppe_address = ppe_address_entry.get().strip()
            
            if not ppe_number:
                messagebox.showerror("Ошибка", "Введите номер ППЭ", parent=dialog)
                return
            
            if not ppe_address:
                messagebox.showerror("Ошибка", "Введите адрес ППЭ", parent=dialog)
                return
            
            try:
                # Здесь будет код для добавления ППЭ в базу данных
                # Пока это заглушка
                messagebox.showinfo("Информация", f"Функция добавления ППЭ в разработке.\n\nДанные для добавления:\nНомер: {ppe_number}\nАдрес: {ppe_address}", parent=dialog)
                dialog.destroy()
                
                # После реализации добавления в БД, нужно обновить список ППЭ
                # self._refresh_ppe_list()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при добавлении ППЭ: {str(e)}", parent=dialog)
        
        tk.Button(button_frame, text="Сохранить", command=on_save, width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Отмена", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=10)
        
        # Фокус на первое поле ввода
        ppe_number_entry.focus_set()

    def edit_ppe(self):
        """Редактирование ППЭ."""
        # Проверяем, выбран ли ППЭ
        if not self.current_ppe:
            messagebox.showwarning("Предупреждение", "Выберите ППЭ для редактирования")
            return
        
        # Получаем данные выбранного ППЭ
        selected_items = self.ppe_list.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        ppe_number, ppe_address = self.ppe_list.item(item, "values")
        
        # Создаем диалоговое окно для редактирования данных ППЭ
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редактирование ППЭ №{ppe_number}")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрируем окно
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Создаем и размещаем элементы формы
        tk.Label(dialog, text="Номер ППЭ:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ppe_number_entry = tk.Entry(dialog, font=("Arial", 12), width=20)
        ppe_number_entry.grid(row=0, column=1, padx=10, pady=10)
        ppe_number_entry.insert(0, ppe_number)
        ppe_number_entry.configure(state="readonly")  # Запрещаем изменение номера
        
        tk.Label(dialog, text="Адрес ППЭ:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ppe_address_entry = tk.Entry(dialog, font=("Arial", 12), width=40)
        ppe_address_entry.grid(row=1, column=1, padx=10, pady=10)
        ppe_address_entry.insert(0, ppe_address)
        
        # Кнопки "Сохранить" и "Отмена"
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def on_save():
            # Проверка ввода
            new_address = ppe_address_entry.get().strip()
            
            if not new_address:
                messagebox.showerror("Ошибка", "Введите адрес ППЭ", parent=dialog)
                return
            
            try:
                # Здесь будет код для обновления ППЭ в базе данных
                # Пока это заглушка
                messagebox.showinfo("Информация", f"Функция редактирования ППЭ в разработке.\n\nДанные для обновления:\nНомер: {ppe_number}\nНовый адрес: {new_address}", parent=dialog)
                dialog.destroy()
                
                # После реализации обновления в БД, нужно обновить список ППЭ
                # self._refresh_ppe_list()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при обновлении ППЭ: {str(e)}", parent=dialog)
        
        tk.Button(button_frame, text="Сохранить", command=on_save, width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Отмена", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=10)
        
        # Фокус на поле с адресом
        ppe_address_entry.focus_set()

    def delete_ppe(self):
        """Удаление ППЭ."""
        # Проверяем, выбран ли ППЭ
        if not self.current_ppe:
            messagebox.showwarning("Предупреждение", "Выберите ППЭ для удаления")
            return
        
        # Получаем данные выбранного ППЭ
        selected_items = self.ppe_list.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        ppe_number, ppe_address = self.ppe_list.item(item, "values")
        
        # Запрашиваем подтверждение
        confirm = messagebox.askyesno(
            "Подтверждение удаления", 
            f"Вы действительно хотите удалить ППЭ №{ppe_number}?\n\nАдрес: {ppe_address}\n\nЭто действие нельзя отменить.",
            icon="warning"
        )
        
        if confirm:
            try:
                # Здесь будет код для удаления ППЭ из базы данных
                # Пока это заглушка
                messagebox.showinfo("Информация", f"Функция удаления ППЭ в разработке.\n\nДанные для удаления:\nНомер: {ppe_number}")
                
                # После реализации удаления из БД, нужно обновить список ППЭ
                # self._refresh_ppe_list()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении ППЭ: {str(e)}")

if __name__ == "__main__":
    # Проверяем наличие необходимых модулей
    try:
        import ttkthemes
    except ImportError:
        print("Установка необходимых модулей...")
        import subprocess
        subprocess.call(["pip", "install", "ttkthemes", "pillow"])
        import ttkthemes
    
    root = tk.Tk()
    app = ModernPPEApp(root)
    
    # Устанавливаем иконку, если она существует
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    root.mainloop()