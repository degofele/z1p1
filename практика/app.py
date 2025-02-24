from flask import Flask, request, redirect, url_for, render_template
import os
import pandas as pd
import csv

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE_FILE'] = 'database.csv'
app.config['SECRET_KEY'] = 'your_secret_key'

# Создаем папку uploads, если ее нет
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Создаем файл базы данных, если его нет (с заголовком)
if not os.path.exists(app.config['DATABASE_FILE']):
    with open(app.config['DATABASE_FILE'], 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['filename', 'data'])  # Заголовок файла

# Функция для сохранения данных из Excel в CSV-файл
def save_excel_to_csv(file_path, filename):
    print("Функция save_excel_to_csv вызвана")
    try:
        df = pd.read_excel(file_path)
        print("Файл Excel успешно прочитан")
        data_list = df.to_dict(orient='records')

        with open(app.config['DATABASE_FILE'], 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in data_list:
                import json
                data_string = json.dumps(row)
                writer.writerow([filename, data_string])
        print("Данные успешно записаны в CSV")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении в CSV: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'excel_file' not in request.files:
            print("Ошибка: Файл не выбран (отсутствует в request.files)")
            return render_template('index.html', error='Файл не выбран')

        file = request.files['excel_file']
        print(f"Имя файла: {file.filename}")
        if file.filename == '':
            print("Ошибка: Файл не выбран (имя файла пустое)")
            return render_template('index.html', error='Файл не выбран')

        if file:
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"Путь сохранения файла: {file_path}")
            file.save(file_path)
            print(f"Файл сохранен.")

            if save_excel_to_csv(file_path, filename):
                return redirect(url_for('view_data'))
            else:
                return render_template('index.html', error='Ошибка при сохранении в базу данных')

    return render_template('index.html')

@app.route('/view_data')
def view_data():
    data = []
    column_names = set()
    try:
        with open(app.config['DATABASE_FILE'], 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Пропускаем заголовок
            for row in reader:
                filename = row[0]
                data_string = row[1]
                import json
                try:
                    data_dict = json.loads(data_string)
                    data.append(data_dict)
                    column_names.update(data_dict.keys())
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Ошибка при декодировании JSON: {e}")
                    continue

    except FileNotFoundError:
        print("Файл базы данных не найден.")

    print(f"Данные прочитаны из CSV: {data}")
    column_names = list(column_names)
    print(f"Имена столбцов: {column_names}")
    return render_template('view_data.html', data=data, column_names=column_names)

if __name__ == '__main__':
    app.run(debug=True)