from config import config
from subprocess import call
from os import path, makedirs
from cli import cli
from utils import nostdout, update_hostfile, normalize, render_template



def vm_path(name):
    """Grab the path to the VM with a given name."""
    vms_path = config.core.get("core", "vms_path")
    return path.join(path.expanduser(vms_path), name)



def register_vagrant_wrap(cli, command, command_name=None):
    """This method registers an action which will be passed to Vagrant and
    run against the given virtual machine.

    For instance:
        cli.register_vagrant_wrap('destroy')
    will lead to the action:
        destroy(name)
    which will perform the following:
        cd ~/.vm/name/ && vagrant destroy"""

    if command_name == None:
        command_name = command.split()[0].lower()
    @cli.register(command_name)
    def wrap(name):
        # All those commands must check if the VM exists before being run.
        with nostdout():
            vms = list_virtual_machines()

        if not name in vms:
            print "VM %s does not exist."
            list_virtual_machines()
            return -1

        vagrant_path = vm_path(name)

        call("cd %s && vagrant %s" % (vagrant_path, command), shell=True)
        return 0

# Register built-in Vagrant commands to the CLI.
for name in ["up", "halt", "ssh", "reload"]:
    register_vagrant_wrap(cli, name)


@cli.register("list")
def list_virtual_machines():
    """List the registered virtual machines."""
    sections = config.vms.sections()

    print "Available virtual machines:"
    for vm in sections:
        print "\t* %s" % vm
    return sections

@cli.register("remove")
def vm_remove(name):
    """Completely destroy the given virtual machine."""

    # Check that the machine exists.
    with nostdout():
        vms = list_virtual_machines()
    if not name in vms:
        print "VM %s does not exist." % name
        list_virtual_machines()
        return -1

    # Grab its IP.
    vagrant_path = vm_path(name)
    ip = config.vms.get(name, 'ip')

    # Destroy the VM using Vagrant.
    call("cd %s && vagrant destroy" % vagrant_path, shell=True)
    # Remove the Vagrant directory.
    call("rm -Rf %s" % vagrant_path, shell=True)
    # Remove the entry from the hosts file.
    update_hostfile(ip)
    # Remove the section in the configuration file.
    config.vms.remove_section(name)
    config.vms.write()
    
    print "Virtual machine removed."
    return 0

@cli.register()
def add(name, base):
    """Create and register a new virtual machine."""
    # Normalize the name of the VM
    name = normalize(name)

    # Check for doubles
    with nostdout():
        vms = list_virtual_machines()
    if name in vms:
        print "A virtual machine with the same name already exists."
        return -1

    # Grab the base IP from the config.
    base_ip = config.core.get("core", "base_ip")
    # The base IP should ends with a . (actually it should have the form of
    # xxx.xxx.xxx.).
    base_ip = base_ip if base_ip.endswith('.') else (base_ip + '.')

    # We will allocate an IP to the new virtual machine by incrementing the
    # byte of the IP address.
    # So let's start by gathering already used bytes.
    used_bytes = [int(config.vms.get(sec, 'ip').split('.')[-1])
                    for sec in config.vms.sections()]

    # Now create a list of every possible bytes. They must be between 0 and
    # 255, but:
    #   * They must not be already used.
    #   * They must not be 0 or 1, because they are reserved by Vagrant.
    byte_range = [i for i in range(2, 256) if not i in used_bytes]

    # Well, sorry, you'll need to patch virtual-manager to continue.
    if not byte_range:
        print "You've reach the maximum number of virtual machines. Well done."
        return -1

    # Form the complete IP address.
    ip = base_ip + str(byte_range[0])

    # Create a dict to substitute the template of the Vagrantfile.
    mapping = {
        'ip': ip,
        'base': base,
    }

    # Create the directory.
    vagrant_dir = vm_path(name)
    makedirs(path.join(vagrant_dir, 'link'))

    # Grab the default vagrant file.
    vagrant_template_path = config.core.get("core", "vagrant_template")
    vagrant_final_path = path.join(vagrant_dir, "Vagrantfile")
    render_template(vagrant_template_path, mapping, vagrant_final_path)

    # Create the configuration file.
    config.vms.add_section(name)
    config.vms.set(name, 'ip', ip)
    config.vms.write()
    
    # Update hosts file.
    newline = ["%s\t%s\n" % (ip, name)]
    update_hostfile(ip, newline)

    # Starts the virtual machine.
    call("/bin/bash -c 'cd %s && vagrant up'" % vagrant_dir, shell=True)

    print "Virtual machine successfully created"
    return 0

@cli.register()
def cd(name):
    """Change the current working directory to the VM path."""
    # Check that the machine exists.
    vmp = vm_path(name)
    return vmp
