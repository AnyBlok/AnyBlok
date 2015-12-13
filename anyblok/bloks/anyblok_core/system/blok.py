# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import BlokManager
from anyblok import Declarations
from anyblok.column import String, Integer, Selection
from anyblok.field import Function
from logging import getLogger
from os.path import join, isfile


logger = getLogger(__name__)
register = Declarations.register
System = Declarations.Model.System


@register(System)
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
        """ fget of the ``short_description`` Column.Selection

        :rtype: the docstring of the blok
        """
        blok = BlokManager.get(self.name)
        if hasattr(blok, '__doc__'):
            return blok.__doc__ or ''

        return ''

    def get_long_description(self):
        """ fget of the ``long_description`` Column.Selection

        :rtype: the readme file of the blok
        """
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
        """ Return the blok name in function of the wanted states

        :param states: list of the state
        :rtype: list if state is a state, dict if the states is a list
        """
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
        """ Populate the bloks list and update the state of existing bloks
        """
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
        """ Call the rigth method is the blok state change

        .. warning::

            for the uninstallation the method called is ``uninstall_all``

        :param bloks: list of the blok name load by the registry
        """
        for blok in bloks:
            # Make the query in the loop to be sure to keep order
            b = cls.query().filter(cls.name == blok).first()
            if b.state in ('undefined', 'uninstalled', 'toinstall'):
                b.install()
            elif b.state == 'toupdate':
                b.upgrade()

        uninstalled_bloks = cls.query().filter(
            cls.state == 'uninstalled').all().name

        conditional_bloks_to_install = []
        for blok in uninstalled_bloks:
            if cls.check_if_the_conditional_are_installed(blok):
                conditional_bloks_to_install.append(blok)

        if conditional_bloks_to_install:
            for b in conditional_bloks_to_install:
                cls.query().filter(cls.name == b).update(
                    {cls.state: 'toinstall'})

            return True

        return False

    @classmethod
    def uninstall_all(cls, *bloksname):
        """ Search and call the uninstall method for all the uninstalled bloks

        .. warning::

            Use the ``desc order`` to uninstall because we can't uninstall
            a dependancies before

        :param bloksname: list of the blok name to uninstall
        """
        if not bloksname:
            return

        query = cls.query().filter(cls.name.in_(bloksname))
        query = query.order_by(cls.order.desc())
        bloks = query.all()
        if bloks:
            bloks.uninstall()

    @classmethod
    def check_if_the_conditional_are_installed(cls, blok):
        """ Return True if all the conditions to install the blok are satisfied

        :param blok: blok name
        :rtype: boolean
        """
        Association = cls.registry.System.Blok.Association
        total_association_count = Association.query().filter(
            Association.blok == blok,
            Association.mode == 'conditional').count()
        query = Association.query().filter(
            Association.blok == blok,
            Association.mode == 'conditional')
        query = query.join(cls, cls.name == Association.linked_blok)
        query = query.filter(
            cls.state.in_(['installed', 'toinstall', 'toupdate']))
        association_count = query.count()
        if total_association_count:
            if total_association_count == association_count:
                return True

        return False

    def install(self):
        """ Method to install the blok
        """
        logger.info("Install the blok %r" % self.name)
        entry = self.registry.loaded_bloks[self.name]
        entry.update(None)
        self.state = 'installed'
        self.installed_version = self.version

    def upgrade(self):
        """ Method to update the blok
        """
        logger.info("Update the blok %r" % self.name)
        entry = self.registry.loaded_bloks[self.name]
        entry.update(self.installed_version)
        self.state = 'installed'
        self.installed_version = self.version

    def uninstall(self):
        """ Method to uninstall the blok
        """
        logger.info("Uninstall the blok %r" % self.name)
        entry = BlokManager.bloks[self.name](self.registry)
        entry.uninstall()
        self.state = 'uninstalled'
        self.installed_version = None

    def load(self):
        """ Method to load the blok when the registry is completly loaded
        """
        if self.name in BlokManager.bloks:
            logger.info("Load the blok %r" % self.name)
            BlokManager.bloks[self.name](self.registry).load()

    @classmethod
    def load_all(cls):
        """ Load all the installed bloks
        """
        query = cls.query().filter(cls.state == 'installed')
        bloks = query.order_by(cls.order).all()
        if bloks:
            bloks.load()


@register(System.Blok)
class Association:

    MODES = {
        'required': 'Required',
        'optional': 'Optional',
        'conditional': 'Conditional',
    }

    blok = String(foreign_key=System.Blok.use('name'),
                  nullable=False, primary_key=True)
    linked_blok = String(foreign_key=System.Blok.use('name'),
                         nullable=False, primary_key=True)
    mode = Selection(selections=MODES, nullable=False, primary_key=True)
