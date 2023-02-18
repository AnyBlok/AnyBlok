# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import warnings
from pkg_resources import iter_entry_points
from anyblok.imp import ImportManager
from .logging import log
from anyblok.environment import EnvironmentManager
from time import sleep
from sys import modules
from os.path import dirname
from logging import getLogger

logger = getLogger(__name__)


class BlokManagerException(LookupError):
    """Simple exception class for BlokManager """

    def __init__(self, *args, **kwargs):
        EnvironmentManager.set('current_blok', None)
        super(BlokManagerException, self).__init__(*args, **kwargs)


class BlokManager:
    """Manage the bloks for one process

    A blok has a `setuptools` entrypoint, this entry point is defined
    by the ``entry_points`` attribute in the first load

    The ``bloks`` attribute is a dict with all the loaded entry points

    Use this class to import all the bloks in the entrypoint::

        BlokManager.load()

    """

    bloks = {}
    entry_points = None
    ordered_bloks = []
    auto_install = []

    @classmethod
    def list(cls):
        """Return the ordered bloks

        :rtype: list of blok name ordered by loading
        """
        return cls.ordered_bloks

    @classmethod
    def has(cls, blok):
        """Return True if the blok is loaded

        :param blok: the name of the blok
        :rtype: bool
        """
        return blok and blok in cls.ordered_bloks or False

    @classmethod
    def get(cls, blok):
        """Return the loaded blok

        :param blok: the name of the blok
        :rtype: blok instance
        :exception: BlokManagerException
        """
        if not cls.has(blok):
            raise BlokManagerException('%r not found' % blok)

        return cls.bloks[blok]

    @classmethod
    def set(cls, blokname, blok):
        """Add a new blok

        :param blokname: the name of the blok
        :param blok: blok instance
        :exception: BlokManagerException
        """
        if cls.has(blokname):
            raise BlokManagerException('%r already present' % blokname)

        cls.bloks[blokname] = blok
        cls.ordered_bloks.append(blokname)

    @classmethod
    @log(logger, level='debug')
    def reload(cls):
        """Reload the entry points

        Empty the ``bloks`` dict and use the ``entry_points`` attribute to
        load bloks
        :exception: BlokManagerException
        """
        if cls.entry_points is None:
            raise BlokManagerException(
                """You must use the ``load`` classmethod before using """
                """``reload``""")

        entry_points = []
        entry_points += cls.entry_points
        cls.unload()
        cls.load(entry_points=entry_points)

    @classmethod
    @log(logger, level='debug')
    def unload(cls):
        """Unload all the bloks but not the registry """
        cls.bloks = {}
        cls.ordered_bloks = []
        cls.entry_points = None
        cls.auto_install = []
        from .registry import RegistryManager
        RegistryManager.unload()

    @classmethod
    def get_needed_blok_dependencies(cls, blok):
        """Get all dependencies for the blok given

        :param blok:
        :return:
        """
        for required in cls.bloks[blok].required:
            if not cls.get_needed_blok(required):
                cls.add_undefined_blok(required)

            cls.bloks[required].required_by.append(blok)

        for optional in cls.bloks[blok].optional:
            if cls.get_needed_blok(optional):
                cls.bloks[optional].optional_by.append(blok)

        for conditional in cls.bloks[blok].conditional:
            cls.bloks[conditional].conditional_by.append(blok)

        for conflicting in cls.bloks[blok].conflicting:
            cls.bloks[conflicting].conflicting_by.append(blok)

    @classmethod
    def blok_importers(cls, blok):
        EnvironmentManager.set('current_blok', blok)

        if not ImportManager.has(blok):
            # Import only if the blok doesn't exists, do not reload here
            mod = ImportManager.add(blok)
            mod.imports()
        else:
            mod = ImportManager.get(blok)
            mod.reload()

    @classmethod
    def get_needed_blok(cls, blok):
        """Get and import/load the blok given with dependencies

        :param blok:
        :return:
        """
        if cls.has(blok):
            return True

        if blok not in cls.bloks:
            return False

        cls.get_needed_blok_dependencies(blok)
        cls.ordered_bloks.append(blok)
        cls.blok_importers(blok)

        if cls.bloks[blok].autoinstall:
            cls.auto_install.append(blok)

        return True

    @classmethod
    def add_undefined_blok(cls, name):
        blok = type(
            'undefined-blok.%s' % name,
            (UndefinedBlok,),
            dict(name=name, required_by=[], optional_by=[], conditional_by=[],
                 conflicting_by=[])
        )
        blok.__doc__ = "Blok undefined"
        cls.set(name, blok)
        # here they are not python module to load, but this action
        # add the undefined blok in registryManager
        cls.blok_importers(name)

    @classmethod
    @log(logger, level='debug')
    def load(cls, entry_points=('bloks',)):
        """Load all the bloks and import them

        :param entry_points: Used by ``iter_entry_points`` to get the blok
        :exception: BlokManagerException
        """
        if not entry_points:
            raise BlokManagerException("The entry_points mustn't be empty")

        cls.entry_points = entry_points

        if EnvironmentManager.get('current_blok'):
            while EnvironmentManager.get('current_blok'):  # pragma: no cover
                sleep(0.1)

        EnvironmentManager.set('current_blok', 'start')

        bloks = []
        for entry_point in entry_points:
            count = 0
            for i in iter_entry_points(entry_point):
                count += 1
                blok = i.load()
                blok.required_by = []
                blok.optional_by = []
                blok.conditional_by = []
                blok.conflicting_by = []
                cls.set(i.name, blok)
                blok.name = i.name
                bloks.append((blok.priority, i.name))

            if not count:
                raise BlokManagerException(
                    "Invalid bloks group %r" % entry_point)

        # Empty the ordered blok to reload it depending on the priority
        cls.ordered_bloks = []
        bloks.sort()

        try:
            while bloks:
                blok = bloks.pop(0)[1]
                cls.get_needed_blok(blok)

        finally:
            EnvironmentManager.set('current_blok', None)

    @classmethod
    def getPath(cls, blok):
        """Return the path of the blok

        :param blok: blok name in ``ordered_bloks``
        :rtype: absolute path
        """
        blok = cls.get(blok)
        return dirname(modules[blok.__module__].__file__)


