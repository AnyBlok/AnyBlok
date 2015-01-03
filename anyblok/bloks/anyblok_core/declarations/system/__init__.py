# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations


@Declarations.register(Declarations.Model)
class System:
    pass

from . import model  # noqa
from . import field  # noqa
from . import column  # noqa
from . import relationship  # noqa
from . import blok  # noqa
from . import cache  # noqa
