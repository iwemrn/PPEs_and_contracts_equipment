import tkinter as tk
from tkinter import messagebox, filedialog, Toplevel
import os
import fitz
from PIL import Image, ImageTk
import shutil

def show_ppe_pdf(app, ppe_number):
    """Отображение PDF для выбранного ППЭ"""
    for widget in app.scrollable_pdf_frame.winfo_children():
        widget.destroy()

    # Ищем файл с точным соответствием номеру ППЭ
    for file in os.listdir(app.pdf_directory):
        if file.endswith(".pdf"):
            # Извлекаем номер ППЭ из имени файла (после дефиса и до .pdf)
            try:
                file_ppe_number = file.split(' - ')[1].split('.pdf')[0]
                # Сравниваем с искомым номером ППЭ
                if file_ppe_number == ppe_number:
                    file_path = os.path.join(app.pdf_directory, file)
                    app.current_pdf_path = file_path
                    load_pdf(app, file_path)
                    return
            except IndexError:
                # Пропускаем файлы с неправильным форматом имени
                continue

def load_pdf(app, file_path):
    """Загрузка PDF-файла и отображение страниц"""
    app.pdf_document = fitz.open(file_path)
    file_name = os.path.basename(file_path)

    _display_download_label(app, file_name, file_path)
    _display_pdf_pages(app)

def _display_download_label(app, file_name, file_path):
    label = tk.Label(app.scrollable_pdf_frame, text=file_name, font=("Arial", 14, "bold"), fg="blue", cursor="hand2")
    label.pack(anchor="w", pady=5)
    label.bind("<Button-1>", lambda e: download_file(file_path))

def _display_pdf_pages(app):
    for i in range(len(app.pdf_document)):
        page = app.pdf_document.load_page(i)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_resized = img.resize((500, 300))
        img_resized = ImageTk.PhotoImage(img_resized)

        pdf_label = tk.Label(app.scrollable_pdf_frame, image=img_resized, cursor="hand2")
        pdf_label.image = img_resized
        pdf_label.pack(anchor="w", pady=5)
        # Если нужно fullscreen:
        pdf_label.bind("<Button-1>", lambda e, original_img=img: show_fullscreen_image(app, original_img))

def download_file(file_path):
    """Скачивание выбранного PDF-файла по указанному пути."""
    destination = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    if destination:
        shutil.copy(file_path, destination)
        messagebox.showinfo("Скачивание", f"Файл успешно сохранён в: {destination}")

def show_fullscreen_image(app, img):
    """Отображение изображения во весь экран c возможностью зума"""
    fullscreen_window = tk.Toplevel(app.root)
    fullscreen_window.title("Просмотр изображения")
    fullscreen_window.attributes("-fullscreen", True)

    original_img = img
    zoom_factor = 1.0

    # Удаляем блок с кнопками plus_button / minus_button
    # Вместо этого будем слушать нажатия клавиш

    # Основная область под картинку
    image_frame = tk.Frame(fullscreen_window, bg="black")
    image_frame.pack(fill=tk.BOTH, expand=True)

    label = tk.Label(image_frame, bg="black")
    label.pack(fill="both", expand=True)

    def redraw_image():
        width = int(original_img.width * zoom_factor)
        height = int(original_img.height * zoom_factor)

        resized = original_img.resize((width, height))
        resized_photo = ImageTk.PhotoImage(resized)

        label.config(image=resized_photo)
        label.image = resized_photo

    def on_keypress(event):
        nonlocal zoom_factor
        # event.keysym может быть 'plus', 'minus', 'KP_Add', 'KP_Subtract' и т.д.
        # Нужно проверить несколько вариантов
        if event.keysym in ("plus", "KP_Add"):
            zoom_factor *= 1.2
            redraw_image()
        elif event.keysym in ("minus", "KP_Subtract"):
            zoom_factor /= 1.2
            redraw_image()
        elif event.keysym == "Escape":
            fullscreen_window.destroy()

    # Первичная отрисовка
    redraw_image()

    # Фокус и обработка клавиш
    fullscreen_window.focus_set()
    fullscreen_window.bind("<Key>", on_keypress)
    # Теперь нажатия + / - / Esc обрабатываются в on_keypress
