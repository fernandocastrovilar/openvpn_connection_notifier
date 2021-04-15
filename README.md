# OpenVPN Notifier
Script that notify when an user connect to openvpn server in last 1 min.

Before notify, checks in a sqlite if the IP of user has changed. If not, it won't notify. If the IP is new, its will send the email.

## Setup
Install requirements.txt
Edit config.json to setup your smtp account.

Launch the script with "-t initdb" option to initialize the DB.

Create a crontab to execute script every 1 min with "-t run" option.
