import pymongo
import pandas as pd
import mysql.connector
import utils
import time
import csv
from datetime import datetime
from textblob import TextBlob
from sklearn.preprocessing import OneHotEncoder

# Connexion à la base MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["MOOC"]
forum_collection = db["forum"]
user_collection = db["user"]

# Extraire les données de la collection "forum" de MongoDB
forum_data = forum_collection.find(batch_size=1000)
user_data = user_collection.find(batch_size=1000)

# Connexion à la base MySQL
mydb = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="root",
    database="g4"
)

start_time = time.time()  # Début du chronomètre

opening_dates = {}

def get_username(msg):
    if 'username' in msg and msg['username'] is not None:
        return msg['username']
    else:
        return "anonyme"

def get_title(msg):
    if 'title' in msg and msg['title'] is not None:
        return msg['title']
    else:
        return "Pas de titre"

def get_course_id(msg):
    if 'course_id' in msg and msg['course_id'] is not None:
        return msg['course_id']
    else:
        return "Pas d'id de cours"

# def get_date(msg):
#     dt = msg['created_at']
#     return dt[:10] + ' ' + dt[11:19]

def get_date(msg):
    dt_str = msg['created_at']
    try:
        dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    return dt

def add_course(course_id, opening_dates, msg):
    if course_id not in opening_dates:
        opening_dates[course_id] = get_date(msg)
        mycursor = mydb.cursor()
        sql = "INSERT INTO course (id, opening_date) VALUES (%s, %s) ON DUPLICATE KEY UPDATE id=id, opening_date=VALUES(opening_date);"
        val = (course_id, opening_dates[course_id])
        mycursor.execute(sql, val)
        mydb.commit()
        # print("Cours ajouté avec id: ", course_id, "et opening_date: ", opening_dates[course_id])

def add_thread(thread_id, title, course_id):
    mycursor = mydb.cursor()
    sql = "INSERT INTO thread (_id, title, course_id) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE _id=_id;"
    val = (thread_id, title, course_id)
    mycursor.execute(sql, val)
    mydb.commit()
    # print("Thread ajouté avec titre: ", title, "et course_id: ", course_id)

def add_user(msg):
    if not msg['anonymous']:
        mycursor = mydb.cursor()
        username = get_username(msg)
        user_id = msg.get('user_id')
        if user_id is None:
            return  # ou lever une exception, selon le comportement souhaité

        sql = "INSERT INTO users (username, user_id) VALUES (%s,%s) ON DUPLICATE KEY UPDATE username=VALUES(username), user_id=VALUES(user_id);"
        val = (username, user_id)
        mycursor.execute(sql, val)
        mydb.commit()
        print("Utilisateur ajouté avec username: ", username, "et user_id: ", user_id)
        
        
def fill_users_table(username, city, country, gender, year_of_birth, CSP, goals, level_of_education):
    mycursor = mydb.cursor()
    sql = "INSERT INTO users (username, city, country, gender, year_of_birth, CSP, goals, level_of_education) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE username=VALUES(username), city=VALUES(city), country=VALUES(country), gender=VALUES(gender), year_of_birth=VALUES(year_of_birth), CSP=VALUES(CSP), goals=VALUES(goals), level_of_education=VALUES(level_of_education);"
    val = (username, city, country, gender, year_of_birth, CSP, goals, level_of_education)
    mycursor.execute(sql, val)
    mydb.commit()


def add_message(msg, thread_id, username, parent_id, dt):
    mycursor = mydb.cursor()
    sql = """INSERT INTO messages 
            (id, created_at, type, depth, body, thread_id, username, parent_id,course_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE parent_id=VALUES(parent_id), depth=VALUES(depth), thread_id=VALUES(thread_id), course_id=VALUES(course_id);"""

    val = (msg['id'], dt, msg['type'], msg['depth'] if 'depth' in msg else None, msg['body'], thread_id, username, parent_id, msg['course_id'])

    mycursor.execute(sql, val)
    mydb.commit()

def add_result(username, course_id, grade, Certificate_Eligible, Certificate_Delivered, Certificate_Type):
    mycursor = mydb.cursor()

    mycursor.execute("SELECT id FROM course WHERE id = %s", (course_id,))
    result = mycursor.fetchone()
    if result is None:
        print(f"Course {course_id} does not exist in the course table")
        return

    sql = "INSERT INTO result (username, course_id, grade, Certificate_Eligible, Certificate_Delivered, Certificate_Type) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE username=VALUES(username), course_id=VALUES(course_id), grade=VALUES(grade), Certificate_Eligible=VALUES(Certificate_Eligible), Certificate_Delivered=VALUES(Certificate_Delivered), Certificate_Type=VALUES(Certificate_Type);"
    val = (username, course_id, grade, Certificate_Eligible, Certificate_Delivered, Certificate_Type)
    try:
        mycursor.execute(sql, val)
        mydb.commit()
    except mysql.connector.Error as err:
        print("Une erreur s'est produite: {}".format(err))
        print("Le nom d'utilisateur est : {}".format(username))

    # print("Résultat ajouté avec : ", username, "course_id: ", course_id, "grade: ", grade)


