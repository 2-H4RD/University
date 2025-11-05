from PIL import Image, ImageDraw, ImageFont
import os
import textwrap


def create_book_cover(title, author, filename):
    """Создание обложки книги"""
    # Создаем изображение 400x600 пикселей
    img = Image.new('RGB', (400, 600), color=(50, 50, 70))
    draw = ImageDraw.Draw(img)

    # Создаем градиентный фон
    for y in range(600):
        r = int(50 + (y / 600) * 30)
        g = int(50 + (y / 600) * 30)
        b = int(70 + (y / 600) * 60)
        draw.line([(0, y), (400, y)], fill=(r, g, b))

    # Добавляем кибер-элементы
    for i in range(100):
        import random
        x1 = random.randint(0, 400)
        y1 = random.randint(0, 600)
        x2 = x1 + random.randint(1, 3)
        y2 = y1 + random.randint(1, 3)
        color = (random.randint(0, 255), random.randint(100, 255), random.randint(0, 100))
        draw.ellipse([x1, y1, x2, y2], fill=color)

    # Добавляем основной текст
    try:
        # Используем встроенный шрифт, если не найден системный
        title_font = ImageFont.truetype("arial.ttf", 36) if os.path.exists("arial.ttf") else ImageFont.load_default()
        author_font = ImageFont.truetype("arial.ttf", 24) if os.path.exists("arial.ttf") else ImageFont.load_default()
    except:
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()

    # Обработка названия книги
    title_lines = textwrap.wrap(title, width=20)
    title_y = 150
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        draw.text(((400 - text_width) // 2, title_y), line, fill=(255, 255, 255), font=title_font)
        title_y += 45

    # Обработка автора
    bbox = draw.textbbox((0, 0), f"Автор: {author}", font=author_font)
    text_width = bbox[2] - bbox[0]
    draw.text(((400 - text_width) // 2, 300), f"Автор: {author}", fill=(200, 200, 200), font=author_font)

    # Добавляем кибер-стилизацию
    draw.rectangle([20, 20, 380, 580], outline=(100, 200, 255), width=3)
    draw.rectangle([25, 25, 375, 575], outline=(80, 180, 240), width=1)

    # Сохраняем изображение
    img.save(filename)


# Создаем папку для изображений, если она не существует
os.makedirs('static/images', exist_ok=True)

# Список известных книг по кибербезопасности
books_info = [
    ("The Web Application Hacker's Handbook", "Dafydd Stuttard, Marcus Pinto"),
    ("The Tangled Web", "Michal Zalewski"),
    ("Applied Cryptography", "Bruce Schneier"),
    ("Cryptography Engineering", "Niels Ferguson, Bruce Schneier, Tadayoshi Kohno"),
    ("The Art of Software Security Assessment", "Mark Dowd, John McDonald, Justin Schuh"),
    ("Hacking: The Art of Exploitation", "Jon Erickson"),
    ("The Hacker Playbook", "Peter Kim"),
    ("Metasploit: The Penetration Tester's Guide", "David Kennedy, Jim O'Gorman, Devon Kearns, Mati Aharoni"),
    ("Real-World Bug Hunting", "Peter Yaworski"),
    ("The Basics of Hacking and Penetration Testing", "Patrick Engebretson"),
    ("Cybersecurity and Cyberwar: What Everyone Needs to Know", "P.W. Singer, Allan Friedman"),
    ("The Cuckoo's Egg", "Clifford Stoll"),
    ("The Art of Deception", "Kevin Mitnick"),
    ("Ghost in the Wires", "Kevin Mitnick"),
    ("The Code Book", "Simon Singh"),
    ("Secrets and Lies", "Bruce Schneier"),
    ("Digital Evidence and Computer Crime", "Eoghan Casey"),
    ("Incident Response", "Stuart McClure"),
    ("Network Security Hacks", "Andrew Lockhart"),
    ("The Practice of Network Security Monitoring", "Michael Collins")
]

# Генерируем изображения для каждой книги
for i, (title, author) in enumerate(books_info, 1):
    filename = f"static/images/book{i}.jpg"
    create_book_cover(title, author, filename)
    print(f"Создано изображение: {filename}")

print("Все изображения обложек созданы!")