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
    """Database sequences.

    This Model allows applications to define and use Database sequences easily.

    It is a rewrapping of `SQLAlchemy sequences
    <http://docs.sqlalchemy.org/en/latest/core/defaults.html
    #sqlalchemy.schema.Sequence>`_, with additional formatting
    capabilities to use them, e.g, in fields of applicative Models.

    Sample usage::

        sequence = registry.System.Sequence.insert(
        code="string code",
        formater="One prefix {seq} One suffix")

    .. seealso:: The :attr:`formater` field.

    To get the next formatted value of the sequence::

        sequence.nextval()

    Full example in a Python shell::

        >>> seq = Sequence.insert(code='SO', formater="{code}-{seq:06d}")
        >>> seq.nextval()
        'SO-000001'
        >>> seq.nextval()
        'SO-000002'
    """

    _cls_seq_name = 'system_sequence_seq_name'

    id = Integer(primary_key=True)
    code = String(nullable=False)
    number = Integer(nullable=False)
    seq_name = String(nullable=False)
    """Name of the sequence in the database.

    Most databases identify sequences by names which must be globally
    unique.

    If not passed at insertion, the value of this field is automatically
    generated.
    """
    formater = String(nullable=False, default="{seq}")
    """Python format string to render the sequence values.

    This format string is used in :meth:`nextval`. Within it, you can use the
    following variables:

       * seq: current value of the underlying database sequence
       * code: :attr:`code` field
       * id: :attr:`id` field
    """

    @classmethod
    def initialize_model(cls):
        """ Create the sequence to determine name """
        super(Sequence, cls).initialize_model()
        seq = SQLASequence(cls._cls_seq_name)
        seq.create(cls.registry.bind)

        to_create = getattr(cls.registry,
                            '_need_sequence_to_create_if_not_exist', ())
        if to_create is None:
            return

        for vals in to_create:
            if cls.query().filter(cls.code == vals['code']).count():
                continue

            formatter = vals.get('formater')
            if formatter is None:
                del vals['formater']

            cls.insert(**vals)

    @classmethod
    def create_sequence(cls, values):
        """Create the database sequence for an instance of Sequence Model.

        :return: suitable field values for insertion of the Model instance
        :rtype: dict
        """
        seq_name = values.get('seq_name')
        if seq_name is None:
            seq_id = cls.registry.execute(SQLASequence(cls._cls_seq_name))
            seq_name = '%s_%d' % (cls.__tablename__, seq_id)
            values['seq_name'] = seq_name

        number = values.setdefault('number', 0)
        if number:
            seq = SQLASequence(seq_name, number)
        else:
            seq = SQLASequence(seq_name)
        seq.create(cls.registry.bind)
        return values

    @classmethod
    def insert(cls, **kwargs):
        """Overwrite to call :meth:`create_sequence` on the fly."""
        return super(Sequence, cls).insert(**cls.create_sequence(kwargs))

    @classmethod
    def multi_insert(cls, *args):
        """Overwrite to call :meth:`create_sequence` on the fly."""
        res = [cls.create_sequence(x) for x in args]
        return super(Sequence, cls).multi_insert(*res)

    def nextval(self):
        """Format and return the next value of the sequence.

        :rtype: str
        """
        nextval = self.registry.execute(SQLASequence(self.seq_name))
        self.update(number=nextval)
        return self.formater.format(code=self.code, seq=nextval, id=self.id)

    @classmethod
    def nextvalBy(cls, **crit):
        """Return next value of the first Sequence matching given criteria.

        :param crit: criteria to match, e.g., ``code=SO``
        :return: :meth:`next_val` result for the first matching Sequence,
                 or ``None`` if there's no match.
        """
        filters = [getattr(cls, k) == v for k, v in crit.items()]
        seq = cls.query().filter(*filters).first()
        if seq is None:
            return None
        return seq.nextval()
