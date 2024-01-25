import mysql.connector
import utils

def get_default_user_device_id():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=utils.get_secret('DB_PASSWORD'),
        database="ic3unrafproject"
    )
    cur = conn.cursor()

    cur.execute("SELECT user_device_id FROM user_profile_api_userprofile")
    device_ids = [int(row[0]) for row in cur.fetchall()]

    device_ids = sorted(device_ids)
    next_id = 1
    for i in range(len(device_ids)):
        if device_ids[i] > next_id:
            break
        next_id += 1

    cur.close()
    conn.close()

    default_user_device_id = next_id
    return default_user_device_id

def get_default_schedule_id():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=utils.get_secret('DB_PASSWORD'),
        database="ic3unrafproject"
    )
    cur = conn.cursor()

    cur.execute("SELECT horario_id FROM user_profile_api_subjectschedule")
    horario_ids = [int(row[0]) for row in cur.fetchall()]

    horario_ids = sorted(horario_ids)
    next_id = 1
    for i in range(len(horario_ids)):
        if horario_ids[i] > next_id:
            break
        next_id += 1

    cur.close()
    conn.close()

    default_horario_id = next_id
    return default_horario_id