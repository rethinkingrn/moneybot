#!/bin/bash
python3 -m venv .venv
source /sftp/sftpuser/files/moneybot/MONEYBOT/.venv/bin/activate
python3 /sftp/sftpuser/files/moneybot/MONEYBOT/main.py
