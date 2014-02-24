# -*- coding: utf-8 -*-
from zope.component import getUtility
from . import _logging
log = _logging.log
from zope.component import getGlobalSiteManager
gsm = getGlobalSiteManager()

from . import release


PROMPT = "%(processName)s - %(version)s"


def start(processName, version=release.version, prompt=PROMPT,
          argsparse_group=None, parts_to_load=None, logger=None):
    from .blok import BlokManager
    from ._argsparse import ArgsParseManager

    if parts_to_load is None:
        parts_to_load = ['anyblok']

    BlokManager.load(*parts_to_load)
    description = prompt % {'processName': processName, 'version': version}
    ArgsParseManager.load(description=description,
                          argsparse_group=argsparse_group,
                          parts_to_load=parts_to_load)

    if logger is None:
        logger = {}
    ArgsParseManager.init_logger(**logger)


class AnyBlok:
    """ Main Class use to work on the registry

        This class is known in the ``sys.modules``::

            import AnyBlok
            from AnyBlok import target_registry

    """

    __registry_name__ = 'AnyBlok'
    current_blok = None

    @classmethod
    def target_registry(cls, registry, cls_=None, **kwargs):
        """ Method to add in registry

            Locate on one registry, this method use the ZCA to know which
            ``Adapter.target_registry`` use

            :param registry: An existing AnyBlok registry
            :param cls_: The ``class`` object to add in the registry
            :rtype: cls_
        """

        def call_adapter(self):
            _interface = ''
            if registry == AnyBlok:
                _interface = self.__name__
            else:
                _interface = registry.__interface__

            name = kwargs.get('name', self.__name__)
            adapter = getUtility(AnyBlok.Interface.ICoreInterface, _interface)
            adapter.target_registry(registry, name, self, **kwargs)

            return self

        if cls_:
            return call_adapter(cls_)
        else:
            return call_adapter

    @classmethod
    def remove_registry(cls, registry, cls_=None, **kwargs):
        """ Method to remove in registry

            Locate on one registry, this method use the ZCA to know which
            ``Adapter.remove_registry`` use

            :param registry: An existing AnyBlok registry
            :param cls_: The ``class`` object to remove in the registry
            :rtype: cls_
        """

        def call_adapter(self):
            _interface = registry.__interface__

            name = kwargs.get('name', self.__name__)
            adapter = getUtility(AnyBlok.Interface.ICoreInterface, _interface)
            adapter.remove_registry(registry, name, self, **kwargs)

            return self

        if cls_:
            return call_adapter(cls_)
        else:
            return call_adapter

    @classmethod
    def add_Adapter(cls, interface, cls_):
        """ Method to add a adapter

        :param interface: The ZCA interface
        :param cls_: The ``class`` object to add this interface
        """
        instance = cls_()
        gsm.registerUtility(instance, interface, cls_.__interface__)


from sys import modules
modules['AnyBlok'] = AnyBlok


from . import _imp  # noqa
from . import interface  # noqa
from . import databases  # noqa
from . import core  # noqa
from . import field  # noqa
from . import column  # noqa
from . import relationship  # noqa
from . import model  # noqa
from . import mixin  # noqa
