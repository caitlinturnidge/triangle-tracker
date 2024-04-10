"""Script updates the database with availabilities, and notifies users if it becomes available, to be run every 5 minutes on a lambda function."""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from os import environ
from concurrent.futures import ThreadPoolExecutor

import logging

from psycopg2 import extensions, connect
from dotenv import load_dotenv
from requests import get
import boto3

BASE_URL = 'https://pfpleisure-pochub.org/LhWeb/en-gb/api'
PADEL = '3eee0ef5-1278-4197-91e7-5a14ef5b7234'
THE_TRIANGLE = '0ee06fb9-09cd-44a0-a316-a28f68dc1c7a'


def get_database_connection():
    """Gets a connection to the Planet Scale Database"""
    return connect(
        host=environ["DB_HOST"],
        user=environ["DB_USER"],
        password=environ["DB_PASSWORD"],
        port=environ["DB_PORT"],
        database=environ["DB_NAME"]
    )


def set_up_logger():
    """Set up a logger, to log pipeline progress to the console."""
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger('logger')


def get_availabilities(date: str):
    """Gets the availabilities at all the times for a given day."""
    url = f'{BASE_URL}/Sites/122/Timetables/{THE_TRIANGLE}/Events?locationGroupId={PADEL}&date={date}%2000:00:00.000&endDate=null'
    response = get(url, timeout=20)
    response = response.json()
    availabilities = []
    for hour in response:
        time = hour['StartTime'].split('T')[1]
        availabilities.append(
            {'Date': date,
             'Time': time[:5],
             'Available': hour['AvailablePlaces']})
    return availabilities


def add_availability(conn, event):
    """Updates/Adds an availability to the database, sends an email if its become available, and deletes old database items."""
    combined_time = f"{event['Date']} {event['Time']}"
    date = datetime.strptime(combined_time, '%Y/%m/%d %H:%M')
    cursor = conn.cursor()
    if event['Available'] == 1:
        query = f"""SELECT * FROM availabilities
                    WHERE time = '{date}';
                """
        cursor.execute(query)
        row = cursor.fetchone()
        if row and row[0] == 0:
            check_alerts_and_email(conn, row[1])
            print('Time has Changed!')
        cursor.fetchall()

    current_datetime = datetime.now()
    delete_query = f"DELETE FROM availabilities WHERE time < '{current_datetime}'"
    cursor.execute(delete_query)

    delete_query = f"DELETE FROM requests WHERE time < '{current_datetime}'"
    cursor.execute(delete_query)

    query = """INSERT INTO availabilities (available, time) 
               VALUES (%s, %s)
               ON DUPLICATE KEY UPDATE available = VALUES(available)"""
    values = (event['Available'], date)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()


def send_email(email, time):
    """Sends an email to the address given."""
    client = boto3.client("ses",
                          region_name="eu-west-2",
                          aws_access_key_id=environ["AWS_ACCESS_KEY_ID_"],
                          aws_secret_access_key=environ["AWS_SECRET_ACCESS_KEY_"])

    message = MIMEMultipart()
    message["Subject"] = "Padel Alert"

    body_text = f"The Padel court is now available at {time}."
    body_part = MIMEText(body_text)
    message.attach(body_part)

    client.send_raw_email(
        Source='caitlinturnidge@gmail.com',
        Destinations=[email],
        RawMessage={
            'Data': message.as_string()
        }
    )


def check_alerts_and_email(conn, time):
    """Checks if the time is in the requests table and send the email out to the people who chose this time."""
    cursor = conn.cursor()
    query = f"""SELECT * FROM requests
                WHERE time = '{time}';
            """
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in set(rows):
        send_email(row[0], time)
    cursor.close()


def process_day(date):
    logger = set_up_logger()
    availabilities = get_availabilities(date)
    connection = get_database_connection()
    logger.info(f"Processing data for {date}")
    for event in availabilities:
        add_availability(connection, event)


def handler(event=None, context=None):
    """Goes through each day in the next two weeks and adds/checks its status from the API and adds it to the database."""
    logger = set_up_logger()
    logger.info("Starting Pipeline")
    load_dotenv()
    with ThreadPoolExecutor() as executor:
        days = [(datetime.now() + timedelta(i)).strftime("%Y/%m/%d")
                for i in range(14)]
        executor.map(process_day, days)
    logger.info("Complete")


if __name__ == "__main__":
    handler()
