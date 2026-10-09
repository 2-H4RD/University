from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # В реальном приложении используйте более надежный ключ

# Путь к базе данных
DATABASE = 'cyber_books.db'


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Создание таблицы пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Создание таблицы книг
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT NOT NULL
        )
    ''')

    # Создание таблицы корзин
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')

    # Добавление книг в базу данных (если они еще не добавлены)
    books = [
        ("The Web Application Hacker's Handbook", "Dafydd Stuttard, Marcus Pinto",
         "Практическое руководство по тестированию безопасности веб-приложений", 3499.99, "book1.jpg"),
        ("The Tangled Web", "Michal Zalewski", "Глубокий анализ безопасности веб-приложений и браузеров", 3299.99,
         "book2.jpg"),
        ("Applied Cryptography", "Bruce Schneier", "Фундаментальный труд по криптографии и её применению", 3999.99,
         "book3.jpg"),
        ("Cryptography Engineering", "Niels Ferguson, Bruce Schneier, Tadayoshi Kohno",
         "Проектирование и реализация криптографических систем", 3699.99, "book4.jpg"),
        ("The Art of Software Security Assessment", "Mark Dowd, John McDonald, Justin Schuh",
         "Анализ безопасности программного обеспечения", 3799.99, "book5.jpg"),
        ("Hacking: The Art of Exploitation", "Jon Erickson", "Техники эксплуатации уязвимостей и разработки эксплойтов",
         3199.99, "book6.jpg"),
        ("The Hacker Playbook", "Peter Kim", "Практическое руководство по пентестингу", 2899.99, "book7.jpg"),
        ("Metasploit: The Penetration Tester's Guide", "David Kennedy, Jim O'Gorman, Devon Kearns, Mati Aharoni",
         "Полное руководство по фреймворку Metasploit", 3399.99, "book8.jpg"),
        ("Real-World Bug Hunting", "Peter Yaworski", "Поиск уязвимостей в реальных веб-приложениях", 2999.99,
         "book9.jpg"),
        ("The Basics of Hacking and Penetration Testing", "Patrick Engebretson",
         "Основы этичного хакинга и тестирования на проникновение", 2799.99, "book10.jpg"),
        ("Cybersecurity and Cyberwar: What Everyone Needs to Know", "P.W. Singer, Allan Friedman",
         "Объяснение киберугроз и войн для широкой аудитории", 2899.99, "book11.jpg"),
        ("The Cuckoo's Egg", "Clifford Stoll", "Классическая книга о расследовании кибератаки", 2699.99, "book12.jpg"),
        ("The Art of Deception", "Kevin Mitnick", "Книга о социальной инженерии от легендарного хакера", 2799.99,
         "book13.jpg"),
        ("Ghost in the Wires", "Kevin Mitnick", "Автобиография легендарного хакера", 2899.99, "book14.jpg"),
        ("The Code Book", "Simon Singh", "История криптографии от древности до квантовой эпохи", 3099.99, "book15.jpg"),
        ("Secrets and Lies", "Bruce Schneier", "Книга о безопасности в цифровом мире", 3199.99, "book16.jpg"),
        ("Digital Evidence and Computer Crime", "Eoghan Casey", "Руководство по цифровой криминалистике", 3499.99,
         "book17.jpg"),
        ("Incident Response", "Stuart McClure", "Стратегии реагирования на инциденты безопасности", 3299.99,
         "book18.jpg"),
        ("Network Security Hacks", "Andrew Lockhart", "Практические советы по защите сетей", 2999.99, "book19.jpg"),
        ("The Practice of Network Security Monitoring", "Michael Collins",
         "Мониторинг сетевой безопасности и анализ трафика", 3399.99, "book20.jpg")
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO books (title, author, description, price, image_url)
        VALUES (?, ?, ?, ?, ?)
    ''', books)

    conn.commit()
    conn.close()


def get_db_connection():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Главная страница с каталогом книг"""
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('index.html', books=books)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация пользователя"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # Проверка на пустые поля
        if not username or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('register.html')

        # Проверка длины пароля
        if len(password) < 6:
            flash('Пароль должен содержать не менее 6 символов', 'error')
            return render_template('register.html')

        # Хеширование пароля
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                         (username, password_hash))
            conn.commit()
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем уже существует', 'error')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Авторизация пользователя"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # Проверка на пустые поля
        if not username or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неправильное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/add_to_cart/<int:book_id>')
def add_to_cart(book_id):
    """Добавление книги в корзину"""
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему для добавления товаров в корзину', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Проверяем, есть ли уже такая книга в корзине
    existing_item = conn.execute(
        'SELECT id, quantity FROM cart WHERE user_id = ? AND book_id = ?',
        (session['user_id'], book_id)
    ).fetchone()

    if existing_item:
        # Увеличиваем количество, если книга уже в корзине
        new_quantity = existing_item['quantity'] + 1
        conn.execute(
            'UPDATE cart SET quantity = ? WHERE id = ?',
            (new_quantity, existing_item['id'])
        )
    else:
        # Добавляем новую запись в корзину
        conn.execute(
            'INSERT INTO cart (user_id, book_id, quantity) VALUES (?, ?, 1)',
            (session['user_id'], book_id)
        )

    conn.commit()
    conn.close()

    flash('Книга добавлена в корзину', 'success')
    return redirect(url_for('index'))


@app.route('/cart')
def cart():
    """Просмотр корзины"""
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему для просмотра корзины', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Получаем книги в корзине с информацией о них
    cart_items = conn.execute('''
        SELECT c.id as cart_id, c.quantity, b.id, b.title, b.author, b.description, b.price, b.image_url
        FROM cart c
        JOIN books b ON c.book_id = b.id
        WHERE c.user_id = ?
    ''', (session['user_id'],)).fetchall()

    # Получаем количество товаров в корзине
    cart_count = len(cart_items)

    conn.close()

    # Вычисляем общую стоимость
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)

    return render_template('cart.html', cart_items=cart_items, total_price=total_price, cart_count=cart_count)


@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    """Удаление книги из корзины"""
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему для изменения корзины', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM cart WHERE id = ? AND user_id = ?', (cart_id, session['user_id']))
    conn.commit()
    conn.close()

    flash('Книга удалена из корзины', 'info')
    return redirect(url_for('cart'))


# Маршрут для получения количества товаров в корзине (для использования в шаблоне)
@app.context_processor
def inject_cart_count():
    """Добавляет количество товаров в корзине в контекст шаблонов"""
    if 'user_id' in session:
        conn = get_db_connection()
        cart_count = \
        conn.execute('SELECT COUNT(*) as count FROM cart WHERE user_id = ?', (session['user_id'],)).fetchone()['count']
        conn.close()
        return dict(cart_count=cart_count)
    return dict(cart_count=0)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)