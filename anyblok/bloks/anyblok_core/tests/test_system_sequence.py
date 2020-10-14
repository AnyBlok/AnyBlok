# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.testing import sgdb_in


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']), reason='ISSUE #89')
@pytest.mark.usefixtures('rollback_registry')
class TestSystemSequence:

    def test_nextval_without_prefix_without_suffix(self, rollback_registry):
        registry = rollback_registry
        Sequence = registry.System.Sequence
        seq = Sequence.insert(code='test.sequence')
        assert seq.number is None
        assert seq.nextval() == '1'
        assert seq.nextval() == '2'
        assert seq.nextval() == '3'
        assert seq.number == 3

    def test_nextval_with_start_value(self, rollback_registry):
        registry = rollback_registry
        Sequence = registry.System.Sequence
        seq = Sequence.insert(code='test.sequence', start=10)
        assert seq.number is None
        assert seq.nextval() == '10'
        assert seq.nextval() == '11'
        assert seq.nextval() == '12'
        assert seq.number == 12

    def test_nextval_without_prefix_without_suffix_two_time(
        self, rollback_registry
    ):
        registry = rollback_registry
        Sequence = registry.System.Sequence
        Sequence.insert(code='test.sequence')
        seq = Sequence.insert(code='test.sequence')
        number = seq.number
        assert number is None
        assert seq.nextval() == '1'
        assert seq.nextval() == '2'
        assert seq.nextval() == '3'

    def test_nextval_without_prefix_with_suffix(self, rollback_registry):
        registry = rollback_registry
        Sequence = registry.System.Sequence
        seq = Sequence.insert(code='test.sequence', formater="{seq}_suffix")
        number = seq.number
        assert number is None
        assert seq.nextval() == '%d_suffix' % 1
        assert seq.nextval() == '%d_suffix' % 2
        assert seq.nextval() == '%d_suffix' % 3

    def test_nextval_with_prefix_without_suffix(self, rollback_registry):
        registry = rollback_registry
        Sequence = registry.System.Sequence
        seq = Sequence.insert(code='test.sequence', formater='prefix_{seq}')
        number = seq.number
        assert number is None
        assert seq.nextval() == 'prefix_%d' % 1
        assert seq.nextval() == 'prefix_%d' % 2
        assert seq.nextval() == 'prefix_%d' % 3

    def test_nextval_with_prefix_with_suffix(self, rollback_registry):
        registry = rollback_registry
        Sequence = registry.System.Sequence
        seq = Sequence.insert(code='test.sequence',
                              formater='prefix_{seq}_suffix')
        number = seq.number
        assert number is None
        assert seq.nextval() == 'prefix_%d_suffix' % 1
        assert seq.nextval() == 'prefix_%d_suffix' % 2
        assert seq.nextval() == 'prefix_%d_suffix' % 3

    def test_nextval_by_attribute(self, rollback_registry):
        registry = rollback_registry
        Sequence = registry.System.Sequence
        seq = Sequence.insert(code='test.sequence')
        number = seq.number
        assert number is None
        assert Sequence.nextvalBy(code=seq.code) == '1'
        assert Sequence.nextvalBy(code=seq.code) == '2'
        assert Sequence.nextvalBy(code=seq.code) == '3'

    def test_sequence_with_gap_rollback(self, rollback_registry):
        registry = rollback_registry
        Sequence = registry.System.Sequence
        seq = Sequence.insert(code='test.sequence', no_gap=False)
        number = seq.number
        assert number is None
        assert Sequence.nextvalBy(code=seq.code) == '1'
        registry.commit()
        assert Sequence.nextvalBy(code=seq.code) == '2'
        registry.rollback()
        assert Sequence.nextvalBy(code=seq.code) == '3'

    def test_sequence_with_no_gap_rollback(self, rollback_registry):
        registry = rollback_registry
        Sequence = registry.System.Sequence
        seq = Sequence.insert(code='test.sequence.nogap', no_gap=True)
        number = seq.number
        assert number is None
        assert Sequence.nextvalBy(code=seq.code) == '1'
        registry.commit()
        assert Sequence.nextvalBy(code=seq.code) == '2'
        registry.rollback()
        assert Sequence.nextvalBy(code=seq.code) == '2'
