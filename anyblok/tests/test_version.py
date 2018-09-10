# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.version import parse_version
from unittest import TestCase


class TestParseVersion(TestCase):

    def test_gt(self):
        version = parse_version('1.2.3')
        self.assertTrue(version > '1.1.13')
        self.assertFalse(version > '1.12.3')
        self.assertFalse(version > '1.2.3')

    def test_ge(self):
        version = parse_version('1.2.3')
        self.assertTrue(version >= '1.1.13')
        self.assertFalse(version >= '1.12.3')
        self.assertTrue(version >= '1.2.3')

    def test_eq(self):
        version = parse_version('1.2.3')
        self.assertFalse(version == '1.1.13')
        self.assertFalse(version == '1.12.3')
        self.assertTrue(version == '1.2.3')

    def test_ne(self):
        version = parse_version('1.2.3')
        self.assertTrue(version != '1.1.13')
        self.assertTrue(version != '1.12.3')
        self.assertFalse(version != '1.2.3')

    def test_lt(self):
        version = parse_version('1.2.3')
        self.assertFalse(version < '1.1.13')
        self.assertTrue(version < '1.12.3')
        self.assertFalse(version < '1.2.3')

    def test_le(self):
        version = parse_version('1.2.3')
        self.assertFalse(version <= '1.1.13')
        self.assertTrue(version <= '1.12.3')
        self.assertTrue(version <= '1.2.3')

    def test_wrong_version(self):
        parse_version('Wrong version')
