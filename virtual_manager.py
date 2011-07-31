"""
virtual-manager.py is a script which aims to manage Vagrant-powered virtual
machines. More precisely it gives them names and references them in the
/etc/hosts to make them easily accessible.

You obviously must have a working Python 2.x and Vagrant installation.

Windows support: ah ah.
"""
from os import path, makedirs
from config import config
import vms
import provisions
from cli import cli


# Executes the entry point of the CLI: interacts with the user.
if __name__ == '__main__':
    directory = path.expanduser(config.core.get('core', 'vms_path'))
    if not path.isdir(directory):
        makedirs(directory)
    
    cli.main()
