import psycopg2
from psycopg2.extras import execute_values

try:
    conn = psycopg2.connect(dbname='form_db2', user='postgres', password='!QAZ2wsx#EDC', host='localhost')
    with conn.cursor as curs:
        try:
            curs.execute('SELECT * FROM form_db2')
            full_db = curs.fetchall()
            try:
                conn2 = psycopg2.connect(dbname='form_db_archive', user='postgres', password='!QAZ2wsx#EDC', host='localhost')
                with conn2.cursor as curs2:
                    try:
                        execute_values(curs2, 'INSERT INTO form_db_archive VALUES %s ON CONFLICT (id) DO UPDATE', full_db)
                    except Exception as e:
                        print("Ошибка вставки данных", e)
            except Exception as e:
                print("Ошибка подключения к БД form_db_archive", e)
        except Exception as e:
            print("Ошибка копирования данных", e)
except Exception as e:
    print("Ошибка подключения к БД form_db2", e)