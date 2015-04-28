# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy import Sequence as SQLASequence


register = Declarations.register
Integer = Declarations.Column.Integer
String = Declarations.Column.String
System = Declarations.Model.System


@register(System)
class Sequence:

    _cls_seq_name = 'system_sequence_seq_name'

    id = Integer(primary_key=True)
    code = String(nullable=False)
    suffix = String()
    number = Integer(nullable=False)
    prefix = String()
    seq_name = String(nullable=False)

    @classmethod
    def initialize_model(cls):
        super(Sequence, cls).initialize_model()
        seq = SQLASequence(cls._cls_seq_name)
        seq.create(cls.registry.bind)

    @classmethod
    def create_sequence(cls, values):
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
        return super(Sequence, cls).insert(**cls.create_sequence(kwargs))

    @classmethod
    def multi_insert(cls, *args):
        res = [cls.create_sequence(x) for x in args]
        return super(Sequence, cls).multi_insert(*res)

    def nextval(self):
        nextval = self.registry.execute(SQLASequence(self.seq_name))
        self.update(dict(number=nextval))
        return '%s%d%s' % (self.prefix + '_' if self.prefix else '', nextval,
                           '_' + self.suffix if self.suffix else '')

    @classmethod
    def nextvalBy(cls, **kwargs):
        filters = [getattr(cls, k) == v for k, v in kwargs.items()]
        query = cls.query().filter(*filters)
        if query.count():
            seq = query.first()
            return seq.nextval()

        return None
