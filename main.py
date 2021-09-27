import os, shutil
from getpass import getpass
import mysql.connector
from lamp_helpers import *
 
# General system administration
apt.update()
apt.upgrade()
ufw.enable()
ufw.reset()

# Removes any pre-existing LAMP installation or LAMP components
apt.remove('apache2')
apt.remove('mysql-server')
apt.remove('php*')

# Installs a full LAMP stack

# Adding php source
apt.add_source('ppa:ondrej/php')
apt.update()

# Installing apache2
apt.install('apache2 libapache2-mod-evasive libapache2-modsecurity')
ufw.add(80)
ufw.add(443)
systemctl.start('apache2')
systemctl.enable('apache2')

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
os.system('a2enmod mod-security')
os.system('a2enmod mod-evasive')
systemctl.restart('apache2')

chmod.chmod_rec('/etc/apache2/conf/', 0o750)
os.chmod('/usr/sbin/apache2', 0o511)
os.chmod('/var/log/apache2', 0o750)
chmod.chmod_rec('/etc/apache2/conf-available/', 0o640)
chmod.chmod_rec('/etc/apache2/conf-enabled/', 0o640)
os.chmod('/etc/apache2/apache2.conf', 0o640)

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

os.system('a2enconf newserver')
os.system('a2dissite 00-default')
systemctl.reload('apache2')

# Installing MySQL server
apt.install('mysql-server')
systemctl.start('mysqld')
systemctl.enable('mysqld')

db = mysql.connector.connect(
    host='localhost',
    user='root',
    password=''
)
db_cursor = db.cursor()
db_cursor.execute('UPDATE mysql.user SET Password=PASSWORD(\'{}\') WHERE User=\'root\''.format(getpass('Enter new SQL root password: ')))
db_cursor.execute('DELETE FROM mysql.user WHERE User=\'\'')
db_cursor.execute('DELETE FROM mysql.user WHERE User=\'root\' AND Host NOT IN (\'localhost\', \'127.0.0.1\', \'::1\')')
db_cursor.execute('DROP DATABASE test')
db_cursor.execute('DELETE FROM mysql.db WHERE Db=\'test\' OR Db=\'test\\_%\'')
db_cursor.execute('FLUSH PRIVILEGES')

# Installing PHP 8.0
apt.install('php8.0 libapache2-mod-php8.0 php8.0-mysql php-common php8.0-cli php8.0-common php8.0-json php8.0-opcache php8.0-readline')
os.system('a2enmod php8.0')
systemctl.restart('apache2')

# Adds service to systemctl and enables it upon startup
service_lines = [
    '[Unit]\n',
    'Description=Service Management Script for LAMP stack\n',
    'After=network.target\n',
    '\n',
    '[Service]\n',
    'ExecStart=/usr/bin/python3 {}/maintenance.py\n'.format(os.getcwd()),
    '\n',
    '[Install]\n',
    'WantedBy=multi-user.target'
]

f = open('lampscript.service','w+')
f.writelines(service_lines)
f.close()

shutil.copy('lampscript.service', '/etc/systemd/system/')
os.chmod("/etc/systemd/system/lampscript.service", 0o644)

systemctl.enable('lampscript')
systemctl.start('lampscript')