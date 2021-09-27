#!/usr/bin/env python3
import sys, subprocess

subprocess.call('apt install python3-venv python3-pip -y', shell=True)
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'mysql-connector-python'])
