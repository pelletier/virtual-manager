import sys
from subprocess import call
from os import remove


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