def traitement(msg=None, parent_id=None, thread_id=None, title=None, course_id=None,  opening_date=None, grade=None, username=None, city=None, country=None):
    '''
    Effectue un traitement sur l'obj passé (Message)
    :param msg: Message
    :param limit: int, limite de messages à traiter
    :return:
    '''
    
    if thread_id is None:
        return
    
    # Récupération des données
    username = get_username(msg)
    title = get_title(msg)
    course_id = get_course_id(msg)
    dt = get_date(msg)
    # print("Recurse ", msg['id'], msg['depth'] if 'depth' in msg else '-', parent_id, dt)

    # Insertion dans la table course- si elle n'existe pas déjà
    # add_course(course_id, opening_dates, msg)

    # Insertion des utilisateurs
    # add_user(msg)
    # fill_users_table()

    # Insertion des threads
    # add_thread(thread_id, title, course_id)

    # Insertion des messages
    add_message(msg, thread_id, username, parent_id, dt)

    # Insertion des résultats
    # add_result(username, course_id, grade, city, country)

    # Récursivement, parcourir les enfants du message
    if 'children' in msg:
        for child in msg['children']:
            traitement(child, msg['id'])

#Messages

# for msg in forum_data:
#     utils.recur_message(msg['content'], traitement, thread_id=msg['_id'])

#Résultats

# for course in user_data:
#     for key, value in course.items():
#         if isinstance(value, dict) and 'grade' in value:
#             grade = value['grade']
#             username = course['username']
#             course_id = key
#             Certificate_Eligible = value.get('Certificate Eligible')
#             Certificate_Delivered = value.get('Certificate Delivered')
#             Certificate_Type = value.get('Certificate Type')
#             # print(f"Grade for {username} {course_id}: {grade}")
#             add_result(username, course_id, grade,Certificate_Eligible, Certificate_Delivered, Certificate_Type)

#Utilisateurs

# for course in user_data:
#     for key, value in course.items():
#         if isinstance(value, dict):
#             username = course['username']
#             if username is not None:
#                 country = value.get('country')
#                 city = value.get('city')
#                 gender = value.get('gender')
#                 year_of_birth = value.get('year_of_birth')
#                 CSP = value.get('CSP')
#                 goals = value.get('goals')
#                 level_of_education = value.get('level_of_education')
#                 fill_users_table(username, city, country, gender, year_of_birth, CSP, goals, level_of_education)

def update_sentiment_analysis(mydb):
    df = pd.read_sql('SELECT * FROM messages;', con=mydb)

    def get_polarity_subjectivity(text):
        blob = TextBlob(text)
        return blob.sentiment.polarity, blob.sentiment.subjectivity

    df[['polarity', 'subjectivity']] = df['body'].apply(get_polarity_subjectivity).apply(pd.Series)

    cursor = mydb.cursor()
    for idx, row in df.iterrows():
        message_id = row['id']
        polarity = row['polarity']
        subjectivity = row['subjectivity']
        cursor.execute('UPDATE messages SET polarity=%s, subjectivity=%s WHERE id=%s', (polarity, subjectivity, message_id))

    mydb.commit()
    
update_sentiment_analysis(mydb)


def export_table_to_csv(table_name):
    # Récupération des données
    mycursor = mydb.cursor()
    mycursor.execute(f"SELECT * FROM {table_name}")
    rows = mycursor.fetchall()

    # Exportation des données en CSV
    with open(f'{table_name}.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([i[0] for i in mycursor.description])
        for row in rows:
            writer.writerow(row)

# export_table_to_csv('users')


# Jointure des tables
df = pd.read_sql(""" SELECT DISTINCT u.username, u.city, u.country, u.gender, u.year_of_birth, u.level_of_education, m.body, m.polarity, m.subjectivity,m.course_id, r.Certificate_Delivered
FROM users u
JOIN messages m ON u.username = m.username
JOIN result r ON u.username = r.username
WHERE u.city IS NOT NULL AND u.city <> ''
    AND u.country IS NOT NULL AND u.country <> ''
    AND u.gender IS NOT NULL AND u.gender <> ''
    AND u.year_of_birth IS NOT NULL
    AND u.level_of_education IS NOT NULL AND u.level_of_education <> ''
    AND m.body IS NOT NULL AND m.body <> ''
    AND m.polarity IS NOT NULL
    AND m.subjectivity IS NOT NULL
    AND r.Certificate_Delivered IS NOT NULL AND r.Certificate_Delivered <> '' ;""", con=mydb)

# print(df.head())

# df.to_csv('data.csv', index=False)

elapsed_time = time.time() - start_time  # Fin du chronomètre
print(f"Temps d'exécution : {elapsed_time:.2f} secondes")
