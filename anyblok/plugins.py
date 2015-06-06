from nose.plugins import Plugin
from anyblok.config import Configuration
from anyblok.blok import BlokManager
from anyblok.registry import RegistryManager
from anyblok.common import format_bloks
from os.path import join, exists


@Configuration.add('nose-config')
def add_configuration_file(parser, configuration):
    """Add configuration file for anyblok"""
    parser.add_argument('--anyblok-config', dest='configfile', default='',
                        help="Relative path of the config file")
    configuration['configfile'] = None


class Arg2OptParser:

    def __init__(self, parser):
        self.parser = parser

    def add_argument_group(self, *args, **kwargs):
        return self

    def add_argument(self, *args, **kwargs):
        self.parser.add_option(*args, **kwargs)


class Arg2OptOptions:

    def __init__(self, options):
        self.options = options

    def _get_args(self):
        return False

    def _get_kwargs(self):
        return [(x, getattr(self.options, x))
                for x in Configuration.configuration.keys()]

    def __getattr__(self, name, default=None):
        return getattr(self.options, name, default)


class AnyBlokPlugin(Plugin):
    name = 'anyblok-bloks'
    score = 100

    def __init__(self):
        super(AnyBlokPlugin, self).__init__()
        self.testFiles = []
        self.registryLoaded = False
        self.AnyBlokOptions = None

    def options(self, parser, env):
        super(AnyBlokPlugin, self).options(parser, env)
        Configuration._load(Arg2OptParser(parser),
                            ('nose-config', 'database', 'unittest'),
                            ('bloks',))

    def configure(self, options, conf):
        super(AnyBlokPlugin, self).configure(options, conf)
        if self.enabled:
            self.AnyBlokOptions = Arg2OptOptions(options)

    def wantModule(self, module):
        if self.registryLoaded is False:
            # Load the registry here not in configuration,
            # because the configuration are not load in order of score
            self.registryLoaded = True
            BlokManager.load()
            Configuration.parse_options(self.AnyBlokOptions, ('bloks',))
            db_name = Configuration.get('db_name')
            if not db_name:
                raise Exception("No database defined to run Test")

            registry = RegistryManager.get(db_name)
            if registry:
                installed_bloks = registry.System.Blok.list_by_state("installed")
                selected_bloks = format_bloks(Configuration.get('selected_bloks'))
                if not selected_bloks:
                    selected_bloks = installed_bloks

                unwanted_bloks = format_bloks(Configuration.get('unwanted_bloks'))
                if unwanted_bloks is None:
                    unwanted_bloks = []

                self.testFiles = [
                    path for blok in installed_bloks
                    if blok in selected_bloks and blok not in unwanted_bloks
                    for path in [join(BlokManager.getPath(blok), 'tests')]
                    if exists(path)]

        return True

    def wantFile(self, file):
        print("want file")
        if self.enabled:
            if len([x for x in self.testFiles if x in file]):
                return True

        return False
