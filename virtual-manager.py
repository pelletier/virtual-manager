"""
virtual-manager.py is a script which aims to manage Vagrant-powered virtual
machines. More precisely it gives them names and references them in the
/etc/hosts to make them easily accessible.

You obviously must have a working Python 2.x and Vagrant installation.

Windows support: ah ah.
"""
import sys
import inspect
from subprocess import call
from string import Template
from os import path, mkdir, remove
from ConfigParser import SafeConfigParser


# With statements ************************************************* {{{
class nostdout:
    """Run the enclosed code without writing to the standard output.  This
    allows us to write actions as pure functions, add some print statements to
    interact with the user and still use them as any other pieces of code.  See
    the list_virtual_machines() for an example."""

    def __enter__(self, *args, **kwargs):
        self.orig = sys.stdout
        self.descr = open('/dev/null', 'w')
        sys.stdout = self.descr
    def __exit__(self, *args, **kwargs):
        sys.stdout = self.orig
        self.descr.close()

# }}}


# CLI ************************************************************* {{{
class CLI(object):
    """
    The CLI is the main part of the script. It handles the different commands
    and their possible arguments.

    The idea is simple: you write functions (ie commands) and register them to
    the CLI using the cli.register decorator. You just have to call cli.main()
    to interact with the user.
    """

    actions = {}

    def help(self, msg=None):
        """
        Display the list of the commands and their arguments. Eventually it
        will also display an error message.
        """

        # Print the message if given.
        if not msg == None:
            print str(msg) + "\n"

        # Display the list of commands, in the alphabetical order.
        print "Use one of the following commands:"
        for action in sorted(self.actions.keys()):
            info = self.actions[action]
            joined_oblig = ' '.join(info['required'])
            if len(info['additional']) > 0:
                add = ["<%s>" % x for x in info['additional']]
                joined_add = '[' + ' '.join(add) + ']'
            else:
                joined_add = ''
            print "\t* %s %s %s" % (action, joined_oblig, joined_add)

    def register(self, *args):
        """Add the action the CLI"""
        def decorate(f):
            if not len(args) == 1:
                full = f.__name__
            else:
                full = args[0]

            # Gather some informations about the arguments of the function, to
            # display them in help() and check for the min / max number of
            # arguments on call.
            spec = inspect.getargspec(f)
            fargs = spec.args if spec.args else []
            nbr_args = len(fargs)
            nbr_filled = len(spec.defaults) if spec.defaults else 0
            reqs = fargs[:nbr_args-nbr_filled+1]
            adds = fargs[nbr_args-nbr_filled+1:]

            info = {
                'function'  : f,
                'required'  : reqs,
                'additional': adds,
            }

            self.actions[full] = info
            return f
        return decorate

    def register_vagrant_wrap(self, command, command_name=None):
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
        @self.register(command_name)
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


    def main(self):
        """Entry point of the CLI"""

        # Make sure we have at least 2 arguments: the script name and
        # a command.
        if len(sys.argv) < 2:
            self.help()
            return 0

        # Gather the action and any parameter.
        action = sys.argv[1]
        params = sys.argv[2:]

        # If this is not a registered command, display an error and the
        # commands list.
        if not action in self.actions.keys():
            self.help("Wrong command")
            return -1

        # Grab information about the requested command.
        info = self.actions[action]
        func = info['function']
        min_args = len(info['required'])
        max_args = min_args + len(info['additional'])

        # Make sure the command receives the correct number of arguments.
        if len(params) > max_args or len(params) < min_args:
            msg = "Wrong number of arguments (want %s<x<%s, got %s)."\
                        % (min_args, max_args, len(params))
            self.help(msg)
            return -1

        # Run the command.
        # This could need some verification (the user input is given directly
        # to the function, without being sanitized, which is a bad practice). Yet
        # it's a hacker tool, yeah?
        return func(*params)

# }}}

# Create a CLI
cli = CLI()

# Create a default configuration using ConfigParser
CONFIG_PATH = path.expanduser("~/.vm.cfg")
config = SafeConfigParser({
    'vms_path'        : "~/.vm/",
    'base_ip'         : "33.33.33.",
    'vagrant_template': path.join(path.dirname(path.abspath(__file__)),\
                                  'Vagrantfile'),
    'ip'              : '0.0.0.0',
})
config.read(CONFIG_PATH)
# We need a core section.
if not 'core' in config.sections():
    config.add_section('core')


