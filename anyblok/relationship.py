# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Pierre Verkest <pverkest@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy import Table, Column, ForeignKeyConstraint
from sqlalchemy.orm import (relationships, backref, relationship, base,
                            attributes)
from sqlalchemy.schema import Column as SA_Column
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import exc as sa_exc, util
from sqlalchemy_utils.functions import get_class_by_table
from .field import Field, FieldException
from .mapper import ModelAdapter, ModelAttribute, ModelRepr, format_schema
from anyblok.common import anyblok_column_prefix
from sqlalchemy.ext.orderinglist import OrderingList, _unsugar_count_from
from types import FunctionType

from logging import getLogger


logger = getLogger(__name__)


class RelationshipProperty(relationships.RelationshipProperty):

    def __init__(self, *args, **kwargs):
        self.relationship_field = kwargs.pop('relationship_field')
        super(RelationshipProperty, self).__init__(*args, **kwargs)

    def _generate_backref(self):  # noqa
        """Interpret the 'backref' instruction to create a
        :func:`.relationship` complementary to this one."""

        if self.parent.non_primary:
            return  # pragma: no cover
        if self.backref is not None and not self.back_populates:
            if isinstance(self.backref, util.string_types):
                backref_key, kwargs = self.backref, {}  # pragma: no cover
            else:
                backref_key, kwargs = self.backref
            mapper = self.mapper.primary_mapper()

            check = set(mapper.iterate_to_root()).\
                union(mapper.self_and_descendants)
            for m in check:
                if m.has_property(backref_key):
                    raise sa_exc.ArgumentError(  # pragma: no cover
                        "Error creating backref "
                        "'%s' on relationship '%s': property of that "
                        "name exists on mapper '%s'" %
                        (backref_key, self, m))

            # determine primaryjoin/secondaryjoin for the
            # backref.  Use the one we had, so that
            # a custom join doesn't have to be specified in
            # both directions.
            if self.secondary is not None:
                # for many to many, just switch primaryjoin/
                # secondaryjoin.   use the annotated
                # pj/sj on the _join_condition.
                pj = kwargs.pop(  # pragma: no cover
                    'primaryjoin',
                    self._join_condition.secondaryjoin_minus_local)
                sj = kwargs.pop(  # pragma: no cover
                    'secondaryjoin',
                    self._join_condition.primaryjoin_minus_local)
            else:
                pj = kwargs.pop(
                    'primaryjoin',
                    self._join_condition.primaryjoin_reverse_remote)
                sj = kwargs.pop('secondaryjoin', None)
                if sj:
                    raise sa_exc.InvalidRequestError(  # pragma: no cover
                        "Can't assign 'secondaryjoin' on a backref "
                        "against a non-secondary relationship."
                    )

            foreign_keys = kwargs.pop('foreign_keys',
                                      self._user_defined_foreign_keys)
            parent = self.parent.primary_mapper()
            kwargs.setdefault('viewonly', self.viewonly)
            kwargs.setdefault('post_update', self.post_update)
            kwargs.setdefault('passive_updates', self.passive_updates)
            self.back_populates = backref_key
            _relationship = RelationshipProperty2(
                parent, self.secondary,
                pj, sj,
                foreign_keys=foreign_keys,
                back_populates=self.key,
                relationship_field=self.relationship_field,
                **kwargs)

            mapper._configure_property(backref_key, _relationship)

        if self.back_populates:
            self._add_reverse_property(self.back_populates)


def register_descriptor(class_, key, comparator=None,
                        parententity=None, doc=None, relationship_field=None):
    manager = base.manager_of_class(class_)
    descriptor = relationship_field.InstrumentedAttribute(
        class_, key, comparator=comparator, parententity=parententity,
        relationship_field=relationship_field)
    descriptor.__doc__ = doc
    manager.instrument_attribute(key, descriptor)
    return descriptor


class RelationshipProperty2(relationships.RelationshipProperty):

    def __init__(self, *args, **kwargs):
        self.relationship_field = kwargs.pop('relationship_field')
        super(RelationshipProperty2, self).__init__(*args, **kwargs)

    def instrument_class(self, mapper):
        register_descriptor(
            mapper.class_,
            self.key,
            comparator=self.comparator_factory(self, mapper),
            parententity=mapper,
            doc=self.doc,
            relationship_field=self.relationship_field,
        )


class RelationShipList:  # don't inherit list

    def append(self, x):
        res = super(RelationShipList, self).append(x)
        self.relationship_field_append_value(x)
        return res

    def extend(self, L):
        res = super(RelationShipList, self).extend(L)
        for el in L:
            self.relationship_field_append_value(el)

        return res

    def insert(self, i, x):
        res = super(RelationShipList, self).insert(i, x)
        self.relationship_field_append_value(x)
        return res

    def remove(self, x):
        self.relationship_field_remove_value(x)
        return super(RelationShipList, self).remove(x)

    def pop(self, *args, **kwargs):
        res = super(RelationShipList, self).pop(*args, **kwargs)
        self.relationship_field_remove_value(res)
        return res

    def clear(self):
        for x in self:
            self.relationship_field_remove_value(x)

        return super(RelationShipList, self).clear()


