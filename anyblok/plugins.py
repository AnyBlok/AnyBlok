from nose.plugins import Plugin
from anyblok.config import Configuration
from anyblok.blok import BlokManager
from anyblok.registry import RegistryManager
from os.path import join, exists


class Arg2OptOptions:

    def __init__(self, options):
        self.options = options

    def _get_args(self):
        return False

    def _get_kwargs(self):
        keys = ['configfile', 'db_name', 'db_driver_name', 'db_user_name',
                'db_password', 'db_host', 'db_port']

        return [(x, getattr(self.options, x))
                for x in keys] + [('withoutautomigration', True)]

    def __getattr__(self, name, default=None):
        return getattr(self.options, name, default)


class AnyBlokPlugin(Plugin):
    name = 'anyblok-bloks'
    score = 100

    def __init__(self):
        super(AnyBlokPlugin, self).__init__()
        self.authoried_bloks_test_files = []
        self.bloks_path = []
        self.registryLoaded = False
        self.AnyBlokOptions = None

    def options(self, parser, env):
        super(AnyBlokPlugin, self).options(parser, env)
        parser.add_option("--anyblok-configfile", dest="configfile")
        parser.add_option('--anyblok-db-name', dest='db_name',
                          default=env.get('ANYBLOK_DATABASE_NAME'),
                          help="Name of the database")
        parser.add_option('--anyblok-db-driver-name', dest='db_driver_name',
                          default=env.get('ANYBLOK_DATABASE_DRIVER'),
                          help="the name of the database backend. This name "
                               "will correspond to a module in "
                               "sqlalchemy/databases or a third party plug-in")
        parser.add_option('--anyblok-db-user-name', dest='db_user_name',
                          default=env.get('ANYBLOK_DATABASE_USER'),
                          help="The user name")
        parser.add_option('--anyblok-db-password', dest='db_password',
                          default=env.get('ANYBLOK_DATABASE_PASSWORD'),
                          help="database password")
        parser.add_option('--anyblok-db-host', dest='db_host',
                          default=env.get('ANYBLOK_DATABASE_HOST'),
                          help="The name of the host")
        parser.add_option('--anyblok-db-port', dest='db_port',
                          default=env.get('ANYBLOK_DATABASE_PORT'),
                          help="The port number")

    def configure(self, options, conf):
        super(AnyBlokPlugin, self).configure(options, conf)
        if self.enabled:
            self.AnyBlokOptions = Arg2OptOptions(options)

    def load_registry(self):
        if self.enabled and self.registryLoaded is False:
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
                installed_bloks = registry.System.Blok.list_by_state(
                    "installed")
                selected_bloks = Configuration.get('selected_bloks')
                if not selected_bloks:
                    selected_bloks = installed_bloks

                unwanted_bloks = Configuration.get('unwanted_bloks')
                if unwanted_bloks is None:
                    unwanted_bloks = []

                self.bloks_path = [BlokManager.getPath(x)
                                   for x in BlokManager.ordered_bloks]

                self.authoried_bloks_test_files = [
                    path for blok in installed_bloks
                    if blok in selected_bloks and blok not in unwanted_bloks
                    for path in [join(BlokManager.getPath(blok), 'tests')]
                    if exists(path)]
                registry.close()  # free the registry to force create it again

    def file_from_blok(self, file):
        for blok_path in self.bloks_path:
            if file.startswith(blok_path):
                return True

        return False

    def file_from_authorized_bloks(self, file):
        for testFile in self.authoried_bloks_test_files:
            if file.startswith(testFile):
                return True

        return False

    def wantModule(self, module):
        self.load_registry()
        return True

    def wantFile(self, file, package=None):
        self.load_registry()
        if self.enabled:
            if file.endswith(".py"):
                if self.file_from_blok(file):
                    return self.file_from_authorized_bloks(file)

        return None
