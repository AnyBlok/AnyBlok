# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.schema import ForeignKey
from anyblok.common import anyblok_column_prefix
from .config import Configuration


def get_for(basekey, path, default=None):
    key = '%s.%s' % (basekey, '.'.join(path))
    key = key.lower()

    if path in (['Model', '*'], ['Mixin', '*']):
        return Configuration.get(key, default)

    res = Configuration.get(key, None)
    if res is not None:
        return res  # pragma: no cover

    new_path = path[:-1]
    if path[-1] == '*':
        new_path[-1] = '*'
    else:
        new_path.append('*')

    return get_for(basekey, new_path, default=default)


def get_schema_for(path, default=None):
    return get_for('db_schema', path, default=default)


def get_schema_prefix_for(path, default=None):
    return get_for('prefix_db_schema', path, default=default)


def get_schema_suffix_for(path, default=None):
    return get_for('suffix_db_schema', path, default=default)


def format_schema(schema, registry_name):
    path = registry_name.split('.')
    schema = get_schema_for(path, default=schema)
    if schema is not None:
        prefix = get_schema_prefix_for(path, default='')
        suffix = get_schema_suffix_for(path, default='')

        return prefix + schema + suffix

    return schema


class ModelReprException(Exception):
    """Exception for Model attribute"""


class ModelAttributeException(Exception):
    """Exception for Model attribute"""


class ModelAttributeAdapterException(Exception):
    """Exception for Model attribute adapter"""


class MapperException(AttributeError):
    """ Simple Exception for Mapper """


class FakeColumn:
    db_column_name = None

    def update_description(self, registry, model, res):
        pass


class FakeRelationShip:

    def __init__(self, mapper):
        self.mapper = mapper

    def update_description(self, registry, model, res):
        pass


