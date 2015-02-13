# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations, reload_module_if_blok_is_reloaded
register = Declarations.register
Model = Declarations.Model


@register(Declarations.Exception)
class IOException(Exception):
    """ IO exception """


@register(Model)
class IO:
    pass


from . import mapping
reload_module_if_blok_is_reloaded(mapping)
