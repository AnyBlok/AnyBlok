# -*- coding: utf-8 -*-
from anyblok.blok import Blok


class AnyBlokCore(Blok):

    priority = 0

    css = [
        'static/css/core.css',
    ]

    @classmethod
    def clean_before_reload(cls):
        super(AnyBlokCore, cls).clean_before_reload()
        from AnyBlok import Column
        from AnyBlok import RelationShip
        fields = {
            Column: [
                'Integer',
                'SmallInteger',
                'BigInteger',
                'Boolean',
                'Float',
                'Decimal',
                'Binary',
                'LargeBinary',
                'Date',
                'DateTime',
                'Time',
                'Interval',
                'String',
                'uString',
                'Text',
                'uText',
                'Enum',
            ],
            RelationShip: [
                'One2One',
                'Many2One',
                'One2Many',
                'Many2Many',
            ],
        }
        for registry, children in fields.items():
            for child in children:
                if hasattr(registry, child):
                    delattr(registry, child)
