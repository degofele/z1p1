from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import sqlite3  # Или psycopg2 для PostgreSQL

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'database.db'  # SQLite
# app.config['DATABASE'] = 'postgresql://user:password@host:port/database' # PostgreSQL
app.config['SECRET_KEY'] = 'your_secret_key'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])  # SQLite
    # Или:
    # conn = psycopg2.connect(app.config['DATABASE']) # PostgreSQL
    conn.row_factory = sqlite3.Row # Или psycopg2.extras.DictCursor
    return conn


def init_db():
    conn = get_db_connection()
    with open('schema.sql') as f:  # Создайте файл schema.sql (см. ниже)
        conn.executescript(f.read())
    conn.close()


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['excel_file']
        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            process_excel(filepath)
            return redirect(url_for('view_data'))
    return render_template('upload.html')


def process_excel(filepath):
    try:
        df = pd.read_excel(filepath)
        column_names = list(df.columns)
        num_rows = len(df)

        conn = get_db_connection()
        cursor = conn.cursor()
        for column_name in column_names:
            cursor.execute("INSERT INTO columns (name) VALUES (?)", (column_name,))
        conn.commit()
        conn.close()

        print(f"Столбцы сохранены в БД: {column_names}")
        print(f"Количество строк: {num_rows}")
    except Exception as e:
        print(f"Ошибка обработки Excel: {e}")



@app.route('/view_data')
def view_data():
    conn = get_db_connection()
    columns = conn.execute("SELECT * FROM columns").fetchall()
    conn.close()
    return render_template('view_data.html', columns=columns)


if __name__ == '__main__':
    with app.app_context():  # Для создания БД вне запроса
        init_db()
    app.run(debug=True)