class RelationShip(Field):
    """ RelationShip class

    The RelationShip class is used to define the type of SQL field Declarations

    Add a new relation ship type::

        @Declarations.register(Declarations.RelationShip)
        class Many2one:
            pass

    the relationship column are forbidden because the model can be used on
    the model
    """

    def __init__(self, *args, **kwargs):
        self.forbid_instance(RelationShip)
        if 'model' in kwargs:
            self.model = ModelAdapter(kwargs.pop('model'))
        else:
            raise FieldException("model is required attribut")

        super(RelationShip, self).__init__(*args, **kwargs)

        if 'info' not in self.kwargs:
            self.kwargs['info'] = {}

        self.kwargs['info']['remote_model'] = self.model.model_name
        self.backref_properties = {}

    def autodoc_get_properties(self):
        res = super(RelationShip, self).autodoc_get_properties()
        res['model'] = self.model
        return res

    def apply_instrumentedlist(self, registry, namespace, fieldname):
        """ Add the InstrumentedList class to replace List class as result
        of the query

        :param registry: current registry
        """
        InstrumentedList = registry.InstrumentedList
        if self.kwargs.get('collection_class'):
            collection_class = self.kwargs['collection_class']
            if isinstance(collection_class, FunctionType):
                if getattr(
                    collection_class, 'is_an_anyblok_instrumented_list', False
                ) is True:
                    InstrumentedList = self.kwargs['collection_class'](registry)

        self.kwargs['collection_class'] = InstrumentedList
        self.backref_properties['collection_class'] = registry.InstrumentedList

    def define_backref_properties(self, registry, namespace, properties):
        """ Add in the backref_properties, new property for the backref

        :param registry: current registry
        :param namespace: name of the model
        :param properties: properties known of the model
        """
        pass

    def format_backref(self, registry, namespace, fieldname, properties):
        """ Create the real backref, with the backref string and the
        backref properties

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        """
        _backref = self.kwargs.get('backref')
        if not _backref:
            return

        if isinstance(_backref, (list, tuple)):
            _backref, backref_properties = _backref
            if backref_properties.get('collection_class'):
                collection_class = backref_properties['collection_class']
                if isinstance(collection_class, FunctionType):
                    if getattr(
                        collection_class, 'is_an_anyblok_instrumented_list',
                        False
                    ) is True:
                        backref_properties[
                            'collection_class'] = collection_class(registry)

            self.backref_properties.update(backref_properties)

        self.define_backref_properties(registry, namespace, properties)

        if self.backref_properties:
            self.kwargs['backref'] = backref(_backref,
                                             **self.backref_properties)
            mapper = ModelAttribute(self.model.model_name, _backref)
            if not mapper.is_declared(registry):
                mapper.add_fake_relationship(registry, namespace, fieldname)

    def get_relationship_cls(self):
        return relationship

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        :rtype: sqlalchemy relation ship instance
        """
        self.model.check_model(registry)
        self.format_label(fieldname)
        self.kwargs['info']['label'] = self.label
        self.kwargs['info']['rtype'] = self.__class__.__name__
        self.apply_instrumentedlist(registry, namespace, fieldname)
        self.format_backref(registry, namespace, fieldname, properties)
        return self.get_relationship_cls()(
            self.model.modelname(registry), **self.kwargs)

    def must_be_declared_as_attr(self):
        """ Return True, because it is a relationship """
        return True

    def init_expire_attributes(self, registry, namespace, fieldname):
        """Init dict of expiration properties

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        """
        if namespace not in registry.expire_attributes:
            registry.expire_attributes[namespace] = {}

        if fieldname not in registry.expire_attributes[namespace]:
            registry.expire_attributes[namespace][fieldname] = set()


class RelationShipListMany2One:

    def relationship_field_append_value(self, value):
        for model_field, rfield in self.relationship_fied.link_between_columns:
            self.relationship_fied.apply_value_to(
                value, model_field, getattr(value, self.fieldname), rfield)

    def relationship_field_remove_value(self, value):
        for model_field, rfield in self.relationship_fied.link_between_columns:
            setattr(value, anyblok_column_prefix + model_field, None)


class Many2One(RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = Many2One(label="The relationship",
                                    model=Model.RemoteModel,
                                    remote_columns="The remote column",
                                    column_names="The column which have the "
                                                 "foreigh key",
                                    nullable=True,
                                    unique=False,
                                    index=False,
                                    primary_key=False,
                                    one2many="themodels")

    If the ``remote_columns`` are not define then, the system takes the primary
    key of the remote model

    If the column doesn't exist, the column will be created. Use the
    nullable option.
    If the name is not filled, the name is "'remote table'_'remote colum'"

    :param model: the remote model
    :param remote_columns: the column name on the remote model
    :param column_names: the column on the model which have the foreign key
    :param nullable: If the column_names is nullable
    :param unique: If True, add the unique constraint on the columns
    :param index: If True, add the index constraint on the columns
    :param primary_key: If True, add the primary_key=True on the columns
    :param one2many: create the one2many link with this many2one
    """
    use_hybrid_property = True

    def __init__(self, **kwargs):
        super(Many2One, self).__init__(**kwargs)

        self._remote_columns = None
        if 'remote_columns' in kwargs:
            self._remote_columns = self.kwargs.pop('remote_columns')
            if not isinstance(self._remote_columns, (list, tuple)):
                self._remote_columns = [self._remote_columns]

        self.primary_key = self.kwargs.pop('primary_key', False)
        self.kwargs['info']['primary_key'] = self.primary_key

        self.nullable = False if self.primary_key else True
        nullable = self.kwargs.pop('nullable', True)
        if not self.primary_key:
            self.nullable = nullable

        self.kwargs['info']['nullable'] = self.nullable

        self.unique = self.kwargs.pop('unique', False)
        self.kwargs['info']['unique'] = self.unique

        self.index = self.kwargs.pop('index', False)
        self.kwargs['info']['index'] = self.index

        if 'one2many' in kwargs:
            self.kwargs['backref'] = backref = self.kwargs.pop('one2many')
            self.kwargs['info']['remote_name'] = backref
            if isinstance(backref, (list, tuple)):
                self.kwargs['info']['remote_name'] = backref[0]
                self.backref_properties.update(**backref[1])

        self._column_names = None
        if 'column_names' in kwargs:
            self._column_names = self.kwargs.pop('column_names')
            if not isinstance(self._column_names, (list, tuple)):
                self._column_names = [self._column_names]

        self.foreign_key_options = self.kwargs.pop('foreign_key_options', {})
        self.cascade = self.kwargs.pop('cascade', 'save-update, merge')

    def autodoc_get_properties(self):
        res = super(Many2One, self).autodoc_get_properties()
        res['remote_columns'] = self._remote_columns
        res['column_names'] = self._column_names
        res['unique'] = self.unique
        res['index'] = self.index
        res['primary_key'] = self.primary_key
        return res

    autodoc_omit_property_values = Field.autodoc_omit_property_values.union((
        ('remote_columns', None),
        ('column_names', None),
        ('unique', False),
        ('primary_key', False),
    ))

    def get_remote_columns(self, registry):
        if self._remote_columns is None:
            return self.model.primary_keys(registry)

        return [ModelAttribute(self.model.model_name, x)
                for x in self._remote_columns]

    def get_columns_names(self, registry, namespace, fieldname, remote_columns):
        if self._column_names is None:
            model = ModelRepr(namespace)
            column_names = model.foreign_keys_for(
                registry, self.model.model_name)
            if not column_names:
                column_names = []
                for x in remote_columns:
                    cname = fieldname + '_' + x.attribute_name
                    column_names.append(ModelAttribute(namespace, cname))
        else:
            column_names = [ModelAttribute(namespace, x)
                            for x in self._column_names]

        return column_names

    def update_local_and_remote_columns_names(self, registry, namespace,
                                              fieldname):
        self.remote_columns = self.get_remote_columns(registry)
        self.kwargs['info']['remote_columns'] = [x.attribute_name
                                                 for x in self.remote_columns]
        self.column_names = self.get_columns_names(
            registry, namespace, fieldname, self.remote_columns)

    def get_property(self, registry, namespace, fieldname, properties):
        """Return the property of the field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known to the model
        """
        res = super(Many2One, self).get_property(
            registry, namespace, fieldname, properties)
        # force the info value in hybrid_property because since SQLAlchemy
        # 1.1.* the info is not propagate
        res.info = self.kwargs['info']
        return res

    def add_expire_attributes(self, registry, namespace, fieldname, cname):
        self.init_expire_attributes(registry, namespace, cname)
        registry.expire_attributes[namespace][cname].add((fieldname,))
        if self.kwargs.get('backref'):
            backref = self.kwargs['backref']
            if isinstance(backref, (list, tuple)):
                backref = backref[0]

            registry.expire_attributes[namespace][cname].add(
                (fieldname, backref))

    def update_properties(self, registry, namespace, fieldname, properties):
        """ Create the column which has the foreign key if the column doesn't
        exist

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        """
        add_fksc = False
        self.link_between_columns = []
        self.model.check_model(registry)
        self.update_local_and_remote_columns_names(
            registry, namespace, fieldname)
        if fieldname in [x.attribute_name for x in self.column_names]:
            raise FieldException("The column_names and the fieldname %r are "
                                 "the same, please choose another "
                                 "column_names" % fieldname)

        self.kwargs['info']['local_columns'] = [
            x.attribute_name for x in self.column_names]
        remote_types = {x.attribute_name: x.native_type(registry)
                        for x in self.remote_columns}
        remote_columns = {x.attribute_name: x
                          for x in self.remote_columns}
        for cname in self.column_names:
            if cname.is_declared(registry):
                del remote_types[cname.get_fk_column(registry)]

        col_names = []
        fk_names = []
        for cname in self.column_names:
            self.add_expire_attributes(registry, namespace, fieldname,
                                       cname.attribute_name)
            if not cname.is_declared(registry):
                rc, remote_type = self.get_column_information(
                    registry, cname, remote_types, fieldname)
                cname.add_fake_column(registry)
                foreign_key = remote_columns[rc].get_fk_name(registry)
                self.create_column(cname, remote_type, foreign_key, properties)
                add_fksc = True
                fk_name = remote_columns[rc]
            else:
                fk_name = cname.get_fk_mapper(registry)

            col_names.append(cname.attribute_name)
            fk_names.append(fk_name.get_fk_name(registry))
            self.link_between_columns.append((cname.attribute_name,
                                              fk_name.attribute_name))

        if namespace == self.model.model_name:
            self.kwargs['remote_side'] = [
                properties[anyblok_column_prefix + x.attribute_name]
                for x in self.remote_columns]

        if (len(self.column_names) > 1 or add_fksc) and col_names and fk_names:
            self.col_names = col_names
            self.fk_names = fk_names
            properties['add_in_table_args'].append(self)

    def remote_model_is_a_table(self, registry):
        if self.model.model_name not in registry.loaded_namespaces:
            return True  # by default

        return hasattr(registry.get(self.model.model_name), '__table__')

    def update_table_args(self, registry, Model):
        """Add foreign key constraint in table args"""
        if not self.remote_model_is_a_table(registry):
            return []  # pragma: no cover

        return [
            ForeignKeyConstraint(self.col_names, self.fk_names,
                                 **self.foreign_key_options)
        ]

    def get_column_information(self, registry, cname, remote_types, fieldname):
        if len(remote_types) == 1:
            rc = [x for x in remote_types][0]
            return rc, remote_types[rc]
        else:
            rc = cname.get_fk_column(registry)
            if rc is None:
                rc = cname.attribute_name[len(fieldname) + 1:]

            if rc in remote_types:
                return rc, remote_types[rc]
            else:
                cname.get_fk_column(registry)
                raise FieldException("Can not create the local "
                                     "column %r" % cname.attribute_name)

    def apply_instrumentedlist(self, registry, namespace, fieldname):
        """ Add the InstrumentedList class to replace List class as result
        of the query

        :param registry: current registry
        """
        properties = {
            'fieldname': fieldname, 'relationship_fied': self}

        collection_class = self.backref_properties.get('collection_class', None)
        if (
            collection_class
            and isinstance(collection_class, FunctionType)
            and getattr(
                collection_class, 'is_an_anyblok_instrumented_list', False
            ) is True
        ):
            InstrumentedList = collection_class(
                registry, RelationShipListMany2One, RelationShipList,
                **properties)
        else:
            InstrumentedList = type(
                'InstrumentedList', (RelationShipListMany2One, RelationShipList,
                                     registry.InstrumentedList), properties)

        self.backref_properties['collection_class'] = InstrumentedList

        cascade = self.cascade
        if self.foreign_key_options.get('ondelete') == 'cascade':
            cascade += ', delete'
        self.backref_properties['cascade'] = cascade

    def create_column(self, cname, remote_type, foreign_key, properties):

        def wrapper(cls):
            return SA_Column(
                cname.attribute_name,
                remote_type,
                nullable=self.nullable,
                unique=self.unique,
                index=self.index,
                primary_key=self.primary_key,
                info=dict(label=self.label, foreign_key=foreign_key))

        properties[(anyblok_column_prefix +
                    cname.attribute_name)] = declared_attr(wrapper)
        properties['loaded_columns'].append(cname.attribute_name)
        properties['hybrid_property_columns'].append(cname.attribute_name)

        fget = self.wrap_getter_column(cname.attribute_name)
        fset = super(Many2One, self).wrap_setter_column(cname.attribute_name)
        fexp = self.wrap_expr_column(cname.attribute_name)

        for func in (fget, fset, fexp):
            func.__name__ = cname.attribute_name

        hybrid = hybrid_property(fget)
        hybrid = hybrid.setter(fset)
        hybrid = hybrid.expression(fexp)
        properties[cname.attribute_name] = hybrid

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relationship

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        :rtype: Many2One relationship
        """
        self.kwargs['foreign_keys'] = '[%s]' % ', '.join(
            [x.get_complete_name(registry) for x in self.column_names])
        if not self.remote_model_is_a_table(registry):
            self.kwargs['viewonly'] = True  # pragma: no cover
            # we used primaryjoin and let the userto defined the good one
            # The foreign key does not exist, we should fine a good way to
            # the the local and remote columns

        return super(Many2One, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)

    def apply_value_to(self, model_self, model_field, remote_self,
                       remote_field):
        if remote_self:
            value = getattr(remote_self,
                            anyblok_column_prefix + remote_field)
        else:
            value = None

        setattr(model_self, anyblok_column_prefix + model_field, value)

    def wrap_setter_column(self, fieldname):
        attr_name = anyblok_column_prefix + fieldname

        def setter_column(model_self, value):
            res = setattr(model_self, attr_name, value)
            for model_field, rfield in self.link_between_columns:
                self.apply_value_to(model_self, model_field, value, rfield)

            return res

        return setter_column


class InstrumentedAttribute_O2O(attributes.InstrumentedAttribute):

    def __init__(self, *args, **kwargs):
        self.relationship_field = kwargs.pop('relationship_field')
        super(InstrumentedAttribute_O2O, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        call_super = False
        if value:
            for cname, fname in self.relationship_field.link_between_columns:
                if instance:
                    if getattr(instance, fname):
                        setattr(value, cname, getattr(instance, fname))
                    else:
                        call_super = True  # pragma: no cover
                else:
                    setattr(value, cname, instance)  # pragma: no cover

        else:
            call_super = True  # pragma: no cover

        if call_super:  # pragma: no cover
            super(InstrumentedAttribute_O2O, self).__set__(instance, value)


class One2One(Many2One):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = One2One(label="The relationship",
                                   model=Model.RemoteModel,
                                   remote_columns="The remote column",
                                   column_names="The column which have the "
                                               "foreigh key",
                                   nullable=False,
                                   backref="themodels")

    If the remote_columns are not define then, the system take the primary key
    of the remote model

    If the column doesn't exist, then the column will be create. Use the
    nullable option.
    If the name is not filled then the name is "'remote table'_'remote colum'"

    :param model: the remote model
    :param remote_columns: the column name on the remote model
    :param column_names: the column on the model which have the foreign key
    :param nullable: If the column_names is nullable
    :param backref: create the one2one link with this one2one
    """

    InstrumentedAttribute = InstrumentedAttribute_O2O

    def __init__(self, **kwargs):
        super(One2One, self).__init__(**kwargs)

        if 'backref' not in kwargs:
            raise FieldException("backref is a required argument")

        if 'one2many' in kwargs:
            raise FieldException("Unknow argmument 'one2many'")

        self.kwargs['info']['remote_name'] = self.kwargs['backref']

    def define_backref_properties(self, registry, namespace, properties):
        """ Add option uselist = False

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param propertie: the properties known
        """
        self.backref_properties.update({'uselist': False})

    def apply_instrumentedlist(self, registry, namespace, fieldname):
        """ Add the InstrumentedList class to replace List class as result
        of the query

        :param registry: current registry
        """

    def get_relationship_cls(self):
        self.kwargs['relationship_field'] = self
        return RelationshipProperty


