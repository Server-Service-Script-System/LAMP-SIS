#!/usr/bin/env python3

import os, shutil, subprocess, time, signal
from getpass import getpass
import mysql.connector

WAIT_TIME = 0

# ======================
# Helper classes
# ======================

# Recursive chmod
class chmod():
    @classmethod
    def chmod_rec(cls, path, mode):
        for dirpath, dirnames, filenames in os.walk(path):
            os.chmod(dirpath, mode)
            for filename in filenames:
                os.chmod(os.path.join(dirpath, filename), mode)

# Wrapper for APT calls
class apt():
    @classmethod
    def install(cls, package):
        subprocess.call('apt install {} -y'.format(package), shell=True)

    @classmethod
    def remove(cls, package):
        subprocess.call('apt remove {} -y'.format(package), shell=True)
        subprocess.call('apt purge {} -y'.format(package), shell=True)

    @classmethod
    def autoremove(cls):
        subprocess.call('apt autoremove -y', shell=True)

    @classmethod
    def update(cls):
        subprocess.call('apt update', shell=True)

    @classmethod
    def upgrade(cls):
        subprocess.call('apt upgrade -y', shell=True)

    @classmethod
    def add_source(cls, repo):
        cls.install('software-properties-common')
        subprocess.call('add-apt-repository {} -y'.format(repo), shell=True)

# Wrapper for UFW calls
class ufw():
    @classmethod
    def enable(cls):
        subprocess.call('ufw enable', shell=True)

    @classmethod
    def reset(cls):
        subprocess.call('ufw --force reset', shell=True)

    @classmethod
    def defaults(cls):
        subprocess.call('ufw default deny incoming', shell=True)
        subprocess.call('ufw default allow outgoing', shell=True)

    @classmethod
    def add(cls, port):
        subprocess.call('ufw allow {}'.format(port), shell=True)

# Wrapper for systemctl calls
class systemctl():
    @classmethod
    def enable(cls, service):
        subprocess.call('systemctl enable {}'.format(service), shell=True)

    @classmethod
    def start(cls, service):
        subprocess.call('systemctl start {}'.format(service), shell=True)

    @classmethod
    def stop(cls, service):
        subprocess.call('systemctl stop {}'.format(service), shell=True)

    @classmethod
    def restart(cls, service):
        subprocess.call('systemctl restart {}'.format(service), shell=True)

    @classmethod
    def reload(cls, service):
        subprocess.call('systemctl reload {}'.format(service), shell=True)

# ======================
# Script begins here
# ======================

# General system administration
apt.update()
apt.upgrade()
ufw.enable()
ufw.reset()

time.sleep(WAIT_TIME)

# Removes any pre-existing LAMP installation or LAMP components
apt.remove('apache2')
apt.remove('mysql-server')
apt.remove('php*')
apt.autoremove()

time.sleep(WAIT_TIME)

# Installs a full LAMP stack

# Adding php source
apt.add_source('ppa:ondrej/php')
apt.update()

time.sleep(WAIT_TIME)

# Installing apache2
apt.install('apache2 libapache2-mod-evasive libapache2-mod-security2')
ufw.add(80)
ufw.add(443)
systemctl.start('apache2')
systemctl.enable('apache2')

time.sleep(WAIT_TIME)

mod_evasive = [
    '# $TFCName Script Entry - Apache2 ModEvasive Configuration $LogTime\n',
    '<ifmodule mod_evasive20.c>',
    '\tDOSHashTableSize 3097\n',
    '\tDOSPageCount 2\n',
    '\tDOSSiteCount 50\n',
    '\tDOSPageInterval 1\n',
    '\tDOSSiteInterval 1\n',
    '\tDOSBlockingPeriod 10\n',
    '\tDOSLogDir /var/log/mod_evasive\n',
    '\tDOSEmailNotify $modEvaEmail\n',
    '\tDOSWhitelist 127.0.0.1\n',
    '</ifmodule>'
]
f = open('mod-evasive.conf', 'w+')
f.writelines(mod_evasive)
f.close()
shutil.copy('mod-evasive.conf', '/etc/apache2/mods-available/')
subprocess.call('a2enmod security2', shell=True)
subprocess.call('a2enmod evasive', shell=True)
systemctl.restart('apache2')

time.sleep(WAIT_TIME)

chmod.chmod_rec('/etc/apache2/conf/', 0o750)
os.chmod('/usr/sbin/apache2', 0o511)
os.chmod('/var/log/apache2', 0o750)
chmod.chmod_rec('/etc/apache2/conf-available/', 0o640)
chmod.chmod_rec('/etc/apache2/conf-enabled/', 0o640)
os.chmod('/etc/apache2/apache2.conf', 0o640)

time.sleep(WAIT_TIME)

for dirpath, dirnames, filenames in os.walk('/var/www/html/'):
    shutil.chown(dirpath, 'www-data', 'www-data')
    for filename in filenames:
        shutil.chown(os.path.join(dirpath, filename), 'www-data', 'www-data')
apache_lines = [
    '<VirtualHost *:80>\n',
    '\tServerName localhost\n',
    '\tServerAdmin webmaster@localhost\n',
    '\tDocumentRoot /var/www/html\n',
    '\tErrorLog ${APACHE_LOG_DIR}/error.log\n',
    '\tCustomLog ${APACHE_LOG_DIR}/access.log combined\n',
    '</VirtualHost>'
]
f = open('newserver.conf', 'w+')
f.writelines(apache_lines)
f.close()
shutil.copy('newserver.conf', '/etc/apache2/conf-available/')

time.sleep(WAIT_TIME)

subprocess.call('a2enconf newserver', shell=True)
subprocess.call('a2dissite 000-default', shell=True)
systemctl.reload('apache2')

time.sleep(WAIT_TIME)

# Installing MySQL server
apt.install('mysql-server')
systemctl.start('mysql')
systemctl.enable('mysql')


time.sleep(WAIT_TIME)

f = open('/var/lib/mysql/ubuntu.pid', 'r')
mysqlpid = int(f.readline().strip('\n'))
f.close()
os.kill(mysqlpid, signal.SIGKILL)
f = open('mysql_init', 'w+')
f.write('ALTER USER \'root\'@\'localhost\' IDENTIFIED BY \'{}\''.format(getpass('Enter new MySQL root password: ')))
f.close()
subprocess.call('mysqld --init-file={}\mysql_init &'.format(os.getcwd()))
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password=getpass('Enter MySQL root password: ')
)
db_cursor = db.cursor()
db_cursor.execute('DELETE FROM mysql.user WHERE User=\'\'')
db_cursor.execute('DELETE FROM mysql.user WHERE User=\'root\' AND Host NOT IN (\'localhost\', \'127.0.0.1\', \'::1\')')
db_cursor.execute('DROP DATABASE test')
db_cursor.execute('DELETE FROM mysql.db WHERE Db=\'test\' OR Db=\'test\\_%\'')
db_cursor.execute('FLUSH PRIVILEGES')
db.close()
systemctl.stop('mysql')
systemctl.start('mysql')

time.sleep(WAIT_TIME)

# Installing PHP 8.0
apt.install('php8.0 libapache2-mod-php8.0 php8.0-mysql php-common php8.0-cli php8.0-common php8.0-opcache php8.0-readline')
subprocess.call('a2enmod php8.0', shell=True)
systemctl.restart('apache2')

print('Done!')