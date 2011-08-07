from os import path
from cli import cli
from subprocess import call
from config import config, NoOptionError
from vms import vm_path, list_virtual_machines
from utils import nostdout, normalize, render_template



class SourceTypeBase(object):

    def __init__(self, source_path, provisioner):
        self.source_path = source_path
        self.provisioner = provisioner

    def initialize(self, vm_path):
        # This method will be called when the user executes the `bind` action.
        raise NotImplementedError()

    def clean(self, vm_path):
        # This method will be called when the user executes the `unbind`
        # action.
        raise NotImplementedError()

    def update(self, vm_path):
        # This method will be called when the user executes the `update`
        # action.
        raise NotImplementedError()

    def destination_path(self, vm_path):
        return path.join(vm_path, self.provisioner)

class LinkType(SourceTypeBase):

    def initialize(self, vm_path):
        destination_path = self.destination_path(vm_path)
        call("ln -s %s %s" % (self.source_path, destination_path), shell=True)

    def clean(self, vm_path):
        destination_path = self.destination_path(vm_path)
        call("rm %s" % destination_path, shell=True)

    @staticmethod
    def update(self, vm_path):
        pass

class CopyType(SourceTypeBase):

    def clean(self, vm_path):
        destination_path = self.destination_path(vm_path)
        call("rm -R %s" % destination_path, shell=True)

    @staticmethod
    def update(self, vm_path):
        destination_path = self.destination_path(vm_path)
        call("cp -R %s %s" % (self.source_path, destination_path), shell=True)

setattr(CopyType, 'initialize', CopyType.update)


class Provision(object):

    props = ['name', 'type', 'source', 'provisioner']
    source_classes = {
        'link': LinkType,
        'copy': CopyType,
    }

    def __init__(self, **kwargs):
        for prop in self.props:
            value = kwargs.get(prop, None)
            setattr(self, prop, value)

        self.src = self.source_classes[self.type](self.source, self.provisioner)
            
    def save(self, config_instance):
        config_instance.add_section(self.name)
        for prop in self.props:
            if prop == 'name': continue
            config_instance.set(self.name, prop, getattr(self, prop))
        config_instance.write()

    @classmethod
    def load(cls, name, config_instance):
        values = [name] + [config_instance.get(name, x)
                            for x in cls.props
                            if not x == 'name']
        return cls(**dict(zip(cls.props, values)))

    @staticmethod
    def remove(name, config_instance):
        config_instance.remove_section(name)
        config_instance.write()


@cli.register()
def provisions_list():
    """List the registered provisions."""
    sections = config.provisions.sections()

    print "Available provisions:"
    for provision in sections:
        print "\t* %s" % provision
    return sections

@cli.register()
def add_provision(name, type, source, provisioner):
    name = normalize(name)
    with nostdout():
        provisions = provisions_list()
    if name in provisions:
        print "A provision with the same name already exists."
        return -1
    kwargs = {
        'name':        name,
        'type':        type,
        'source':      source,
        'provisioner': provisioner
    }
    new_prov = Provision(**kwargs)
    new_prov.save(config.provisions)

    print "New provision registered."

@cli.register()
def remove_provision(name):
    with nostdout():
        provisions = provisions_list()
    if not name in provisions:
        print "No such registered provision."
        return -1
    Provision.remove(name, config.provisions)
    print "Provision removed."
    return 0

@cli.register()
def bind_provision(name, vm_name):
    # Check that the machine exists.
    with nostdout():
        vms = list_virtual_machines()
    if not vm_name in vms:
        print "VM %s does not exist." % name
        list_virtual_machines()
        return -1

    with nostdout():
        provisions = provisions_list()
    if not name in provisions:
        print "No such registered provision."
        return -1

    provision = Provision.load(name, config.provisions)
    provisioners_path = config.core.get("core", "provisioners_templates")

    vmpath = vm_path(vm_name)

    template_path = path.join(provisioners_path, provision.provisioner)
    snippet = render_template(template_path)

    vagrant_path = path.join(vmpath, "Vagrantfile")
    vagrantfile = open(vagrant_path, 'r')
    vf_content = vagrantfile.read()
    vagrantfile.close()

    vf_new_content = vf_content.replace('# VM:PROVISIONER', snippet)

    vagrantfile = open(vagrant_path, 'w')
    vagrantfile.write(vf_new_content)
    vagrantfile.close()

    provision.src.initialize(vmpath)

    config.vms.set(vm_name, 'provision', name)
    config.vms.write()

    print "Provision %s bound to %s." % (name, vm_name)

@cli.register()
def unbind_provision(vm_name):
    with nostdout():
        vms = list_virtual_machines()
    if not vm_name in vms:
        print "VM %s does not exist." % vm_name
        list_virtual_machines()
        return -1

    try:
        provision = config.vms.get(vm_name, 'provision')
    except NoOptionError:
        print "No provision is bound to this VM."
        return -1

    provision = Provision.load(provision, config.provisions)
    config.vms.remove_option(vm_name, 'provision')
    config.vms.write()

    vmpath = vm_path(vm_name)

    provision.src.clean(vmpath)

    vf_buffer = ""

    vagrant_path = path.join(vmpath, "Vagrantfile")
    vagrantfile = open(vagrant_path, 'r')
    skip = False
    for line in vagrantfile.readlines():
        if "VM:PROVISIONER:START" in line:
            skip = True
            vf_buffer = vf_buffer + "# VM:PROVISIONER\n"
        elif "VM:PROVISIONER:STOP" in line:
            skip = False
        elif not skip:
            vf_buffer = vf_buffer + line + '\n'
    vagrantfile.close()

    vagrantfile = open(vagrant_path, 'w')
    vagrantfile.write(vf_buffer)
    vagrantfile.close()

    print "Provision unbound from %s." % vm_name
