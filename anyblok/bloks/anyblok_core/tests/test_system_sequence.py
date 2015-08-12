# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase


class TestSystemSequence(BlokTestCase):

    def test_nextval_without_prefix_without_suffix(self):
        Sequence = self.registry.System.Sequence
        seq = Sequence.insert(code='test.sequence')
        number = seq.number
        self.assertEqual(seq.nextval(), str(number + 1))
        self.assertEqual(seq.nextval(), str(number + 2))
        self.assertEqual(seq.nextval(), str(number + 3))

    def test_nextval_without_prefix_without_suffix_two_time(self):
        Sequence = self.registry.System.Sequence
        Sequence.insert(code='test.sequence')
        seq = Sequence.insert(code='test.sequence')
        number = seq.number
        self.assertEqual(seq.nextval(), str(number + 1))
        self.assertEqual(seq.nextval(), str(number + 2))
        self.assertEqual(seq.nextval(), str(number + 3))

    def test_nextval_without_prefix_with_suffix(self):
        Sequence = self.registry.System.Sequence
        seq = Sequence.insert(code='test.sequence', formater="{seq}_suffix")
        number = seq.number
        self.assertEqual(seq.nextval(), '%d_suffix' % (number + 1))
        self.assertEqual(seq.nextval(), '%d_suffix' % (number + 2))
        self.assertEqual(seq.nextval(), '%d_suffix' % (number + 3))

    def test_nextval_with_prefix_without_suffix(self):
        Sequence = self.registry.System.Sequence
        seq = Sequence.insert(code='test.sequence', formater='prefix_{seq}')
        number = seq.number
        self.assertEqual(seq.nextval(), 'prefix_%d' % (number + 1))
        self.assertEqual(seq.nextval(), 'prefix_%d' % (number + 2))
        self.assertEqual(seq.nextval(), 'prefix_%d' % (number + 3))

    def test_nextval_with_prefix_with_suffix(self):
        Sequence = self.registry.System.Sequence
        seq = Sequence.insert(code='test.sequence',
                              formater='prefix_{seq}_suffix')
        number = seq.number
        self.assertEqual(seq.nextval(), 'prefix_%d_suffix' % (number + 1))
        self.assertEqual(seq.nextval(), 'prefix_%d_suffix' % (number + 2))
        self.assertEqual(seq.nextval(), 'prefix_%d_suffix' % (number + 3))

    def test_nextval_by_attribute(self):
        Sequence = self.registry.System.Sequence
        seq = Sequence.insert(code='test.sequence')
        number = seq.number
        self.assertEqual(Sequence.nextvalBy(code=seq.code), str(number + 1))
        self.assertEqual(Sequence.nextvalBy(code=seq.code), str(number + 2))
        self.assertEqual(Sequence.nextvalBy(code=seq.code), str(number + 3))
