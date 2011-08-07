# Virtual-manager

Virtual-manager is a Python script which helps you to manage your
Vagrant-powered virtual machines. It allows you to automatically assign a name
and an host-only IP address to each of your VMs, so as you can easily access
them from your other programs.

You can watch the [demo video](http://vimeo.com/27112588) (revision 5 of
virtual-manager).

## Quick start

    hg clone https://bitbucket.org/pelletier/virtual-manager
    echo "source ~/path/to/virtual-manager/vm.sh" >> ~/.bash_profile

Source your `bash_profile` or start a new shell, then :

    vm

This will show the list of the commands.

## For non-BASH shells

I use a trick which only works on bash to guess the path of`virtual-manager`
directory. If you are using another shell (such as ZSH), you have to set the
`$VM_DIR` variable before sourcing the file:

    export VM_DIR="/path/to/virtual-manager/"
    source "$VM_DIR/vm.sh"

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

## Provisions

Revision 7 brought the support of provisions. It allows you to automatically
provision your VM when you load it. Here is an example shell session to deal
with provisioning using virtual-manager:

    $ vm
    Use one of the following commands:
        * add name base
        * add_provision name type source provisioner
        * bind_provision name vm_name
        * cd name
        * halt name
        * list
        * provisions_list
        * reload name
        * remove name
        * remove_provision name
        * ssh name
        * unbind_provision vm_name
        * up name

    $ vm add_provision baseprov link /Users/thomas/code/base-provision puppet
    New provision registered.

    $ vm provisions_list
    Available provisions:
        * baseprov

    $ vm add foo lucid32
    Password for sudo?
    [...]
    Virtual machine successfully created

    $ vm bind_provision baseprov foo
    Provision baseprov bound to foo.

    $ vm reload foo
    [default] Attempting graceful shutdown of linux.
    [...]

    $ vm unbind_provision foo
    Provision unbound from foo.

    $ vm remove foo
    [default] Forcing shutdown of VM...
    [...]
    Virtual machine removed.

    $ vm remove_provision baseprov
    Provision removed.

