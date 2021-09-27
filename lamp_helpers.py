import os

# ======================
# Helper classes
# ======================

class chmod():

    def chmod_rec(path, mode):
        for dirpath, dirnames, filenames in os.walk(path):
            os.chmod(dirpath, mode)
            for filename in filenames:
                os.chmod(os.path.join(dirpath, filename), mode)

# Wrapper for APT calls
class apt():
    def install(self, package):
        os.system('apt install {} -y'.format(package))

    def remove(self, package):
        os.system('apt remove {} -y'.format(package))
        os.system('apt purge {} -y'.format(package))

    def autoremove(self):
        os.system('apt autoremove -y')

    def update(self):
        os.system('apt update')

    def upgrade(self):
        os.system('apt upgrade')

    def add_source(self, repo):
        self.install('software-properties-common')
        os.system('add-apt-repository {}'.format(repo))

# Wrapper for UFW calls
class ufw():
    def enable(self):
        os.system('ufw enable')

    def reset(self):
        os.system('ufw --force reset')

    def defaults(self):
        os.system('ufw default deny incoming')
        os.system('ufw default allow outgoing')

    def add(self, port):
        os.system('ufw allow {}'.format(port))

# Wrapper for systemctl calls
class systemctl():
    def enable(self, service):
        os.system('systemctl enable {}'.format(service))

    def start(self, service):
        os.system('systemctl start {}'.format(service))

    def stop(self, service):
        os.system('systemctl stop {}'.format(service))

    def restart(self, service):
        os.system('systemctl restart {}'.format(service))

    def reload(self, service):
        os.system('systemctl reload {}'.format(service))