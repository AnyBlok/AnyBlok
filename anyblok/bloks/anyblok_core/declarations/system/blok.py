from anyblok.blok import BlokManager
from anyblok import Declarations
from logging import getLogger
from os.path import join, isfile

logger = getLogger(__name__)
target_registry = Declarations.target_registry
System = Declarations.Model.System
String = Declarations.Column.String
Integer = Declarations.Column.Integer
Selection = Declarations.Column.Selection
Function = Declarations.Field.Function


@target_registry(System)
class Blok:

    STATES = {
        'uninstalled': 'Uninstalled',
        'installed': 'Installed',
        'toinstall': 'To install',
        'toupdate': 'To update',
        'touninstall': 'To uninstall',
        'undefined': 'Undefined',
    }

    name = String(primary_key=True, nullable=False)
    state = Selection(selections=STATES, default='uninstalled', nullable=False)
    order = Integer(default=-1, nullable=False)
    short_description = Function(fget='get_short_description')
    long_description = Function(fget='get_long_description')
    version = String(nullable=False)
    installed_version = String()

    def get_short_description(self):
        blok = BlokManager.get(self.name)
        if hasattr(blok, '__doc__'):
            return blok.__doc__

        return ''

    def get_long_description(self):
        blok = BlokManager.get(self.name)
        path = BlokManager.getPath(self.name)
        readme = 'README.rst'
        if hasattr(blok, 'readme'):
            readme = blok.readme

        file_path = join(path, readme)
        description = ''
        if isfile(file_path):
            with open(file_path, 'r') as fp:
                description = fp.read()

        return description

    def __repr__(self):
        return "%s (%s)" % (self.name, self.state)

    @classmethod
    def list_by_state(cls, *states):
        if not states:
            return None

        res = {state: [] for state in states}
        bloks = cls.query().filter(cls.state.in_(states)).order_by(cls.order)
        for blok in bloks.all():
            res[blok.state].append(blok.name)

        if len(states) == 1:
            return res[states[0]]
        return res

    @classmethod
    def update_list(cls):
        # Do not remove blok because 2 or More AnyBlok api may use the same
        # Database

        Association = cls.registry.System.Blok.Association

        def populate_association(blok, links, mode, createifnotexist=False):
            for link in links:
                if createifnotexist:
                    if not cls.query().filter(cls.name == link).count():
                        cls.insert(name=link, state='undefined',
                                   version='None')
                query = Association.query()
                query = query.filter(Association.blok == blok)
                query = query.filter(Association.linked_blok == link)
                query = query.filter(Association.mode == mode)
                if not query.count():
                    Association.insert(blok=blok, linked_blok=link, mode=mode)

        # Create blok if not exist
        for order, blok in enumerate(BlokManager.ordered_bloks):
            b = cls.query().filter(cls.name == blok)
            version = BlokManager.bloks[blok].version
            if b.count():
                b.order = order
                b.version = version
            else:
                cls.insert(name=blok, order=order, version=version)

        # Update required, optional, conditional
        for blok in BlokManager.ordered_bloks:
            entry = BlokManager.bloks[blok]

            populate_association(blok, entry.required, 'required')
            populate_association(blok, entry.optional, 'optional',
                                 createifnotexist=True)
            populate_association(blok, entry.conditional, 'conditional',
                                 createifnotexist=True)

    @classmethod
    def apply_state(cls, *bloks):
        Association = cls.registry.System.Blok.Association
        for blok in bloks:
            # Make the query in the loop to be sure to keep order
            b = cls.query().filter(cls.name == blok).first()
            entry = cls.registry.loaded_bloks[blok]
            if b.state in ('undefined', 'uninstalled', 'toinstall'):
                logger.info("Install the blok %r" % blok)
                entry.update(None)
                b.state = 'installed'
                b.installed_version = b.version
            elif b.state == 'toupdate':
                # FIXME look wrong
                entry.update(b.version)
                bloks = cls.query('name').filter(cls.state == 'installed')
                bloks = bloks.all()
                associate = Association.query()
                associate = associate.filter(Association.blok == blok)
                associate = associate.filter(
                    Association.linked_blok.in_(bloks))
                associate.update({'state': 'toupdate'})
                b.state = 'installed'
                b.installed_version = b.version
            elif b.state == 'touninstall':
                # FIXME look wrong
                entry.uninstall()
                bloks = cls.query('name')
                bloks = bloks.filter(cls.state.in_(('installed', 'toupdate')))
                bloks = bloks.all()
                associate = Association.query()
                associate = associate.filter(Association.blok == blok)
                associate = associate.filter(associate.linked_blok.in_(bloks))
                associate = associate.filter(associate.mode == 'required')
                associate.update({'state': 'touninstall'})
                b.state = 'uninstalled'
                b.installed_version = None

        uninstalled_bloks = cls.query('name').filter(
            cls.state == 'uninstalled').all()
        installed_bloks = cls.query('name').filter(
            cls.state == 'installed').all()

        conditional_bloks_to_install = []
        for blok in uninstalled_bloks:
            total_association_count = Association.query().filter(
                Association.blok == blok,
                Association.mode == 'conditional').count()
            association_count = Association.query().filter(
                Association.blok == blok,
                Association.mode == 'conditional',
                Association.linked_blok.in_(installed_bloks)).count()
            if total_association_count:
                if total_association_count == association_count:
                    conditional_bloks_to_install.append(blok[0])

        if conditional_bloks_to_install:
            for b in conditional_bloks_to_install:
                query = cls.query().filter(cls.name == b)
                query.update({'state': 'toinstall'})

            return True
        else:
            for blok in bloks:
                # Make the query in the loop to be sure to keep order
                entry = cls.registry.loaded_bloks[blok]
                entry.load()

        return False


@target_registry(System.Blok)
class Association:

    blok = String(foreign_key=(System.Blok, 'name'),
                  nullable=False, primary_key=True)
    linked_blok = String(foreign_key=(System.Blok, 'name'),
                         nullable=False, primary_key=True)
    mode = String(nullable=False, primary_key=True)
