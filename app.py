from datetime import datetime, timedelta
import json
import gzip
import sqlite3
import requests
import os
import psycopg2
from psycopg2.extras import DictCursor
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask, Response, render_template, g, send_from_directory
import re  # Import modułu do wyrażeń regularnych

app = Flask(__name__, static_url_path='')

# HEROKU
DATABASE_URL = os.environ['DATABASE_URL']
SSL_MODE = 'require'

# LOCAL
# DATABASE_URL = "127.0.0.1"
# SSL_MODE = None

def get_gzipped_response(data):
    response = Response(gzip.compress(bytes(json.dumps(data), 'utf-8')))
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Vary'] = 'Accept-Encoding'
    response.headers['Accept-Charset'] = 'utf-8'
    response.headers['Content-Length'] = len(response.data)
    return response

def send_notification(title: str, body: str):
    x = requests.post("https://fcm.googleapis.com/fcm/send", json={
        "to": "/topics/all",
        "notification": {
            "title": title,
            "body": body
        }
    }, headers={
        'Content-type': 'application/json',
        "Authorization": "key=" + "AAAAh_ImxPE:APA91bFHHx7t3lAxnq4sxIUfxQP6v1FlO7EATk9QD_4hcTIj8BZ1fKL1mp3uXtgeiMrIJ_m2bDNcvP4Xm8BN_Vdt-lk42nCLMD7fhD4yGnQj5LGtC9TYxQoJjGi_gGjJnL2gxOfNeweY"
    })
    return x.content

def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = psycopg2.connect(DATABASE_URL, sslmode='require')
        create_tables(db)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_tables(db):
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS homework_update (
        id SERIAL PRIMARY KEY,
        date TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reference (
        id SERIAL PRIMARY KEY,
        name TEXT,
        link TEXT,
        homework TEXT,
        type TEXT,
        homework_update_id INTEGER,
        homework_tags TEXT 
    )""")
    db.commit()

def scrap_page():
    con = get_db()
    cur = con.cursor(cursor_factory=DictCursor)
    cur.execute("select * from homework_update order by id desc limit 1")
    last_update_id = cur.fetchone()
    update_id = last_update_id['id'] + 1 if last_update_id else 1

    cur.execute("select * from reference")
    myresult = cur.fetchall()
    if not myresult:
        addThisLinks1234()
        cur.execute("select * from reference")
        myresult = cur.fetchall()

    is_updated = False
    for subject in myresult:
        page_content = requests.get(subject['link']).text
        homework_content = BeautifulSoup(page_content, 'html.parser').find('div', class_="entry-content")
        homework_text = homework_content.text if homework_content else ""
        
        # Regex do wyszukiwania wzorca w treści zadania domowego, np. terminu
        match = re.search(r'\b(termin|deadline):\s*(\d{2}-\d{2}-\d{4})\b', homework_text)
        if match:
            deadline = match.group(2)
            print(f"Znaleziono termin dla przedmiotu '{subject['type']}': {deadline}")

        # Aktualizacja zadania domowego, jeśli treść się zmieniła
        if homework_text != subject['homework']:
            is_updated = True
            send_notification("Nowa praca domowa", f"Przedmiot '{subject['type']}' został zaktualizowany")
            cur.execute('update reference set homework=%s, homework_tags=%s, homework_update_id=%s where id=%s',
                        (homework_text, str(homework_content), update_id, subject['id']))

    if is_updated:
        cur.execute("insert into homework_update (date) values (%s)", ((datetime.now() + timedelta(hours=2)).strftime("%d.%m.%Y, %H:%M:%S"),))

    con.commit()
    con.close()

def insert_links_once():
    # Regex do walidacji URL
    url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*')
    subjects = [
        ('Zbigniew Switek', 'http://zsstaszow.pl/switek-zbigniew/', 'Język polski'),
        ('Krzysztof Janik', 'http://zsstaszow.pl/janik-krzysztof/', 'Język angielski'),
        # Dodaj pozostałe przedmioty...
    ]

    db = get_db()
    for subject in subjects:
        name, link, subject_type = subject
        if not re.match(url_pattern, link):
            print(f"Nieprawidłowy link: {link}")
            continue  # Pomija nieprawidłowy link

        cur = db.cursor()
        cur.execute("INSERT INTO reference (name, link, type) VALUES (%s, %s, %s)", (name, link, subject_type))
    db.commit()

@app.route('/api/all')
def get_all_teachers():
    cur = get_db().cursor()
    cur.execute("""
    SELECT r.id, r.name, r.link, r.homework, r.type, h.date, r.homework_tags
    FROM reference as r, homework_update as h
    WHERE r.homework_update_id = h.id
    """)
    return get_gzipped_response(cur.fetchall())

@app.route('/api/<id>')
def get_one_teacher(id: int):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM reference where id=%s", (id,))
    return get_gzipped_response(cur.fetchall())

@app.route('/static/<path:path>')
def send_asset(path):
    return send_from_directory('static', path)

@app.route('/single/<id>')
def single(id: int):
    return render_template('single.html', id=id)

@app.route('/scrap')
def scrap():
    scrap_page()
    return "Ok."

@app.route('/addThisLinks1234')
def addThisLinks1234():
    insert_links_once()
    return "Ok XD"

@app.route('/')
def main():
    cur = get_db().cursor()
    cur.execute("select date from homework_update order by id desc limit 1")
    date = cur.fetchone()
    if date is None:
        date = ['']

    return render_template('index.html', last_update=date[0])

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(scrap_page, 'interval', hours=1)
    scheduler.start()
    app.run(debug=True)
