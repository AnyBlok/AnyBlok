# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
LargeBinary = Declarations.Column.LargeBinary
Boolean = Declarations.Column.Boolean


@Declarations.register(Declarations.Model.IO)
class Importer(Declarations.Mixin.IOMixin):

    file = LargeBinary(nullable=False)
    commit_in_each_grouped = Boolean(default=True)
