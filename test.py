# import tkinter as tk
# from tkinter import ttk, messagebox, filedialog, Toplevel
# import os
# import psycopg2
# import fitz  # PyMuPDF
# from PIL import Image, ImageTk  # Обработка изображений


#     # ===== Заготовки функций для взаимодействия с базой данных =====
#     def add_ppe(self):
#         messagebox.showinfo("Добавить ППЭ", "Функция добавления ППЭ в разработке.")

#     def edit_ppe(self):
#         messagebox.showinfo("Редактировать ППЭ", "Функция редактирования ППЭ в разработке.")

#     def delete_ppe(self):
#         messagebox.showinfo("Удалить ППЭ", "Функция удаления ППЭ в разработке.")
                
#     def toggle_ppe_list(self):
#         """
#         Обновлённая функция для корректного скрытия и показа списка ППЭ
#         """
#         if not hasattr(self, 'ppe_list_visible'):
#             self.ppe_list_visible = True  # Инициализация атрибута при первом вызове

#         if self.ppe_list_visible:
#             self.frame_ppe_list.pack_forget()
#             self.ppe_list_visible = False
#         else:
#             self.frame_ppe_list.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
#             self.ppe_list_visible = True

#         # Обновление текста пункта меню в зависимости от состояния
#         menubar = self.root.nametowidget(self.root.winfo_children()[0])  # Получаем меню
#         view_menu = menubar.winfo_children()[1]  # Предполагается, что второй элемент — это меню "Отображение"
#         view_menu.entryconfig(0, label="Показать список ППЭ" if not self.ppe_list_visible else "Скрыть список ППЭ")

#     def toggle_pdf_visibility(self):
#         if self.pdf_frame.winfo_ismapped():
#             self.pdf_frame.pack_forget()
#         else:
#             self.pdf_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)

#     def load_ppe_list(self):
#         cursor = self.connection.cursor()
#         cursor.execute("SELECT ppe_number, ppe_address FROM dat_ppe ORDER BY ppe_number")
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

#         ppe_number, ppe_address = self.ppe_list.item(selected_item, "values")

#         tk.Label(self.scrollable_frame, text=f"Детали ППЭ № {ppe_number}", font=("Arial", 16)).pack(anchor="w", pady=5)
#         tk.Label(self.scrollable_frame, text=f"Адрес: {ppe_address}", font=("Arial", 14)).pack(anchor="w", pady=5)

#         # Подключаем вкладки
#         equipment_tabs = ttk.Notebook(self.scrollable_frame)
#         equipment_tabs.pack(fill=tk.BOTH, expand=True)

#         # Вкладка "Оборудование"
#         equipment_tab = ttk.Frame(equipment_tabs)
#         equipment_tabs.add(equipment_tab, text="Оборудование")

#         equipment_tree = ttk.Treeview(equipment_tab, columns=("Тип", "Марка", "Модель", "Год", "Кол-во"), show="headings")
#         equipment_tree.heading("Тип", text="Тип оборудования")
#         equipment_tree.heading("Марка", text="Марка")
#         equipment_tree.heading("Модель", text="Модель")
#         equipment_tree.heading("Год", text="Год выпуска")
#         equipment_tree.heading("Кол-во", text="Количество")
#         equipment_tree.pack(fill=tk.BOTH, expand=True)

#         # Загружаем данные
#         self.load_equipment_data(equipment_tree, ppe_number)

#         self.show_ppe_pdf(str(ppe_number))
#         self.show_contracts(str(ppe_number))
    
#     def show_contracts(self, ppe_number):
#         """
#         Рефакторинг функции show_contracts для упрощения логики и повышения читаемости.
#         Теперь отображение данных вынесено в отдельные методы.
#         """
#         rows = self._fetch_contracts(ppe_number)

#         if not rows:
#             tk.Label(
#                 self.scrollable_frame,
#                 text="Контракты: не найдены",
#                 font=("Arial", 12, "italic")
#             ).pack(anchor="w", pady=5)
#             return

#         self._display_contracts(rows)

#     def _fetch_contracts(self, ppe_number):
#         """Получение данных контрактов из базы данных для указанного ППЭ."""
#         cursor = self.connection.cursor()
#         query = """
#             SELECT contract_date, contract_namber, supplier, supplier_inn, contract_name 
#             FROM dat_contract 
#             WHERE id IN (SELECT contract_id FROM equip_data WHERE ppe_id = %s)
#         """
#         cursor.execute(query, (ppe_number,))
#         rows = cursor.fetchall()
#         print(f"Контракты для ППЭ {ppe_number}: {rows}")
#         return rows

#     def _display_contracts(self, contracts):
#         """Отображение данных контрактов в виде таблицы во вкладке интерфейса."""
#         equipment_tabs = ttk.Notebook(self.scrollable_frame)
#         equipment_tabs.pack(fill=tk.BOTH, expand=True)

#         contract_tab = ttk.Frame(equipment_tabs)
#         equipment_tabs.add(contract_tab, text="Контракты")

#         contract_tree = ttk.Treeview(
#             contract_tab,
#             columns=("Дата", "Номер", "Поставщик", "ИНН", "Описание"),
#             show="headings"
#         )

#         # Настройка заголовков и ширины колонок
#         columns_settings = [
#             ("Дата", 120, "center"),
#             ("Номер", 150, "center"),
#             ("Поставщик", 200, "w"),
#             ("ИНН", 120, "center"),
#             ("Описание", 400, "w")
#         ]

#         for col, width, anchor in columns_settings:
#             contract_tree.heading(col, text=col)
#             contract_tree.column(col, width=width, anchor=anchor)

#         # Добавление данных в таблицу
#         for row in contracts:
#             contract_tree.insert("", tk.END, values=row)

#         contract_tree.pack(fill=tk.BOTH, expand=True)

#     def load_contract_data(self, ppe_number):
#         cursor = self.connection.cursor()
#         query = """
#             SELECT contract_date, contract_namber, supplier, supplier_inn, contract_name 
#             FROM dat_contract 
#             WHERE id IN (SELECT contract_id FROM equip_data WHERE ppe_id = %s)
#         """
#         cursor.execute(query, (ppe_number,))
#         return cursor.fetchall()

#     def load_equipment_data(self, tree, ppe_number):
#         cursor = self.connection.cursor()
#         query = """
#             SELECT de.equip_type, de.equip_mark, de.equip_mod, de.release_year, ed.amount
#             FROM equip_data ed
#             JOIN dat_equip de ON ed.equip_id = de.id::INTEGER
#             WHERE ed.ppe_id = %s;
#         """
#         cursor.execute(query, (ppe_number,))
#         rows = cursor.fetchall()
        
#         for row in rows:
#             tree.insert("", tk.END, values=row)


#     def on_close(self):
#         self.connection.close()
#         self.root.destroy()

# def main():
#     root = tk.Tk()
#     app = PPEApp(root)
#     root.protocol("WM_DELETE_WINDOW", app.on_close)
#     root.mainloop()

# if __name__ == "__main__":
#     main()