import json
import os
from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
import sqlite3
from model import *
import pandas as pd

app = Flask(__name__)


# tasks = [
#     {'title': 'Task 1', 'date': '2022-01-01', 'description': 'Do something', 'id': 1},
#     {'title': 'Task 2', 'date': '2022-01-02', 'description': 'Do something else', 'id': 11}
#     # Другие задачи
# ]
# tasks *= 10
def get_q():
    conn = sqlite3.connect('Users.db')
    df = pd.read_sql_query("SELECT * FROM Queue", conn)

    # Преобразование DataFrame в массив словарей
    records = df.to_dict(orient='records')
    cur = conn.cursor()
    for i in records:
        cur.execute(('''SELECT name,surname FROM Auth WHERE id = '{}';''').format(i["account_id"]))
        skin=cur.fetchall()
        print(skin)
        i["name"]=skin[0][0]+" "+skin[0][1]
    # # Закрытие соединения с базой данных SQLite
    # cur.close()
    # conn.close()
    # print(records[0]["account_id"])

    return records


models = load_models("./models/", ECGNet)


@app.route('/', methods=['GET', 'POST'])
def task_list():
    tasks = get_q()
    return render_template('main.html', tasks=tasks, id=1)


@app.route('/registration', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        password = request.form.get('password')
        is_doctor = 1 if request.form.get('checkbox') == 'on' else 0
        conn = sqlite3.connect('Users.db')
        cur = conn.cursor()
        sql_insert = '''INSERT INTO Auth VALUES(NULL,'{}','{}','{}','{}','{}');'''.format(first_name, last_name, email,
                                                                                          password, is_doctor)
        cur.execute(sql_insert)
        cur.close()
        conn.commit()
        conn.close()
        # print(first_name, last_name, email, password, is_doctor)
        # print(first_name, last_name, email, password, is_doctor)
        # print(first_name)
        return redirect(url_for('login'))
    return render_template('reg.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = sqlite3.connect('Users.db')
        cur = conn.cursor()
        cur.execute(('''SELECT password,is_doctor,id FROM Auth
                                                               WHERE login = '{}';
                                                               ''').format(email))
        pas = cur.fetchall()
        cur.close()
        # print(pas[0][0], password)
        if pas[0][0] != password:
            return render_template('auth.html')
        elif (pas[0][1] == 1):
            # return render_template('/')
            return redirect(url_for("task_list"))
            # return render_template('main.html', tasks=tasks, id=1)
        else:
            return redirect(url_for(f"profile_id", id=pas[0][2]))

        conn.close()
    return render_template('auth.html')


@app.route('/<int:id>', methods=['GET', 'POST'])
def get_id(id):
    tasks = get_q()
    return render_template('main.html', tasks=tasks, id=id)


@app.route('/<int:id>/', methods=['GET', 'POST'])
def profile_id(id):
    if request.method == 'POST':
        file = request.files['file']
        data = np.load(file)

        pred = json.dumps(get_predictions(data, models))

        conn = sqlite3.connect('Users.db')
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO Queue VALUES(NULL,'{}','{}','{}');'''.format(id, pred, datetime.now().strftime("%d-%m-%Y")))
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        p = f"./static/profiles/{id}"
        if not os.path.exists(p):
            os.makedirs(p)
        p += f"/{new_id}"
        os.makedirs(p)
        p += f"/{new_id}.png"
        to_img(data, p)
        return redirect(url_for(f"profile_id", id=id))
    return render_template('Upload.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port="80")