# Utils functions ************************************************* {{{
def write_config():
    """Write the currently running configuration to the config file."""
    config_file = open(CONFIG_PATH, 'w')
    config.write(config_file)
    config_file.close()

def vm_path(name):
    """Grab the path to the VM with a given name."""
    vms_path = config.get("core", "vms_path")
    return path.join(path.expanduser(vms_path), name)

def update_hostfile(ip, append=[]):
    """Remove the given IP from the /etc/hosts file, then append any given
    line.
    This requests the sudo password."""
    call("cp /etc/hosts /tmp/hosts", shell=True)
    hostsf = open('/tmp/hosts', 'r')
    hosts_content = hostsf.readlines()
    hostsf.close()
    remove('/tmp/hosts')

    lines = [line for line in hosts_content if not ip in line]
    for l in append:
        lines.append(str(l) + "\n")

    final_hosts = open('/tmp/hosts_final', 'w')
    final_hosts.writelines(lines)
    final_hosts.close()

    print "Password for sudo?"
    call('sudo cp /tmp/hosts_final /etc/hosts', shell=True)
    call('sudo touch /etc/hosts', shell=True)
    remove('/tmp/hosts_final')
# }}}


# CLI actions ***************************************************** {{{

# Register built-in Vagrant commands to the CLI.
for name in ["up", "halt", "ssh"]:
    cli.register_vagrant_wrap(name)


@cli.register("list")
def list_virtual_machines():
    """List the registered virtual machines."""
    sections = config.sections()
    if "core" in sections:
        sections.remove("core")

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
        print "VM %s does not exist."
        list_virtual_machines()
        return -1

    # Grab its IP.
    vagrant_path = vm_path(name)
    ip = config.get(name, 'ip')

    # Destroy the VM using Vagrant.
    call("cd %s && vagrant destroy" % vagrant_path, shell=True)
    # Remove the Vagrant directory.
    call("rm -Rf %s" % vagrant_path, shell=True)
    # Remove the entry from the hosts file.
    update_hostfile(ip)
    # Remove the section in the configuration file.
    config.remove_section(name)
    write_config()
    
    print "Virtual machine removed."
    return 0

@cli.register()
def add(name, base):
    """Create and register a new virtual machine."""
    # Normalize the name of the VM
    name = name.lower().replace(' ', "_")

    # Check for doubles
    with nostdout():
        vms = list_virtual_machines()
    if name in vms:
        print "A virtual machine with the same name already exists."
        return -1

    # Core is restricted, because we have a configuration section called
    # "core", and that each VM has a dedicated configuration section.
    if name == 'core':
        print "You cannot name a virtual machine \"core\""
        return -1

    # Grab the base IP from the config.
    base_ip = config.get("core", "base_ip")
    # The base IP should ends with a . (actually it should have the form of
    # xxx.xxx.xxx.).
    base_ip = base_ip if base_ip.endswith('.') else (base_ip + '.')

    # We will allocate an IP to the new virtual machine by incrementing the
    # byte of the IP address.
    # So let's start by gathering already used bytes.
    used_bytes = [int(config.get(sec, 'ip').split('.')[-1])
                    for sec in config.sections()]

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
    mkdir(vagrant_dir)

    # Grab the default vagrant file.
    vagrant_template_path = config.get("core", "vagrant_template")
    vagrant_template_descr = open(path.expanduser(vagrant_template_path), 'r')
    vagrant_template = Template(vagrant_template_descr.read())
    vagrant_template_descr.close()

    # Write the new one.
    vagrant_content = vagrant_template.substitute(mapping)
    vagrant_final_path = path.join(vagrant_dir, "Vagrantfile")
    vagrant_descr = open(vagrant_final_path, 'w')
    vagrant_descr.write(vagrant_content)
    vagrant_descr.close()

    # Create the configuration file.
    config.add_section(name)
    config.set(name, 'ip', ip)
    write_config()
    
    # Update hosts file.
    newline = ["%s\t%s\n" % (ip, name)]
    update_hostfile(ip, newline)

    # Starts the virtual machine.
    call("/bin/bash -c 'cd %s && vagrant up'" % vagrant_dir, shell=True)

    print "Virtual machine successfully created"
    return 0
# }}}


# Executes the entry point of the CLI: interacts with the user.
if __name__ == '__main__':
    directory = path.expanduser(config.get('core', 'vms_path'))
    if not path.isdir(directory):
        mkdir(directory)
    cli.main()
