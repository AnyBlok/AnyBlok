# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations


register = Declarations.register
IO = Declarations.Model.IO


@register(IO)
class Exporter:

    @classmethod
    def get_mode_choices(cls):
        res = super(Exporter, cls).get_mode_choices()
        res.update({'Model.IO.Exporter.XML': 'XML'})
        return res


@register(IO.Exporter)
class XML:

    def __init__(self, exporter):
        self.exporter = exporter

    @classmethod
    def insert(cls, delimiter=None, quotechar=None, fields=None, **kwargs):
        kwargs['mode'] = cls.__registry_name__
        if 'model' in kwargs:
            if not isinstance(kwargs['model'], str):
                kwargs['model'] = kwargs['model'].__registry_name__

        return cls.registry.IO.Exporter.insert(**kwargs)

    def run(self, entries):
        raise NotImplemented