class ModelAttribute:
    """The Model attribute represente the using of a declared attribute, in the
    goal of get the real attribute after of the foreign_key::

        ma = ModelAttribute('registry name', 'attribute name')

    """

    def __repr__(self):
        return "%s => %s" % (self.model_name, self.attribute_name)

    def __str__(self):
        return "%s => %s" % (self.model_name, self.attribute_name)

    def __init__(self, model_name, attribute_name):
        if not model_name or not attribute_name:
            raise ModelAttributeException(
                "model_name (%s) and attribute_name (%s) are "
                "required" % (model_name, attribute_name))

        self.model_name = model_name
        self.attribute_name = attribute_name
        self._options = {}

    def get_attribute(self, registry, usehybrid=True):
        """Return the assembled attribute, the model need to be assembled

        :param registry: instance of the registry
        :param usehybrid: if True return the hybrid property if exist
        :rtype: instance of the attribute
        :exceptions: ModelAttributeException
        """
        if self.model_name not in registry.loaded_namespaces:
            raise ModelAttributeException(
                "Unknow model %r, maybe the model doesn't exist or is not"
                "assembled yet" % self.model_name)

        Model = registry.get(self.model_name)
        if not hasattr(Model, self.attribute_name):
            raise ModelAttributeException(
                "Model %r has not get %r attribute" % (
                    self.model_name, self.attribute_name))

        attribute_name = self.attribute_name
        if not usehybrid:
            if attribute_name in Model.hybrid_property_columns:
                attribute_name = anyblok_column_prefix + attribute_name

        return getattr(Model, attribute_name)

    def get_type(self, registry):
        """Return the foreign key which represent the attribute in the data
        base

        :param registry: instance of the sqlalchemy ForeignKey
        :rtype: instance of the attribute
        """
        Model = self.check_model_in_first_step(registry)
        column_name = self.check_column_in_first_step(registry, Model)
        col = registry.loaded_namespaces_first_step[self.model_name][
            column_name]
        return col

    def get_fk_column(self, registry):
        """Return the foreign key which represent the attribute in the data
        base

        :param registry: instance of the sqlalchemy ForeignKey
        :rtype: instance of the attribute
        """
        mapper = self.get_fk_mapper(registry)
        if mapper:
            return mapper.attribute_name

        return None

    def get_fk_mapper(self, registry):
        """Return the foreign key which represent the attribute in the data
        base

        :param registry: instance of the sqlalchemy ForeignKey
        :rtype: instance of the attribute
        """
        Model = self.check_model_in_first_step(registry)
        try:
            column_name = self.check_column_in_first_step(registry, Model)
            if Model[column_name].foreign_key:
                return Model[column_name].foreign_key
        except ModelAttributeException:
            pass

        return None

    def get_fk(self, registry):
        """Return the foreign key which represent the attribute in the data
        base

        :param registry: instance of the sqlalchemy ForeignKey
        :rtype: instance of the attribute
        """
        return ForeignKey(self.get_fk_name(registry), **self._options)

    def options(self, **kwargs):
        """Add foreign key options to create the sqlalchemy ForeignKey

        :param **kwargs: options
        :rtype: the instance of the ModelAttribute
        """
        self._options.update(kwargs)
        return self

    def get_fk_name(self, registry, with_schema=True):
        """Return the name of the foreign key

        the need of foreign key may be before the creation of the model in
        the registry, so we must use the first step of assembling

        :param registry: instance of the registry
        :rtype: str of the foreign key (tablename.columnname)
        :exceptions: ModelAttributeException
        """
        Model = self.check_model_in_first_step(registry)
        column_name = self.check_column_in_first_step(registry, Model)
        tablename = Model['__tablename__']
        if Model[self.attribute_name].db_column_name:
            column_name = Model[self.attribute_name].db_column_name

        if with_schema and Model.get('__db_schema__'):
            return '%s.%s.%s' % (
                Model['__db_schema__'], tablename, column_name)

        return tablename + '.' + column_name

    def get_complete_name(self, registry):
        """Return the name of the foreign key

        the need of foreign key may be before the creation of the model in
        the registry, so we must use the first step of assembling

        :param registry: instance of the registry
        :rtype: str of the foreign key (modelname.columnname)
        :exceptions: ModelAttributeException
        """
        Model = self.check_model_in_first_step(registry)
        column_name = self.check_column_in_first_step(registry, Model)
        modelname = self.model_name.replace('.', '')
        return modelname + '.' + column_name

    def get_fk_remote(self, registry):
        Model = self.check_model_in_first_step(registry)
        column_name = self.check_column_in_first_step(registry, Model)
        remote = Model[column_name].foreign_key
        if not remote:
            return None

        return remote.get_fk_name(registry)

    def get_complete_remote(self, registry):
        Model = self.check_model_in_first_step(registry)
        column_name = self.check_column_in_first_step(registry, Model)
        remote = Model[column_name].foreign_key
        if not remote:
            return None

        return remote.get_complete_name(registry)

    def add_fake_column(self, registry):
        Model = self.check_model_in_first_step(registry)
        if self.attribute_name in Model:
            return

        Model[self.attribute_name] = FakeColumn()

    def add_fake_relationship(self, registry, namespace, fieldname):
        Model = self.check_model_in_first_step(registry)
        if self.attribute_name in Model:
            return

        Model[self.attribute_name] = FakeRelationShip(ModelAttribute(
            namespace, fieldname))

    def get_column_name(self, registry):
        """Return the name of the column

        the need of foreign key may be before the creation of the model in
        the registry, so we must use the first step of assembling

        :param registry: instance of the registry
        :rtype: str of the foreign key (tablename.columnname)
        :exceptions: ModelAttributeException
        """
        Model = self.check_model_in_first_step(registry)
        column_name = self.check_column_in_first_step(registry, Model)
        if hasattr(Model[self.attribute_name], 'db_column_name'):
            if Model[self.attribute_name].db_column_name:
                column_name = Model[self.attribute_name].db_column_name

        return column_name

    def check_model_in_first_step(self, registry):
        if self.model_name not in registry.loaded_namespaces_first_step:
            raise ModelAttributeException(
                "Unknow model %r" % self.model_name)

        Model = registry.loaded_namespaces_first_step[self.model_name]
        if len(Model.keys()) == 3:
            # (__depends__, __db_schema__, __tablename__)
            # No column found, so is not an sql model
            raise ModelAttributeException(
                "The Model %r is not an SQL Model" % self.model_name)
        return Model

    def check_column_in_first_step(self, registry, Model):
        if self.attribute_name not in Model:
            raise ModelAttributeException(
                "the Model %r has not got attribute %r" % (
                    self.model_name, self.attribute_name))

        return self.attribute_name

    def is_declared(self, registry):
        Model = self.check_model_in_first_step(registry)
        if self.attribute_name not in Model:
            return False

        return True

    def native_type(self, registry):
        Model = self.check_model_in_first_step(registry)
        column_name = self.check_column_in_first_step(registry, Model)
        return Model[column_name].native_type(registry)


