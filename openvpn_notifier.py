#!/usr/bin/env python3

"""Check users connected in last 5 min and send an email notification"""

import os
import json
import datetime
import smtplib
from dateutil.parser import parse


def get_users_list():
    """get list of online users"""
    data = os.popen("/usr/local/openvpn_as/scripts/sacli VPNstatus")
    data = data.read()
    data = json.loads(data)
    data_list = data['openvpn_0']
    return data_list


def users_5min(data):
    """get users who logged in last 5 min"""
    data_list = data
    users = ""
    now = parse(str(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")))
    for user in data_list['client_list']:
        connection_date = user[6]
        connection_date = datetime.datetime.strptime(connection_date, '%a %b %d %H:%M:%S %Y')
        difference = now - connection_date
        if str(difference) < "0:05:00":
            users = users + user[0] + " "
    return users


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


def main():
    """notify users connected in last 5 min"""
    users_list = get_users_list()
    recently_connect = users_5min(data=users_list)
    if not recently_connect:
        print("Nothing to do")
        return "Nothing to do"
    for user in users_list['client_list']:
        if str(user[0]) in str(recently_connect):
            username = user[0]
            connected_since = user[6]
            real_ip = user[1].split(":", 1)[0]
            print("Notifying {0}".format(username))
            subject = "Correct access to VPN"
            msg = "Dear {0},\n\nRecently happened a correct login into your VPN account using the next data:\n\n" \
                  "- Username: {0}\n- Real IP: {1}\n- Date: {2}\n\nIf you don't recognize this login, please, " \
                  "contact your sysadmin and change your password.".format(username, real_ip, connected_since)
            send_email(subject=subject, msg=msg, recipients=username)
    print("- Done")
    return "ok"


if __name__ == '__main__':
    main()