class Many2Many(RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = Many2Many(label="The relationship",
                                     model=Model.RemoteModel,
                                     join_table="many2many table",
                                     remote_columns="The remote column",
                                     m2m_remote_columns="Name in many2many"
                                     local_columns="local primary key"
                                     m2m_local_columns="Name in many2many"
                                     many2many="themodels")

    if the join_table is not defined, then the table join is
        "join_'local table'_and_'remote table'"

    .. warning::

        The join_table must be filled when the declaration of the
        Many2Many is done in a Mixin

    If the remote_columns are not define then, the system take the primary key
    of the remote model

    if the local_columns are not define the take the primary key of the local
        model

    :param model: the remote model
    :param join_table: the many2many table to join local and remote models
    :param join_model: rich many2many where the join table come from a Model
    :param remote_columns: the column name on the remote model
    :param m2m_remote_columns: the column name to remote model in m2m table
    :param local_columns: the column on the model
    :param m2m_local_columns: the column name to local model in m2m table
    :param many2many: create the opposite many2many on the remote model
    """

    def __init__(self, **kwargs):
        super(Many2Many, self).__init__(**kwargs)

        self.join_table = self.kwargs.pop('join_table', None)
        self.join_model = self.kwargs.pop('join_model', None)
        if self.join_model:
            self.join_model = ModelAdapter(self.join_model)

        self.remote_columns = self.kwargs.pop('remote_columns', None)
        if self.remote_columns and not isinstance(self.remote_columns,
                                                  (list, tuple)):
            self.remote_columns = [self.remote_columns]

        self.m2m_remote_columns = self.kwargs.pop('m2m_remote_columns', None)
        if self.m2m_remote_columns and not isinstance(self.m2m_remote_columns,
                                                      (list, tuple)):
            self.m2m_remote_columns = [self.m2m_remote_columns]

        self.local_columns = self.kwargs.pop('local_columns', None)
        if self.local_columns and not isinstance(self.local_columns,
                                                 (list, tuple)):
            self.local_columns = [self.local_columns]

        self.m2m_local_columns = self.kwargs.pop('m2m_local_columns', None)
        if self.m2m_local_columns and not isinstance(self.m2m_local_columns,
                                                     (list, tuple)):
            self.m2m_local_columns = [self.m2m_local_columns]

        self.compute_join = self.kwargs.pop('compute_join', False)
        self.kwargs['backref'] = backref = self.kwargs.pop('many2many', None)
        self.kwargs['info']['remote_name'] = backref
        if isinstance(backref, (list, tuple)):
            self.kwargs['info']['remote_name'] = backref[0]
            self.backref_properties.update(**backref[1])

        self.schema = self.kwargs.pop('schema', None)

    def autodoc_get_properties(self):
        res = super(Many2Many, self).autodoc_get_properties()
        if self.join_table:
            res['join table'] = self.join_table

        if self.join_model:
            res['join model'] = self.join_model.model_name  # pragma: no cover

        if self.schema:
            res['schema'] = self.schema

        res['remote_columns'] = self.remote_columns
        res['m2m_remote_columns'] = self.m2m_remote_columns
        res['local_columns'] = self.local_columns
        res['m2m_local_columns'] = self.m2m_local_columns
        res['compute_join'] = self.compute_join
        return res

    def get_m2m_columns(self, registry, columns, m2m_columns, modelname,
                        suffix=""):
        if m2m_columns is None:
            m2m_columns = [
                x.get_fk_name(
                    registry, with_schema=False).replace('.', '_') + suffix
                for x in columns]
        elif self.join_model:
            m2m_columns_ = []
            first_step = registry.loaded_namespaces_first_step[
                self.join_model.model_name]
            for col in m2m_columns:
                if col not in first_step:
                    m2m_columns_.append(col)  # pragma: no cover
                elif isinstance(first_step[col], (Many2One, One2One)):
                    c = first_step[col]
                    remote_columns = c.get_remote_columns(registry)
                    m2m_columns_.extend([
                        x.attribute_name
                        for x in c.get_columns_names(
                            registry,
                            self.join_model.model_name,
                            col,
                            remote_columns
                        )
                    ])
                else:
                    m2m_columns_.append(col)

            m2m_columns = m2m_columns_

        if len(columns) != len(m2m_columns):
            raise FieldException((
                "The number of the column (%r) is not the same that the "
                "number m2m column (%r)") % (
                    columns, m2m_columns
                )
            )

        cols = []
        col_names = []
        ref_cols = []
        primaryjoin = []
        for i, column in enumerate(m2m_columns):
            sqltype = columns[i].native_type(registry)
            foreignkey = columns[i].get_fk_name(registry)
            completename = columns[i].get_complete_name(registry)
            cols.append(Column(column, sqltype, primary_key=True))
            col_names.append(column)
            ref_cols.append(foreignkey)
            primaryjoin.append(
                modelname + '.' + column + ' == ' + completename)

        primaryjoin = 'and_(' + ', '.join(primaryjoin) + ')'
        return cols, ForeignKeyConstraint(col_names, ref_cols), primaryjoin

    def get_local_and_remote_columns(self, registry):
        if not self.local_columns:
            local_columns = self.local_model.primary_keys(registry)
        else:
            local_columns = [ModelAttribute(self.local_model.model_name, x)
                             for x in self.local_columns]

        if not self.remote_columns:
            remote_columns = self.model.primary_keys(registry)
        else:
            remote_columns = [ModelAttribute(self.model.model_name, x)
                              for x in self.remote_columns]

        self.kwargs['info']['local_columns'] = [x.attribute_name
                                                for x in local_columns]
        self.kwargs['info']['remote_columns'] = [x.attribute_name
                                                 for x in remote_columns]

        return local_columns, remote_columns

    def get_join_table(self, registry, namespace, fieldname):
        """Get the join table name from join_table or join_model

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :rtype: name of the join table
        :exception: FieldException
        """
        join_table = self.join_table
        join_model_table = None
        if self.join_model:
            join_model_table = self.join_model.tablename(registry)

        if join_table and '.' in join_table:
            schema, table = join_table.split('.')
            schema = format_schema(schema, namespace)
            join_table = '%s.%s' % (schema, table)

        if join_table is None and join_model_table is None:
            join_table = ('join_%s_and_%s_for_%s' % (
                self.local_model.tablename(registry, with_schema=False),
                self.model.tablename(registry, with_schema=False),
                fieldname))[:63]

        elif join_table and join_model_table and join_table != join_model_table:
            raise FieldException(
                (
                    "The join_table %r and join_model %r is both declared, "
                    "on model %r and many2many %r, "
                    "but the both table name are different and we can not "
                    "determinate which is the good table's name"
                ) % (self.join_table, self.join_model.model_name,
                     namespace, fieldname)
            )

        return join_table or join_model_table

    def has_join_table_for_schema(self, registry, namespace, properties,
                                  join_table):
        has_join_table = False
        schema = None
        tables = registry.declarativebase.metadata.tables
        if '.' in join_table:
            has_join_table = join_table in tables
        elif self.join_model:
            has_join_table = join_table in tables
        elif self.schema:
            schema = format_schema(self.schema, namespace)
            has_join_table = self.schema + '.' + join_table in tables
        elif properties.get('__db_schema__'):
            schema = properties['__db_schema__']
            has_join_table = (
                properties['__db_schema__'] + '.' + join_table in tables)
        elif join_table in tables:
            has_join_table = True

        return has_join_table, schema

    def get_back_populate_relationship(self, registry, join_table):
        remote_model = self.model.model_name
        lnfs = registry.loaded_namespaces_first_step[remote_model]
        for fieldname in lnfs:
            field = lnfs[fieldname]
            if not isinstance(field, Many2Many):
                continue

            field.local_model = self.model
            remote_join_table = field.get_join_table(
                registry, remote_model, fieldname)
            if join_table == remote_join_table:
                return fieldname

        return None

    def set_overlaps_properties(self, registry, namespace):
        if not self.join_model:
            return

        lnfs = registry.loaded_namespaces_first_step[
            self.join_model.model_name]
        fieldnames = []
        for fieldname in lnfs:
            field = lnfs[fieldname]
            if not isinstance(field, Many2One):
                continue

            if field.model.model_name not in (
                namespace, self.model.model_name
            ):
                continue  # pragma: no cover

            fieldnames.append(anyblok_column_prefix + fieldname)

        if fieldnames:
            # M2O on join model to M2M fields
            self.kwargs['overlaps'] = ','.join(fieldnames)
            self.backref_properties['overlaps'] = ','.join(fieldnames)

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relationship

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param properties: the properties known
        :rtype: Many2One relationship
        """
        self.model.check_model(registry)
        self.local_model = ModelRepr(namespace)
        local_columns, remote_columns = self.get_local_and_remote_columns(
            registry)
        join_table = self.get_join_table(registry, namespace, fieldname)
        has_join_table, schema = self.has_join_table_for_schema(
            registry, namespace, properties, join_table)
        if not has_join_table:
            modelname = ''.join(x.capitalize() for x in join_table.split('_'))
            remote_columns, remote_fk, secondaryjoin = self.get_m2m_columns(
                registry, remote_columns, self.m2m_remote_columns, modelname,
                suffix="right" if namespace == self.model.model_name else ""
            )
            local_columns, local_fk, primaryjoin = self.get_m2m_columns(
                registry, local_columns, self.m2m_local_columns, modelname,
                suffix="left" if namespace == self.model.model_name else ""
            )

            Node = Table(join_table, registry.declarativebase.metadata, *(
                local_columns + remote_columns + [local_fk, remote_fk]),
                schema=schema)

            if namespace == self.model.model_name:
                type(modelname, (registry.declarativebase,), {
                    '__table__': Node
                })
                self.kwargs['primaryjoin'] = primaryjoin
                self.kwargs['secondaryjoin'] = secondaryjoin

        elif namespace == self.model.model_name or self.compute_join:
            table = registry.declarativebase.metadata.tables[
                '%s.%s' % (schema, join_table) if schema else join_table]
            cls = get_class_by_table(registry.declarativebase, table)
            modelname = ModelRepr(cls.__registry_name__).modelname(registry)
            if (
                self.m2m_local_columns is None and
                self.m2m_remote_columns is None
            ):
                raise FieldException(  # pragma: no cover
                    "No 'm2m_local_columns' and 'm2m_remote_columns' "
                    "attribute filled for many2many "
                    "%r on model %r" % (fieldname, namespace))
            elif self.m2m_local_columns is None:
                raise FieldException(
                    "No 'm2m_local_columns' attribute filled for many2many "
                    "%r on model %r" % (fieldname, namespace))
            elif self.m2m_remote_columns is None:
                raise FieldException(
                    "No 'm2m_remote_columns' attribute filled for many2many"
                    " %r on model %r" % (fieldname, namespace))

            remote_columns, remote_fk, secondaryjoin = self.get_m2m_columns(
                registry, remote_columns, self.m2m_remote_columns,
                modelname,
                suffix="right" if namespace == self.model.model_name else ""
            )

            local_columns, local_fk, primaryjoin = self.get_m2m_columns(
                registry, local_columns, self.m2m_local_columns, modelname,
                suffix="left" if namespace == self.model.model_name else ""
            )
            self.kwargs['primaryjoin'] = primaryjoin
            self.kwargs['secondaryjoin'] = secondaryjoin

        self.set_overlaps_properties(registry, namespace)
        self.kwargs['secondary'] = (
            '%s.%s' % (schema, join_table) if schema else join_table)
        # definition of expiration
        if self.kwargs.get('backref'):
            self.init_expire_attributes(registry, namespace, fieldname)
            backref = self.kwargs['backref']
            if isinstance(backref, (tuple, list)):
                backref = backref[0]

            registry.expire_attributes[namespace][fieldname].add(
                ('x2m', fieldname, backref))
            model_name = self.model.model_name
            self.init_expire_attributes(registry, model_name, backref)
            registry.expire_attributes[model_name][backref].add(
                ('x2m', backref, fieldname))
        else:
            m2m = self.get_back_populate_relationship(registry, join_table)
            if m2m:
                self.kwargs['back_populates'] = m2m

        return super(Many2Many, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)


class InstrumentedAttribute_O2M(attributes.InstrumentedAttribute):

    def __init__(self, *args, **kwargs):
        self.relationship_field = kwargs.pop('relationship_field')
        super(InstrumentedAttribute_O2M, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        super(InstrumentedAttribute_O2M, self).__set__(instance, value)
        if instance:
            for cname, fname in self.relationship_field.link_between_columns:
                if value:
                    setattr(instance, cname, getattr(value, fname))
                else:
                    setattr(instance, cname, value)  # pragma: no cover


class One2Many(RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = One2Many(label="The relationship",
                                    model=Model.RemoteModel,
                                    remote_columns="The remote column",
                                    primaryjoin="Join condition"
                                    many2one="themodel")

    If the primaryjoin is not filled then the join condition is
        "'local table'.'local promary key' == 'remote table'.'remote colum'"

    :param model: the remote model
    :param remote_columns: the column name on the remote model
    :param primaryjoin: the join condition between the remote column
    :param many2one: create the many2one link with this one2many
    """

    InstrumentedAttribute = InstrumentedAttribute_O2M

    def __init__(self, **kwargs):
        super(One2Many, self).__init__(**kwargs)

        self.remote_columns = None
        if 'remote_columns' in kwargs:
            remote_columns = self.kwargs.pop('remote_columns')
            if not isinstance(remote_columns, (list, tuple)):
                remote_columns = [remote_columns]

            self.remote_columns = [ModelAttribute(self.model.model_name, x)
                                   for x in remote_columns]

        if 'many2one' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('many2one')
            self.kwargs['info']['remote_name'] = self.kwargs['backref']

    def autodoc_get_properties(self):
        res = super(One2Many, self).autodoc_get_properties()
        res['remote_columns'] = self.remote_columns
        return res

    def add_expire_attributes(self, registry, namespace, fieldname):
        if self.kwargs.get('backref'):
            backref = self.kwargs['backref']
            if isinstance(backref, (list, tuple)):
                backref = backref[0]

            model_name = self.model.model_name
            for rname in self.remote_columns:
                self.init_expire_attributes(
                    registry, model_name, rname.attribute_name)
                _rname = rname.attribute_name
                registry.expire_attributes[model_name][_rname].add((backref,))
                registry.expire_attributes[model_name][_rname].add(
                    (backref, fieldname))

    def format_join_from_remote_columns(self, registry, namespace, fieldname):

        self.kwargs['info']['remote_columns'] = [x.attribute_name
                                                 for x in self.remote_columns]
        self.link_between_columns = [
            (x.attribute_name, x.get_fk_mapper(registry).attribute_name)
            for x in self.remote_columns
            if x.get_fk_mapper(registry)
        ]

        if 'primaryjoin' not in self.kwargs:
            pjs_ = {}
            for cname in self.remote_columns:
                remote = cname.get_complete_remote(registry)
                complete = cname.get_complete_name(registry)
                if remote in pjs_:
                    pjs_[remote].append(complete)
                else:
                    pjs_[remote] = [complete]

            pjs = []
            for k, v in pjs_.items():
                if len(v) == 1:
                    pjs.append("%s == %s" % (k, v[0]))
                else:
                    pj = 'or_(%s)' % ', '.join("%s == %s" % (k, y) for y in v)
                    logger.warning(
                        ("The One2Many %r on %r do a jointure on two identical "
                         "primary key : %r"), fieldname, namespace, pj)
                    pjs.append(pj)

            self.kwargs['primaryjoin'] = 'and_(' + ', '.join(pjs) + ')'

    def format_join_and_remote_columns(self, registry, namespace, fieldname):
        many2ones = self.model.many2one_for(registry, namespace)
        cmodel = self.model.model_name.replace('.', '')
        model = namespace.replace('.', '')
        pjs_ = {}
        self.link_between_columns = []
        self.kwargs['info']['remote_columns'] = []
        self.kwargs['info']['local_columns'] = []
        for m2o_name, many2one in many2ones:
            remote_columns = many2one.get_remote_columns(registry)
            for x in remote_columns:
                cname = m2o_name + '_' + x.attribute_name
                self.link_between_columns.append((cname, x.attribute_name))
                self.kwargs['info']['remote_columns'].append(cname)
                complete_name = cmodel + '.' + cname
                remote_name = model + '.' + x.attribute_name
                if remote_name in pjs_:
                    pjs_[remote_name].append(complete_name)
                else:
                    pjs_[remote_name] = [complete_name]

        if 'primaryjoin' not in self.kwargs:
            pjs = []
            for k, v in pjs_.items():
                if len(v) == 1:
                    pjs.append("%s == %s" % (k, v[0]))  # pragma: no cover
                else:
                    pj = 'or_(%s)' % ', '.join("%s == %s" % (k, y) for y in v)
                    logger.warning(
                        ("The One2Many %r on %r do a jointure on two identical "
                         "primary key : %r"), fieldname, namespace, pj)
                    pjs.append(pj)

            self.kwargs['primaryjoin'] = 'and_(' + ', '.join(pjs) + ')'

    def get_back_populate_relationship(self, registry, namespace):
        remote_model = self.model.model_name
        lnfs = registry.loaded_namespaces_first_step[remote_model]
        fieldnames = []
        for fieldname in lnfs:
            field = lnfs[fieldname]
            if not isinstance(field, Many2One):
                continue

            if field.model.model_name != namespace:
                continue  # pragma: no cover

            if field.kwargs.get('backref'):
                continue  # pragma: no cover

            fieldnames.append(anyblok_column_prefix + fieldname)

        return fieldnames

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relationship

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        :rtype: Many2One relationship
        """
        self.model.check_model(registry)
        if not self.remote_columns:
            self.remote_columns = self.model.foreign_keys_for(
                registry, namespace)

        if self.remote_columns:
            self.format_join_from_remote_columns(registry, namespace, fieldname)
        else:
            self.format_join_and_remote_columns(registry, namespace, fieldname)

        self.kwargs['info']['local_columns'] = []
        for rcol in self.kwargs['info']['remote_columns']:
            col = ModelAttribute(
                self.model.model_name, rcol).get_fk_column(registry)
            if col:
                self.kwargs['info']['local_columns'].append(col)

        if not self.kwargs.get('backref'):
            m2o = self.get_back_populate_relationship(registry, namespace)
            if m2o:
                self.kwargs['overlaps'] = ','.join(m2o)

        self.add_expire_attributes(registry, namespace, fieldname)
        return super(One2Many, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)

    def define_backref_properties(self, registry, namespace, properties):
        """ Add option in the backref if both model and remote model are the
        same, it is for the One2Many on the same model

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param propertie: the properties known
        """
        if namespace == self.model.model_name:
            pks = ModelRepr(namespace).primary_keys(registry)
            self.backref_properties.update({'remote_side': [
                properties[anyblok_column_prefix + pk.attribute_name]
                for pk in pks]})

    def get_relationship_cls(self):
        self.kwargs['relationship_field'] = self
        return RelationshipProperty


def ordering_list(*args, **kwargs):
    fnct_args = args
    fnct_kwargs = kwargs

    def wrap(registry, *instrumented_list_bases, **properties):
        InstrumentedList = type(
            'InstrumentedList',
            (
                OrderingList.__mro__[0],
                *instrumented_list_bases,
                registry.InstrumentedList,
            ),
            properties
        )

        kw = _unsugar_count_from(**fnct_kwargs)
        return lambda: InstrumentedList(*fnct_args, **kw)

    wrap.is_an_anyblok_instrumented_list = True

    return wrap
