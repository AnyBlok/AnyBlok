# -*- coding: utf-8 -*-
from zope.component import getUtility
from . import _logging
log = _logging.log

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

    __registry_name__ = 'AnyBlok'
    current_blok = None

    @classmethod
    def target_registry(cls, registry, cls_=None, **kwargs):

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
            call_adapter(cls_)
        else:
            return call_adapter

    @classmethod
    def remove_registry(cls, registry, cls_=None, **kwargs):

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


from sys import modules
modules['AnyBlok'] = AnyBlok


from . import _imp  # noqa
from . import interface  # noqa
from . import databases  # noqa
from . import core  # noqa
from . import model  # noqa
from . import mixin  # noqa
