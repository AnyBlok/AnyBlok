# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from packaging.version import Version, LegacyVersion
import packaging


class VersionComparator:

    def parse_other(self, other):
        if other is None:
            other = LegacyVersion('')
        elif not isinstance(other, (Version, LegacyVersion)):
            other = parse_version(other)

        return other

    def __lt__(self, other):
        other = self.parse_other(other)
        return super(VersionComparator, self).__lt__(other)

    def __le__(self, other):
        other = self.parse_other(other)
        return super(VersionComparator, self).__le__(other)

    def __eq__(self, other):
        other = self.parse_other(other)
        return super(VersionComparator, self).__eq__(other)

    def __ne__(self, other):
        other = self.parse_other(other)
        return super(VersionComparator, self).__ne__(other)

    def __ge__(self, other):
        other = self.parse_other(other)
        return super(VersionComparator, self).__ge__(other)

    def __gt__(self, other):
        other = self.parse_other(other)
        return super(VersionComparator, self).__gt__(other)


class AnyBlokVersion(VersionComparator, Version):
    pass


class AnyBlokLegacyVersion(VersionComparator, LegacyVersion):
    pass


def parse_version(v):
    try:
        return AnyBlokVersion(v)
    except packaging.version.InvalidVersion:
        return AnyBlokLegacyVersion(v)
