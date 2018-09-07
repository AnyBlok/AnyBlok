# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from pkg_resources import SetuptoolsVersion, SetuptoolsLegacyVersion
from pkg_resources.extern import packaging


class VersionComparator:

    def __lt__(self, other):
        if other is None:
            other = SetuptoolsLegacyVersion('')
        elif not isinstance(
            other, (SetuptoolsVersion, SetuptoolsLegacyVersion)
        ):
            other = parse_version(other)

        return super(VersionComparator, self).__lt__(other)

    def __le__(self, other):
        if other is None:
            other = SetuptoolsLegacyVersion('')
        elif not isinstance(
            other, (SetuptoolsVersion, SetuptoolsLegacyVersion)
        ):
            other = parse_version(other)

        return super(VersionComparator, self).__le__(other)

    def __eq__(self, other):
        if other is None:
            other = SetuptoolsLegacyVersion('')
        elif not isinstance(
            other, (SetuptoolsVersion, SetuptoolsLegacyVersion)
        ):
            other = parse_version(other)

        return super(VersionComparator, self).__eq__(other)

    def __ne__(self, other):
        if other is None:
            other = SetuptoolsLegacyVersion('')
        elif not isinstance(
            other, (SetuptoolsVersion, SetuptoolsLegacyVersion)
        ):
            other = parse_version(other)

        return super(VersionComparator, self).__ne__(other)

    def __ge__(self, other):
        if other is None:
            other = SetuptoolsLegacyVersion('')
        elif not isinstance(
            other, (SetuptoolsVersion, SetuptoolsLegacyVersion)
        ):
            other = parse_version(other)

        return super(VersionComparator, self).__ge__(other)

    def __gt__(self, other):
        if other is None:
            other = SetuptoolsLegacyVersion('')
        elif not isinstance(
            other, (SetuptoolsVersion, SetuptoolsLegacyVersion)
        ):
            other = parse_version(other)

        return super(VersionComparator, self).__gt__(other)


class AnyBlokVersion(VersionComparator, SetuptoolsVersion):
    pass


class AnyBlokLegacyVersion(VersionComparator, SetuptoolsLegacyVersion):
    pass


def parse_version(v):
    try:
        return AnyBlokVersion(v)
    except packaging.version.InvalidVersion:
        return AnyBlokLegacyVersion(v)
