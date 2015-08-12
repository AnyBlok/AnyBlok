# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy import Sequence as SQLASequence
from anyblok.column import Integer, String


register = Declarations.register
System = Declarations.Model.System


@register(System)
class Sequence:
    """ System sequence """

    _cls_seq_name = 'system_sequence_seq_name'

    id = Integer(primary_key=True)
    code = String(nullable=False)
    number = Integer(nullable=False)
    seq_name = String(nullable=False)
    formater = String(nullable=False, default="{seq}")

    @classmethod
    def initialize_model(cls):
        """ Create the sequence to determine name """
        super(Sequence, cls).initialize_model()
        seq = SQLASequence(cls._cls_seq_name)
        seq.create(cls.registry.bind)

        if hasattr(cls.registry, '_need_sequence_to_create_if_not_exist'):
            if cls.registry._need_sequence_to_create_if_not_exist:
                for vals in cls.registry._need_sequence_to_create_if_not_exist:
                    if vals['formater'] is None:
                        del vals['formater']

                    if cls.query().filter(cls.code == vals['code']).count():
                        continue

                    cls.insert(**vals)

    @classmethod
    def create_sequence(cls, values):
        """ create the sequence for one instance """
        if 'seq_name' in values:
            seq_name = values['seq_name']
        else:
            seq_id = cls.registry.execute(SQLASequence(cls._cls_seq_name))
            seq_name = '%s_%d' % (cls.__tablename__, seq_id)
            values['seq_name'] = seq_name
        if 'number' in values:
            seq = SQLASequence(seq_name, values['number'])
        else:
            values['number'] = 0
            seq = SQLASequence(seq_name)

        seq.create(cls.registry.bind)
        return values

    @classmethod
    def insert(cls, **kwargs):
        """ Overwrite insert """
        return super(Sequence, cls).insert(**cls.create_sequence(kwargs))

    @classmethod
    def multi_insert(cls, *args):
        """ Overwrite multi_insert """
        res = [cls.create_sequence(x) for x in args]
        return super(Sequence, cls).multi_insert(*res)

    def nextval(self):
        """ return the next value of the sequence """
        nextval = self.registry.execute(SQLASequence(self.seq_name))
        self.update(dict(number=nextval))
        return self.formater.format(code=self.code, seq=nextval, id=self.id)

    @classmethod
    def nextvalBy(cls, **kwargs):
        """ Get the first sequence filtering by entries and return the next
        value """
        filters = [getattr(cls, k) == v for k, v in kwargs.items()]
        query = cls.query().filter(*filters)
        if query.count():
            seq = query.first()
            return seq.nextval()

        return None
