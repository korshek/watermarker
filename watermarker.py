import fitz  # PyMuPDF для встраивания PDF-водяного знака
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import math
import os

# === НАСТРОЙКИ ДЛЯ ВОДЯНОГО ЗНАКА ===
watermark_text = "Confidential-"

# Параметры «волны»
amplitude = 10    # Амплитуда волны (вертикальное смещение)
frequency = 0.23 # Частота волны (0.1–0.2 обычно достаточно)
letter_spacing = 25  # Расстояние между символами при рисовании волны

opacity = 100    # Прозрачность для изображений (0-255)
font_size = 35   # Размер шрифта
angle = 30       # Общий наклон строки при наложении
density = 250    # «Шаг» между повторениями водяного знака в X,Y

# ========================================================
# === 1. Часть для PDF (ReportLab + PyMuPDF)
# ========================================================

def snake_text_on_canvas(c, text, start_x, start_y, 
                         amplitude, frequency,
                         letter_spacing):
    """
    Рисует одну «змейку» текста на canvas ReportLab:
      - Для каждого символа считаем dx, dy.
      - dx = i * letter_spacing
      - dy = amplitude * sin(frequency * dx)
    """
    for i, ch in enumerate(text):
        dx = i * letter_spacing
        dy = amplitude * math.sin(frequency * dx)
        c.drawString(start_x + dx, start_y + dy, ch)

def draw_snake_text_at(c, text, origin_x, origin_y, 
                       angle, amplitude, frequency, 
                       letter_spacing, font_size):
    """
    Рисует одну волну текста text на canvas с предварительной
    трансформацией (translate + rotate), чтобы задать угол и позицию.
    """
    c.saveState()
    c.translate(origin_x, origin_y)
    c.rotate(angle)
    snake_text_on_canvas(c, text, 0, 0, amplitude, frequency, letter_spacing)
    c.restoreState()

def create_watermark_pdf(text, page_width, page_height):
    """
    Создаёт PDF-страницу c повторяющимися «змейками» текста.
    Используем ReportLab для генерирования PDF в память (BytesIO),
    а потом PyMuPDF, чтобы «наложить» его на нужную страницу.
    """
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))

    # Настраиваем шрифт (Times-Roman есть по умолчанию в ReportLab)
    c.setFont("Times-Roman", font_size)
    # Устанавливаем цвет (RGBA через setFillColorRGB не напрямую, но alpha можно приблизительно)
    # Здесь используем "полупрозрачный" за счёт небольших ухищрений:
    c.setFillColorRGB(0.6, 0.6, 0.6, alpha=0.3)  # Светло-серый с прозрачностью

    # В цикле размещаем волну-надпись в разных точках
    # Пробегаемся по сетке в координатах страницы
    # (исходя из density в «штуках», а -5..5 - просто пример; подберите под размер страницы)
    for i in range(-5, 6):
        for j in range(-5, 6):
            x_pos = i * density
            y_pos = j * density
            draw_snake_text_at(
                c, text, 
                page_width/2 + x_pos,  # Смещаем центр
                page_height/2 + y_pos, 
                angle,
                amplitude,
                frequency,
                letter_spacing,
                font_size
            )
    
    c.save()
    packet.seek(0)

    # Превращаем байтовый PDF из packet в fitz.Document, чтобы вставить в основное PDF
    return fitz.open("pdf", packet.read())

def add_watermark_to_pdf(input_pdf, output_pdf):
    """
    Добавляет волновой водяной знак на все страницы PDF
    при помощи PyMuPDF: 
    1. Открываем исходный PDF (fitz.open).
    2. Для каждой страницы создаём PDF с водяным знаком.
    3. Накладываем ("show_pdf_page") поверх (overlay=True).
    """
    doc = fitz.open(input_pdf)
    for page_num in range(len(doc)):
        page = doc[page_num]
        width, height = page.rect.width, page.rect.height

        # Создаём PDF c «змейками»
        watermark_pdf = create_watermark_pdf(
            watermark_text, width, height
        )

        # Наносим поверх страницы
        page.show_pdf_page(page.rect, watermark_pdf, 0, overlay=True)

    doc.save(output_pdf)
    print(f"✅ Водяной знак добавлен в PDF: {output_pdf}")

# ========================================================
# === 2. Часть для изображений (PIL)
# ========================================================

def snake_text_on_image(draw, text, start_x, start_y, font, amplitude, frequency, letter_spacing, fill):
    """
    Рисует одну «змейку» текста PIL (ImageDraw):
    Для каждого символа считаем dx, dy, после чего draw.text(...)
    """
    x_offset = 0
    for ch in text:
        dx = x_offset
        dy = amplitude * math.sin(frequency * dx)
        draw.text((start_x + dx, start_y + dy), ch, font=font, fill=fill)
        # Сдвиг вправо
        x_offset += letter_spacing

def add_watermark_to_image(input_image, output_image):
    """
    Добавляет волновой водяной знак (PIL) на изображение.
    1. Открываем картинку как RGBA.
    2. Рисуем повторяющиеся «змейки» на новом прозрачном слое watermark_layer.
    3. Накладываем (Image.alpha_composite).
    4. Сохраняем результат.
    """
    img = Image.open(input_image).convert("RGBA")
    width, height = img.size

    # Создаём прозрачный слой
    watermark_layer = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw_ctx = ImageDraw.Draw(watermark_layer)

    # Загружаем шрифт
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    fill_color = (150, 150, 150, opacity)  # Светло-серый с заданной прозрачностью

    # В двойном цикле повторяем волну
    for i in range(-5, width // density + 5):
        for j in range(-5, height // density + 5):
            # координаты «базы» для каждой волны
            base_x = i * density + (density // 2)
            base_y = j * density + (density // 2)

            # Рисуем «змейку» — на самом деле не вращаем, а только волна по вертикали:
            snake_text_on_image(
                draw_ctx, watermark_text, base_x, base_y, font,
                amplitude, frequency, letter_spacing,
                fill=fill_color
            )

    # Накладываем слой поверх исходного изображения
    watermarked = Image.alpha_composite(img, watermark_layer)

    # Сохраняем в PNG (с цветностью RGB)
    watermarked.convert("RGB").save(output_image, "PNG")
    print(f"✅ Водяной знак добавлен в изображение: {output_image}")

# ========================================================
# === 3. Универсальная обёртка
# ========================================================

def add_watermark(input_file, output_file):
    """Определяет формат файла и добавляет волновой водяной знак."""
    ext = os.path.splitext(input_file)[1].lower()
    if ext == ".pdf":
        add_watermark_to_pdf(input_file, output_file)
    elif ext in [".png", ".jpg", ".jpeg"]:
        add_watermark_to_image(input_file, output_file)
    else:
        print("❌ Ошибка: неподдерживаемый формат файла")

# === Пример запуска ===
if __name__ == "__main__":
    input_file = "/path/to/input.pdf"  # Или "пример.png"
    output_file = "/path/to/output.pdf"  # Или "пример_watermarked.png"
    add_watermark(input_file, output_file)