# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2020 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy import Sequence as SQLASequence
from anyblok.column import Integer, String, Boolean


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

    You can create a Sequence without gap warranty using `no_gap` while
    creating the sequence::


        >>> seq = Sequence.insert(
                code='SO', formater="{code}-{seq:06d}", no_gap=True)
        >>> commit()

        >>> # Transaction 1:
        >>> Sequence.nextvalBy(code='SO')
        'SO-000001'

        >>> # Concurrent transaction 2:
        >>> Sequence.nextvalBy(code='SO')
        ...
        sqlalchemy.exc.OperationalError: (psycopg2.errors.LockNotAvailable)
        ...
    """

    _cls_seq_name = 'system_sequence_seq_name'

    id = Integer(primary_key=True)
    code = String(nullable=False)
    start = Integer(default=1)
    current = Integer(default=None)
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
    no_gap = Boolean(default=False, nullable=False)
    """If no_gap is False, it will use Database sequence. Otherwise, if `True`
    it will ensure there is no gap while getting next value locking the
    sequence row until transaction is released (rollback/commit). If a
    concurrent transaction try to get a lock an
    `sqlalchemy.exc.OperationalError: (psycopg2.errors.LockNotAvailable)`
    exception is raised.
    """

    @classmethod
    def initialize_model(cls):
        """ Create the sequence to determine name """
        super(Sequence, cls).initialize_model()
        seq = SQLASequence(cls._cls_seq_name)
        seq.create(cls.anyblok.bind)

        to_create = getattr(cls.anyblok,
                            '_need_sequence_to_create_if_not_exist', ())
        if to_create is None:
            return

        for vals in to_create:
            if cls.query().filter(cls.code == vals['code']).count():
                continue  # pragma: no cover

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
        start = values.setdefault('start', 1)

        if values.get("no_gap"):
            values.setdefault('seq_name', values.get("code", "no_gap"))
        else:
            if seq_name is None:
                seq_id = cls.anyblok.execute(SQLASequence(cls._cls_seq_name))
                seq_name = '%s_%d' % (cls.__tablename__, seq_id)
                values['seq_name'] = seq_name

            seq = SQLASequence(seq_name, start=start)
            seq.create(cls.anyblok.bind)
        return values

    @classmethod
    def insert(cls, **kwargs):
        """Overwrite to call :meth:`create_sequence` on the fly."""
        return super(Sequence, cls).insert(**cls.create_sequence(kwargs))

    @classmethod
    def multi_insert(cls, *args):  # pragma: no cover
        """Overwrite to call :meth:`create_sequence` on the fly."""
        res = [cls.create_sequence(x) for x in args]
        return super(Sequence, cls).multi_insert(*res)

    def nextval(self):
        """Format and return the next value of the sequence.

        :rtype: str
        """
        if self.no_gap:
            self.refresh(with_for_update={"nowait": True})
            nextval = self.start if self.current is None else self.current + 1
        else:
            nextval = self.anyblok.execute(SQLASequence(self.seq_name))
        self.update(current=nextval)
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
            return None  # pragma: no cover
        return seq.nextval()
