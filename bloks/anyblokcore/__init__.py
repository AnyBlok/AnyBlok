# -*- coding: utf-8 -*-
from anyblok.blok import Blok
from . import _fields, _columns, _relationship  # noqa


class AnyBlokCore(Blok):

    autoinstall = True
    priority = 0

    css = [
        'static/css/core.css',
    ]