class Blok:
    """Super class for all the bloks

    define the default value for:

    * priority: order to load the blok
    * required: list of the bloks required to install this blok
    * optional: list of the bloks to be installed if present in the blok list
    * conditional: if all the bloks of this list are installed then install
      this blok
    """

    autoinstall = False
    priority = 100
    required = []
    optional = []
    conditional = []
    conflicting = []
    name = None  # set by the BlokManager
    author = ''
    logo = ''

    def __init__(self, registry):
        self.anyblok = registry

    @property
    def registry(self):  # pragma: no cover
        warnings.warn(
            "'registry' attribute is deprecated because SQLAlchemy 1.4 add is "
            "own 'registry' attribute. Replace it by 'anyblok' attribute",
            DeprecationWarning, stacklevel=2)

        return self.anyblok

    @classmethod
    def import_declaration_module(cls):
        """Do the python import for the Declaration of the model or other
        """

    def update(self, latest_version):
        """Called on install or update

        :param latest_version: latest version installed, if the blok has never
                               been installed, latest_version is None
        """

    def pre_migration(self, latest_version):
        """Called on update, before the auto migration

        .. warning::

            You can not use the ORM

        :param latest_version: latest version installed, if the blok has never
                               been installed, latest_version is None
        """

    def post_migration(self, latest_version):
        """Called on update, after the auto migration

        :param latest_version: latest version installed, if the blok has never
                               been installed, latest_version is None
        """

    def update_demo(self, latest_version):
        """Called on install or update to set or update demo data if
        `System.Parameter.get("with-demo", False) is True`

        :param latest_version: latest version installed, if the blok has never
                               been installed, latest_version is None
        """

    def uninstall_demo(self):
        """Called on uninstall demo data if
        `System.Parameter.get("with-demo", False) is True`
        """

    def uninstall(self):
        """Called on uninstall
        """

    def load(self):
        """Called on start / launch
        """


class UndefinedBlok(Blok):

    version = '0.0.0'
