#!/usr/bin/env python3

"""Check users connected in last 1 min and send an email notification"""

import os
import json
import datetime
import smtplib
import sqlite3
import argparse
from dateutil.parser import parse
from ip2geotools.databases.noncommercial import DbIpCity


def get_users_list():
    """get list of online users"""
    data = os.popen("/usr/local/openvpn_as/scripts/sacli VPNstatus")
    data = data.read()
    data = json.loads(data)
    data_list = data['openvpn_0']
    return data_list


def users_1min(data):
    """get users who logged in last 1 min"""
    data_list = data
    users = ""
    now = parse(str(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")))
    for user in data_list['client_list']:
        connection_date = user[6]
        connection_date = datetime.datetime.strptime(connection_date, '%a %b %d %H:%M:%S %Y')
        difference = now - connection_date
        if str(difference) < "0:01:00":
            users = users + user[0] + " "
    return users


def init_db():
    """function for init db first time"""
    print("Creating DB and tables...")
    try:
        conn = sqlite3.connect("/tmp/openvpn_users.db")
        conn.execute('''CREATE TABLE IF NOT EXISTS USERS
                (IP               TEXT    NOT NULL,
                USERNAME          TEXT     NOT NULL);''')
        print("Created table successfully")
    except Exception as err:
        print(err)


def op_to_db(user, ip, op):
    """operation to db"""
    conn = sqlite3.connect('/tmp/openvpn_users.db')
    result = None
    if op == "write":
        try:
            conn.execute("INSERT INTO USERS (IP,USERNAME) VALUES ('{0}', '{1}')".format(ip, user))
            conn.commit()
            result = "ok"
        except Exception as err:
            print(err)
            result = "ko"
    elif op == "read":
        try:
            cursor = conn.execute("SELECT IP from USERS where USERNAME = '{0}'".format(user))
            result = cursor.fetchall()
        except Exception as err:
            print(err)
            result = "ko"
    elif op == "delete":
        try:
            conn.execute("DELETE from USERS where USERNAME = '{0}'".format(user))
            conn.commit()
            result = "ok"
        except Exception as err:
            print(err)
            result = "ko"
    return result


def db_user_check(user, ip):
    """check if user is already on bd, it checks if IP change to notify or not"""
    out = op_to_db(user=user, ip=ip, op="read")
    if out == "ko":
        os.popen("rm /tmp/openvpn_users.db")
        init_db()
        out = op_to_db(user=user, ip=ip, op="read")
    if not out:
        result = op_to_db(user=user, ip=ip, op="write")
    elif str(ip) in str(out):
        result = "ko"
    else:
        op_to_db(user=user, ip=ip, op="delete")
        op_to_db(user=user, ip=ip, op="write")
        result = "ok"
    return result


def send_email(subject, msg, recipients):
    """Send email via gmail"""
    with open("config.json") as config_file:
        data = json.load(config_file)
    notifications = data['notifications']

    smtp_server = notifications['smtp_server']
    smtp_user = notifications['username']
    smtp_pass = notifications['password']

    recipients = recipients + notifications['recipient']
    sender = smtp_user
    message = "Subject: {0}\n\n{1}".format(subject, msg)

    server = smtplib.SMTP(smtp_server, 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(smtp_user, smtp_pass)
    server.sendmail(sender, recipients, message)
    server.quit()
    return "ok"


def iplocation(ip):
    """Serch IP location"""
    data = DbIpCity.get(ip, api_key='free')
    location = data.region + "," + data.country
    return location


def notify():
    """notify users connected in last 1 min"""
    users_list = get_users_list()
    recently_connect = users_1min(data=users_list)
    if not recently_connect:
        print("Nothing to do")
        return "Nothing to do"
    for user in users_list['client_list']:
        if str(user[0]) in str(recently_connect):
            username = user[0]
            connected_since = user[6]
            real_ip = user[1].split(":", 1)[0]
            location = iplocation(ip=real_ip)
            out = db_user_check(user=username, ip=real_ip)
            if out == "ko":
                continue
            print("Notifying {0}".format(username))
            subject = "Correct access to VPN"
            msg = "Dear {0},\n\nRecently happened a correct login into your VPN account using the next data:\n\n" \
                  "- Username: {0}\n- Real IP: {1}\n- Location: {2}\n- Date: {3}\n\nIf you don't recognize this login, please, " \
                  "contact your sysadmin and change your password.".format(username, real_ip, location, connected_since)
            send_email(subject=subject, msg=msg, recipients=username)
    print("- Done")
    return "ok"


def main(arguments):
    if arguments.task == "run":
        notify()
    elif arguments.task == "initdb":
        init_db()
    else:
        print("Invalid option")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Task")
    parser.add_argument("-t", "--task",
                        required=False,
                        dest="task",
                        action="store",
                        help="run/initdb")
    args = parser.parse_args()
    main(arguments=args)
