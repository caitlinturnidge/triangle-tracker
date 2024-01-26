"""Database functions for the views.py file."""
from os import environ
import mysql.connector
import boto3

def get_database_connection():
    """Gets a connection to the Planet Scale Database"""
    return mysql.connector.connect(
        host=environ["DB_HOST"],
        user=environ["DB_USER"],
        password=environ["DB_PASSWORD"],
        database=environ["DB_NAME"],
        auth_plugin='mysql_native_password'
    )


def get_all_availabilities():
    """Gets a list of all the available times in the next two weeks."""
    conn = get_database_connection()
    cursor = conn.cursor()
    query = """SELECT * FROM availabilities
               WHERE available = 1;
              """
    cursor.execute(query)
    rows = cursor.fetchall()
    available_list = []
    for row in rows:
        formatted_datetime = row[1].strftime("%d-%m-%Y %H:%M")
        if formatted_datetime.split(' ')[1][:2] not in {'06', '07', '08'}:
            day_of_week = row[1].strftime("%A")
            available_list.append(day_of_week + ' ' + formatted_datetime)
    return available_list


def send_verification_email(email):
    """Sends a verification email from Amazon Web Services to add an identity."""
    client = boto3.client("ses",
                          region_name="eu-west-2",
                          aws_access_key_id=environ["AWS_ACCESS_KEY_ID_"],
                          aws_secret_access_key=environ["AWS_SECRET_ACCESS_KEY_"])

    try:
        client.verify_email_identity(EmailAddress=email)
    except Exception as e:
        print(f"Error: {e}")


def add_request(email, time):
    """Adds any given request to the database."""
    conn = get_database_connection()
    cursor = conn.cursor()
    query = """INSERT INTO requests (email, time) 
               VALUES (%s, %s)"""
    values = (email, time)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()


def verify_email(email):
    """Adds the email to AWS, this will send out a verification email."""
    conn = get_database_connection()
    cursor = conn.cursor()
    query = f"""SELECT * FROM requests
               WHERE email = '{email}';"""
    cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) == 0:
        send_verification_email(email)
    cursor.close()
