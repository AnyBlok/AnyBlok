# -*- coding: utf-8 -*-
from anyblok.blok import Blok


class AnyBlokCore(Blok):

    priority = 0

    imports = [
        'fields',
        'columns',
        'relationship',
        'core',
    ]

    tests = [
        'tests/columns.py',
    ]
