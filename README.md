# Virtual-manager

Virtual-manager is a Python script which helps you to manage your
Vagrant-powered virtual machines. It allows you to automatically assign a name
and an host-only IP address to each of your VMs, so as you can easily access
them from your other programs.

## Quick start

    hg clone https://bitbucket.org/pelletier/virtual-manager
    echo "source ~/path/to/virtual-manager/vm.sh" >> ~/.bash_profile

Source your `bash_profile` or start a new shell, then :

    vm

This will show the list of the commands.

## Requirements

    * A Linux or Unix box.
    * Python 2.6 or 2.7.
    * Vagrant and VirtualBox.

## Configuration

The configuration is stored in `~/.vm.cfg` in the INI format (as parsed by
[ConfigParser](http://docs.python.org/library/configparser.html)). Here is an
example configuration file:

    [core]
    vms_path = ~/.vm/
    base_ip = 33.33.33.
    vagrant_template = ~/virtual-manager/Vagrantfile

    [my_box]
    ip = 33.33.33.2

Each created box has its own section, with only this IP inside (for now). The
core section describes the behavior of the script. It's structure is very
straightforward.