class ModelRepr:
    """Pseudo class to represent a model
    ::

        mr = ModelRepr('registry name')
    """
    def __init__(self, model_name):
        if not model_name:
            raise ModelReprException(
                "model_name (%s) is required" % model_name)

        self.model_name = model_name

    def __str__(self):
        return self.model_name

    def check_model(self, registry):
        """Check if the model exist else raise an exception

        :param registry: instance of the registry
        :rtype: dict which represent the first step of the model
        :exceptions: ModelReprException
        """
        if self.model_name not in registry.loaded_namespaces_first_step:
            raise ModelReprException("Model %r unexisting" % self.model_name)

        return registry.loaded_namespaces_first_step[self.model_name]

    def tablename(self, registry, with_schema=True):
        """Return the  real tablename of the Model

        :param registry: instance of the registry
        :rtype: string
        """
        Model = self.check_model(registry)
        if with_schema and Model.get('__db_schema__'):
            return Model['__db_schema__'] + '.' + Model['__tablename__']

        return Model['__tablename__']

    def modelname(self, registry):
        """Return the  real tablename of the Model

        :param registry: instance of the registry
        :rtype: string
        """
        self.check_model(registry)
        return self.model_name.replace('.', '')

    def primary_keys(self, registry):
        """Return the  of the primary keys

        :param registry: instance of the registry
        :rtype: list of ModelAttribute
        """
        from anyblok.column import Column
        Model = self.check_model(registry)
        pks = []
        for k, v in Model.items():
            if isinstance(v, Column):
                if v.kwargs.get('primary_key') is True:
                    pks.append(ModelAttribute(self.model_name, k))

        return pks

    def foreign_keys_for(self, registry, remote_model):
        """Return the  of the primary keys

        :param registry: instance of the registry
        :rtype: list of ModelAttribute
        """
        from anyblok.column import Column
        Model = self.check_model(registry)
        fks = []
        for k, v in Model.items():
            if isinstance(v, Column):
                if v.foreign_key:
                    if v.foreign_key.model_name == remote_model:
                        fks.append(ModelAttribute(self.model_name, k))

        return fks

    def many2one_for(self, registry, remote_model):
        """Return the many2one links to the remote_model

        :param registry: instance of the registry
        :rtype: list of many2one field
        """
        from anyblok.relationship import Many2One
        Model = self.check_model(registry)
        many2ones = []
        for k, v in Model.items():
            if isinstance(v, Many2One):
                if v.model.model_name == remote_model:
                    many2ones.append((k, v))

        return many2ones


def ModelAttributeAdapter(Model):
    """ Return a ModelAttribute

    :param Model: ModelAttribute or string ('registry name'=>'attribute name')
    :rtype: instance of ModelAttribute
    :exceptions: ModelAttributeAdapterException
    """
    if isinstance(Model, str):
        if '=>' not in Model:
            raise ModelAttributeAdapterException(
                "Wrong value %r impossible to find model and attribtue" % (
                    Model))
        model, attribute = Model.split('=>')
        return ModelAttribute(model, attribute)
    else:
        return Model


def ModelAdapter(Model):
    """ Return a ModelRepr

    :param Model: ModelRepr or string
    :rtype: instance of ModelRepr
    :exceptions: ModelAdapterException
    """
    if isinstance(Model, str):
        return ModelRepr(Model)
    elif isinstance(Model, ModelRepr):
        return Model
    else:
        return ModelRepr(Model.__registry_name__)


class ModelMapper:

    sqlalchemy_known_events = [
        'after_delete', 'after_insert', 'after_update', 'append_result',
        'before_delete', 'before_insert', 'before_update', 'create_instance',
        'expire', 'first_init', 'init', 'load', 'refresh',
    ]

    def __init__(self, mapper, event, *args, **kwargs):
        if isinstance(mapper, str):
            self.model = ModelRepr(mapper)
        elif isinstance(mapper, ModelRepr):
            self.model = mapper
        elif hasattr(mapper, '__registry_name__'):
            self.model = ModelRepr(mapper.__registry_name__)

        self.event = event
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def capable(cls, mapper):
        if isinstance(mapper, str):
            return True
        elif isinstance(mapper, ModelRepr):
            return True
        elif hasattr(mapper, '__registry_name__'):
            return True

        return False

    def listen(self, method):
        if self.event in self.sqlalchemy_known_events:
            method.is_an_sqlalchemy_event_listener = True
            method.sqlalchemy_listener = self
        else:
            method.is_an_event_listener = True
            method.model = self.model.model_name
            method.event = self.event

    def mapper(self, registry, namespace, **kwargs):
        model = self.model
        if self.model.model_name.upper() == 'SELF':
            model = ModelRepr(namespace)

        model.check_model(registry)
        return registry.get(model.model_name)


class ModelAttributeMapper:

    def __init__(self, mapper, event, *args, **kwargs):
        if isinstance(mapper, str):
            self.attribute = ModelAttribute(*mapper.split('=>'))
        elif isinstance(mapper, ModelAttribute):
            self.attribute = mapper

        self.event = event
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def capable(cls, mapper):
        if isinstance(mapper, str):
            if '=>' in mapper:
                model, column = mapper.split('=>')
                if model and column:
                    return True
        elif isinstance(mapper, ModelAttribute):
            return True

        return False

    def listen(self, method):
        method.is_an_sqlalchemy_event_listener = True
        method.sqlalchemy_listener = self

    def mapper(self, registry, namespace, usehybrid=True):
        attribute = self.attribute
        if self.attribute.model_name.upper() == 'SELF':
            attribute = ModelAttribute(  # pragma: no cover
                namespace, self.attribute.attribute_name)

        return attribute.get_attribute(registry, usehybrid=usehybrid)


def MapperAdapter(mapper, *args, **kwargs):
    if ModelAttributeMapper.capable(mapper):
        return ModelAttributeMapper(mapper, *args, **kwargs)
    elif ModelMapper.capable(mapper):
        return ModelMapper(mapper, *args, **kwargs)
    else:
        raise MapperException("Unknow mapper type %r")
