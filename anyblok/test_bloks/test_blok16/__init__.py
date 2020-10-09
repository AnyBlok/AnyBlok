# This file is a part of the AnyBlok project
#
#    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok


class TestBlok(Blok):

    version = "1.0.0"

    called_methods = []

    def pre_migration(self, latest_version):
        self.__class__.called_methods.append("pre_migration")

    def update(self, latest_version):
        self.__class__.called_methods.append("update")

    def post_migration(self, latest_version):
        self.__class__.called_methods.append("post_migration")

    def update_demo(self, latest_version):
        self.__class__.called_methods.append("update_demo")

    def uninstall(self):
        self.__class__.called_methods.append("uninstall")

    def uninstall_demo(self):
        self.__class__.called_methods.append("uninstall_demo")
