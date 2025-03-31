
# import sqlite3
# import tkinter as tk
# from tkinter import ttk, messagebox, simpledialog
# import os
# import fitz  # PyMuPDF
# from PIL import Image, ImageTk
# from ui import on_generate_contract_click_wrapper

# class PPEApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Список ППЭ")
#         self.root.geometry("1200x800")  # Увеличенное окно

#         self.connection = sqlite3.connect("ppe_database.db")
        
#         # Путь к папке с PDF-файлами
#         self.pdf_directory = "Z:\\_ГИА_2025\\Планы БТИ"
        
#         self.pdf_document = None
#         self.current_page = 0
        
#         # Создание интерфейса
#         self.create_ui()

#     def create_ui(self):
#         # Фрейм для списка ППЭ
#         frame_ppe_list = tk.Frame(self.root)
#         frame_ppe_list.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

#         tk.Label(frame_ppe_list, text="Список ППЭ", font=("Arial", 14)).pack()

#         # Список ППЭ
#         self.ppe_list = ttk.Treeview(frame_ppe_list, columns=("ppe_id", "address"), show="headings", height=35)
#         self.ppe_list.heading("ppe_id", text="№ ППЭ")
#         self.ppe_list.heading("address", text="Адрес ППЭ")
#         self.ppe_list.bind("<Double-1>", self.show_ppe_details)
#         self.ppe_list.pack(fill=tk.BOTH, expand=True)

#         # Устанавливаем ширину колонок
#         self.ppe_list.column("ppe_id", width=80, anchor="center")  # Уменьшаем ширину для ID
#         self.ppe_list.column("address", width=400, anchor="w")  # Увеличиваем ширину адреса

#         # Горизонтальный скроллбар
#         scroll_x = ttk.Scrollbar(frame_ppe_list, orient="horizontal", command=self.ppe_list.xview)
#         self.ppe_list.configure(xscrollcommand=scroll_x.set)

#         scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
#         self.ppe_list.pack(fill=tk.BOTH, expand=True)

#         self.ppe_list.bind("<Double-1>", self.show_ppe_details)

#         # Кнопка для редактирования ППЭ
#         self.edit_button = tk.Button(frame_ppe_list, text="Изменить сведения о ППЭ", command=self.edit_ppe)
#         self.edit_button.pack(pady=10)

#         # Загрузка данных
#         self.load_ppe_list()

#         # Фрейм для отображения деталей
#         self.details_frame = tk.Frame(self.root)
#         self.details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

#         # Добавляем холст и скроллбар для просмотра PDF
#         self.canvas = tk.Canvas(self.details_frame)
#         self.scrollbar = tk.Scrollbar(self.details_frame, orient="vertical", command=self.canvas.yview)
#         self.scrollable_frame = tk.Frame(self.canvas)

#         self.scrollable_frame.bind(
#             "<Configure>",
#             lambda e: self.canvas.configure(
#                 scrollregion=self.canvas.bbox("all")
#             )
#         )

#         self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
#         self.canvas.configure(yscrollcommand=self.scrollbar.set)

#         self.pdf_buttons_frame = tk.Frame(self.pdf_frame)
#         self.pdf_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

#         # Кнопка «Просмотр договора»
#         self.preview_button = tk.Button(
#             self.pdf_buttons_frame,
#             text="Просмотр договора",
#             command=self.on_preview_contract
#         )
#         self.preview_button.pack(side=tk.LEFT, padx=5)

#         # Кнопка «Скачать договор»
#         self.download_button = tk.Button(
#             self.pdf_buttons_frame,
#             text="Скачать договор",
#             command=self.on_download_contract
#         )
#         self.download_button.pack(side=tk.LEFT, padx=5)


#     def load_ppe_list(self):
#         cursor = self.connection.cursor()
#         cursor.execute("SELECT ppe_id, address, exam_type, auditory_count FROM PPE")
#         rows = cursor.fetchall()
#         for row in rows:
#             self.ppe_list.insert("", tk.END, values=row)

#     def show_ppe_details(self, event):
#         for widget in self.scrollable_frame.winfo_children():
#             widget.destroy()

#         selected_item = self.ppe_list.selection()
#         if not selected_item:
#             messagebox.showerror("Ошибка", "Выберите ППЭ для просмотра деталей.")
#             return

#         ppe_id, address, exam_type, auditory_count = self.ppe_list.item(selected_item, "values")

#         # Отображаем данные о ППЭ
#         tk.Label(self.scrollable_frame, text=f"Детали ППЭ № {ppe_id}", font=("Arial", 16)).pack(anchor="w", pady=5)
#         tk.Label(self.scrollable_frame, text=f"Адрес: {address}", font=("Arial", 14)).pack(anchor="w", pady=5)
#         tk.Label(self.scrollable_frame, text=f"ГИА: {exam_type}", font=("Arial", 14)).pack(anchor="w", pady=5)
#         tk.Label(self.scrollable_frame, text=f"Кол-во аудиторий: {auditory_count}", font=("Arial", 14)).pack(anchor="w", pady=5)

#         total_equipment = self.get_total_equipment(ppe_id)
#         tk.Label(self.scrollable_frame, text=f"Общее количество оборудования: {total_equipment}", font=("Arial", 14)).pack(anchor="w", pady=5)

#         self.show_ppe_pdf(str(ppe_id))

#     def on_preview_contract(self):
#         """
#         Метод-обработчик для кнопки «Просмотр договора».
#         Тут вы либо показываете всплывающее окно 
#         с информацией по выбранному ППЭ, 
#         либо генерируете временный docx и сообщаете пользователю.
#         """
#         # Пример:
#         selected_item = self.ppe_list.selection()
#         if not selected_item:
#             messagebox.showerror("Ошибка", "Сначала выберите ППЭ.")
#             return

#         ppe_id = self.ppe_list.item(selected_item, "values")[0]
#         # Далее: логика формирования контекста и «предпросмотра» 
#         # (либо просто messagebox, либо Toplevel)

#     def on_download_contract(self):
#         """
#         Метод-обработчик для кнопки «Скачать договор».
#         Тут вы вызываете вашу функцию generate_contract(ppe_number),
#         а потом ask_saveasfilename (при желании).
#         """
#         selected_item = self.ppe_list.selection()
#         if not selected_item:
#             messagebox.showerror("Ошибка", "Сначала выберите ППЭ.")
#             return

#         ppe_id = self.ppe_list.item(selected_item, "values")[0]
#         # Вызываем код генерации (или ask_saveasfilename для пути)
#         try:
#             from contracts import generate_contract
#             generate_contract(ppe_id)
#             messagebox.showinfo("Успех", f"Договор для ППЭ={ppe_id} сформирован!")
#         except Exception as e:
#             messagebox.showerror("Ошибка", str(e))


