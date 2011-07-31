from os import path
from ConfigParser import SafeConfigParser


class ConfigItem(SafeConfigParser):
    
    def __init__(self, config_path, defaults={}):
        self.config_path = config_path
        SafeConfigParser.__init__(self, defaults)
        self.read(config_path)

    def write(self):
        self.remove_section("DEFAULT")
        file_descr = open(self.config_path, 'w')
        SafeConfigParser.write(self, file_descr)
        file_descr.close()


class Config(object):

    base_config_path = path.expanduser("~/.vm.d/")

    def register(self, name, config_file=None, defaults={},
                                               initial_sections=[]):
        if not getattr(self, name, None) == None:
            raise Exception("This config name is already registed.")
        if config_file == None:
            config_file = name + '.cfg'
        final_path = path.join(self.base_config_path, config_file)

        ci = ConfigItem(final_path, defaults)
        for section in initial_sections:
            ci.add_section(section)

        setattr(self, name, ci)



config = Config()

config.register('core', initial_sections=['core'], defaults={
    'vms_path'        : "~/.vm.d/machines",
    'base_ip'         : "33.33.33.",
    'vagrant_template': path.join(path.dirname(path.abspath(__file__)),\
                                  'Vagrantfile'),
})
config.register('provisions')
config.register('vms', defaults={
    'ip': '0.0.0.0',
})
