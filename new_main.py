"""
модуль нового интерфейса для работы с ППЭ
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkthemes
from PIL import Image, ImageTk
import os
from database import connect_to_database, get_ppe_list, show_equipment, show_contracts
from contracts import generate_contract, get_contract_data_from_db
from utils import show_contract_input_dialog, open_document, show_save_dialog

class ModernPPEApp:
    def __init__(self, root):
        self.root = root
        self._initialize_window()
        self.connection = connect_to_database()
        self._initialize_variables()
        self._create_ui()
        
    def _initialize_window(self):
        """Настройка параметров главного окна приложения."""
        self.root.title("Система управления ППЭ")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 768)
        
        # Применяем современную тему
        self.style = ttkthemes.ThemedStyle(self.root)
        self.style.set_theme("arc")  # Можно выбрать: arc, equilux, breeze и др.
        
        # Настраиваем стили
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("Subheader.TLabel", font=("Segoe UI", 12))
        self.style.configure("Sidebar.TFrame", background="#f0f0f0")
        self.style.configure("Content.TFrame", background="#ffffff")
        
    def _initialize_variables(self):
        """Инициализация переменных."""
        self.pdf_directory = "Z:\\_ГИА_2025\\Планы БТИ\\Планы"
        self.pdf_document = None
        self.current_pdf_path = ""
        self.current_ppe = None
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_ppe_list)
        
    def _create_ui(self):
        """Создание современного пользовательского интерфейса."""
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
        self._create_toolbar()
        
    def _create_sidebar(self):
        """Создание боковой панели с поиском и списком ППЭ."""
        # Заголовок
        ttk.Label(self.sidebar, text="Пункты проведения экзаменов", 
                 style="Header.TLabel").pack(pady=10, padx=10)
        
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
        
    def _create_content_area(self):
        """Создание основной области контента с вкладками."""
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
        
        # Создаем заглушку для начального экрана
        self._create_welcome_screen()
        
    def _create_welcome_screen(self):
        """Создание приветственного экрана."""
        for frame in [self.info_frame, self.equipment_frame, self.contracts_frame, self.plans_frame]:
            ttk.Label(
                frame, 
                text="Выберите ППЭ из списка слева для просмотра информации",
                style="Subheader.TLabel"
            ).pack(expand=True)
        
    def _create_toolbar(self):
        """Создание панели инструментов."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Кнопки для работы с договорами
        ttk.Button(
            toolbar, 
            text="Просмотр договора", 
            command=self._preview_contract
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            toolbar, 
            text="Скачать договор", 
            command=self._download_contract
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Кнопка справки
        ttk.Button(
            toolbar, 
            text="Справка", 
            command=self._show_help
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
    def _load_ppe_list(self):
        """Загрузка списка ППЭ из базы."""
        # Очищаем текущий список
        for item in self.ppe_list.get_children():
            self.ppe_list.delete(item)
            
        try:
            rows = get_ppe_list()
            for row in rows:
                self.ppe_list.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список ППЭ: {str(e)}")
    
    def _filter_ppe_list(self, *args):
        """Фильтрация списка ППЭ по поисковому запросу."""
        search_term = self.search_var.get().lower()
        
        # Очищаем текущий список
        for item in self.ppe_list.get_children():
            self.ppe_list.delete(item)
            
        try:
            rows = get_ppe_list()
            for row in rows:
                # Проверяем, содержит ли номер или адрес ППЭ поисковый запрос
                if (search_term in str(row[0]).lower() or 
                    search_term in str(row[1]).lower()):
                    self.ppe_list.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при фильтрации списка: {str(e)}")
    
    def _on_ppe_select(self, event):
        """Обработчик выбора ППЭ из списка."""
        selected_items = self.ppe_list.selection()
        if not selected_items:
            return
            
        # Получаем данные выбранного ППЭ
        item = selected_items[0]
        ppe_number, ppe_address = self.ppe_list.item(item, "values")
        self.current_ppe = ppe_number
        
        # Обновляем информацию на вкладках
        self._update_info_tab(ppe_number, ppe_address)
        self._update_equipment_tab(ppe_number)
        self._update_contracts_tab(ppe_number)
        self._update_plans_tab(ppe_number)
    
    def _update_info_tab(self, ppe_number, ppe_address):
        """Обновление вкладки с общей информацией."""
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
            
            details = get_ppe_details(ppe_number)
            responsible = get_responsible_person(ppe_number)
            
            # Информация об организации
            org_frame = ttk.LabelFrame(scrollable_frame, text="Информация об организации")
            org_frame.pack(fill="x", expand=True, padx=20, pady=10)
            
            if details:
                info_grid = [
                    ("Полное наименование:", details[2] if details[2] else "Не указано"),
                    ("ИНН:", details[4] if details[4] else "Не указано"),
                    ("КПП:", details[5] if details[5] else "Не указано"),
                    ("ОКПО:", details[6] if details[6] else "Не указано"),
                    ("ОГРН:", details[7] if details[7] else "Не указано"),
                    ("Расчетный счет:", details[8] if details[8] else "Не указано"),
                    ("Банковский счет:", details[9] if details[9] else "Не указано"),
                    ("Лицевой счет:", details[10] if details[10] else "Не указано"),
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
    
    def _update_equipment_tab(self, ppe_number):
        """Обновление вкладки с оборудованием."""
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
    
    def _update_contracts_tab(self, ppe_number):
        """Обновление вкладки с контрактами."""
        # Очищаем текущее содержимое
        for widget in self.contracts_frame.winfo_children():
            widget.destroy()
            
        # Создаем таблицу для отображения контрактов
        columns = ("Дата", "Номер", "Поставщик", "ИНН", "Описание")
        contracts_tree = ttk.Treeview(
            self.contracts_frame,
            columns=columns,
            show="headings"
        )
        
        # Настраиваем заголовки и колонки
        column_settings = [
            ("Дата", 120, "center"),
            ("Номер", 150, "center"),
            ("Поставщик", 200, "w"),
            ("ИНН", 120, "center"),
            ("Описание", 400, "w")
        ]
        
        for col, width, anchor in column_settings:
            contracts_tree.heading(col, text=col)
            contracts_tree.column(col, width=width, anchor=anchor)
        
        # Добавляем скроллбары
        y_scrollbar = ttk.Scrollbar(self.contracts_frame, orient="vertical", command=contracts_tree.yview)
        x_scrollbar = ttk.Scrollbar(self.contracts_frame, orient="horizontal", command=contracts_tree.xview)
        contracts_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Размещаем элементы
        contracts_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Добавляем кнопки для работы с контрактами
        button_frame = ttk.Frame(self.contracts_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame, 
            text="Создать договор", 
            command=self._preview_contract
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Просмотреть договор", 
            command=lambda: self._view_selected_contract(contracts_tree)
        ).pack(side=tk.LEFT, padx=5)
        
        # Загружаем данные контрактов
        try:
            from database import _fetch_contracts
            rows = _fetch_contracts(self, ppe_number)
            
            if rows:
                for row in rows:
                    contracts_tree.insert("", tk.END, values=row)
            else:
                # Если нет данных, показываем сообщение в таблице
                ttk.Label(
                    button_frame, 
                    text="Контракты для данного ППЭ не найдены", 
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

    
    def _refresh_ppe_list(self):
        """Обновление списка ППЭ."""
        self._load_ppe_list()
        messagebox.showinfo("Информация", "Список ППЭ обновлен")
    
    def _preview_contract(self):
        """Предварительный просмотр договора."""
        if not self.current_ppe:
            messagebox.showwarning("Предупреждение", "Выберите ППЭ для просмотра договора")
            return
            
        # Используем существующую логику из utils.py
        try:
            # Получаем данные контракта из базы данных
            contract_data = get_contract_data_from_db(self.current_ppe)
            
            # Создаем диалоговое окно для ввода номера и даты договора
            contract_details = show_contract_input_dialog(self, self.current_ppe)
            if not contract_details:
                return  # Пользователь отменил операцию
            
            # Создаем временный файл для договора
            from contracts import create_temp_contract_directory
            import os
            from datetime import datetime
            
            temp_dir = create_temp_contract_directory()
            temp_file = os.path.join(temp_dir, f"contract_{self.current_ppe}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx")
            
            # Генерируем временный договор
            result = generate_contract(
                self.current_ppe, 
                temp_file, 
                contract_details["number"], 
                contract_details["date"]
            )
            
            if result:
                # Открываем файл в системном приложении
                open_document(temp_file)
                
                # Даем время на открытие документа перед показом диалога
                self.root.after(1000, lambda: show_save_dialog(self, self.current_ppe, temp_file))
            else:
                messagebox.showerror("Ошибка", "Не удалось сгенерировать договор")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
    
    def _download_contract(self):
        """Скачивание договора."""
        if not self.current_ppe:
            messagebox.showwarning("Предупреждение", "Выберите ППЭ для скачивания договора")
            return
            
        # Используем существующую логику из utils.py
        from utils import on_download_contract
        on_download_contract(self)
    
    def _view_selected_contract(self, contracts_tree):
        """Просмотр выбранного контракта."""
        selected_items = contracts_tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите контракт для просмотра")
            return
            
        # Получаем данные выбранного контракта
        item = selected_items[0]
        contract_date, contract_number = contracts_tree.item(item, "values")[:2]
        
        messagebox.showinfo("Информация о контракте", 
                           f"Контракт №{contract_number} от {contract_date}\n\n"
                           "Функция просмотра контракта в разработке.")
    
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