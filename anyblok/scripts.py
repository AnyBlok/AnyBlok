# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import anyblok
from anyblok.blok import BlokManager
from anyblok._argsparse import ArgsParseManager
from anyblok.registry import RegistryManager
from anyblok._graphviz import ModelSchema, SQLSchema
import code
import inspect


def format_bloks(bloks):
    if bloks == '':
        bloks = None

    if bloks is not None:
        bloks = bloks.split(',')

    return bloks


def format_argsparse(argsparse_groups, *confs):
    if argsparse_groups is None:
        argsparse_groups = []

    for conf in confs:
        if conf not in argsparse_groups:
            argsparse_groups.append(conf)


def createdb(description, argsparse_groups, parts_to_load):
    """ Create a database and install blok from config

    :param description: description of argsparse
    :param argsparse_groups: list argsparse groupe to load
    :param parts_to_load: group of blok to load
    """
    BlokManager.load(*parts_to_load)
    ArgsParseManager.load(description=description,
                          argsparse_groups=argsparse_groups,
                          parts_to_load=parts_to_load)
    ArgsParseManager.init_logger()
    drivername = ArgsParseManager.get('dbdrivername')
    dbname = ArgsParseManager.get('dbname')
    bloks = format_bloks(ArgsParseManager.get('install_bloks'))

    bdd = anyblok.BDD[drivername]
    bdd.createdb(dbname)

    registry = RegistryManager.get(dbname)
    registry.upgrade(install=bloks)
    registry.commit()
    registry.close()


def updatedb(description, version, argsparse_groups, parts_to_load):
    """ Update an existing database

    :param description: description of argsparse
    :param version: version of script for argparse
    :param argsparse_groups: list argsparse groupe to load
    :param parts_to_load: group of blok to load
    """
    format_argsparse(argsparse_groups, 'install-bloks', 'uninstall-bloks',
                     'update-bloks')

    registry = anyblok.start(description, version,
                             argsparse_groups=argsparse_groups,
                             parts_to_load=parts_to_load)

    install_bloks = format_bloks(ArgsParseManager.get('install_bloks'))
    uninstall_bloks = format_bloks(ArgsParseManager.get('uninstall_bloks'))
    update_bloks = format_bloks(ArgsParseManager.get('update_bloks'))
    registry.upgrade(install=install_bloks, update=update_bloks,
                     uninstall=uninstall_bloks)
    registry.commit()
    registry.close()


def interpreter(description, version, argsparse_groups, parts_to_load):
    """ Execute a script or open an interpreter

    :param description: description of argsparse
    :param version: version of script for argparse
    :param argsparse_groups: list argsparse groupe to load
    :param parts_to_load: group of blok to load
    """
    format_argsparse(argsparse_groups, 'interpreter')
    registry = anyblok.start(description, version,
                             argsparse_groups=argsparse_groups,
                             parts_to_load=parts_to_load)
    python_script = ArgsParseManager.get('python_script')
    if python_script:
        with open(python_script, "r") as fh:
            exec(fh.read(), None, locals())
    else:
        code.interact(local=locals())


def sqlschema(description, version, argsparse_groups, parts_to_load):
    """ Create a Table model schema of the registry

    :param description: description of argsparse
    :param version: version of script for argparse
    :param argsparse_groups: list argsparse groupe to load
    :param parts_to_load: group of blok to load
    """
    format_argsparse(argsparse_groups, 'schema')
    registry = anyblok.start(description, version,
                             argsparse_groups=argsparse_groups,
                             parts_to_load=parts_to_load)
    if registry is None:
        return

    format_ = ArgsParseManager.get('schema_format')
    name_ = ArgsParseManager.get('schema_output')
    models_ = format_bloks(ArgsParseManager.get('schema_model'))
    models_ = [] if models_ is None else models_

    Column = registry.System.Column

    dot = SQLSchema(name_, format=format_)

    # add all the class
    for model, cls in registry.loaded_namespaces.items():
        if not hasattr(cls, '__tablename__'):
            continue

        if not models_:
            dot.add_table(cls.__tablename__)
        elif model in models_:
            dot.add_table(cls.__tablename__)
        else:
            dot.add_label(cls.__tablename__)

    for model, cls in registry.loaded_namespaces.items():
        if models_ and model not in models_:
            continue

        if not hasattr(cls, '__tablename__'):
            continue

        t = dot.get_table(cls.__tablename__)
        columns = Column.query('name', 'ctype', 'foreign_key', 'primary_key',
                               'nullable')
        columns = columns.filter(Column.model == model)
        columns = columns.order_by(Column.primary_key.desc())
        columns = {x[0]: x[1:] for x in columns.all()}

        for k, v in columns.items():
            ctype, foreign_key, primary_key, nullable = v
            if foreign_key:
                t2 = dot.get_table(foreign_key.split('.')[0])
                t.add_foreign_key(t2, label=k, nullable=nullable)
            else:
                t.add_column(k, ctype, primary_key=primary_key)

    dot.save()
    registry.rollback()
    registry.close()


def modelschema(description, version, argsparse_groups, parts_to_load):
    """ Create a UML model schema of the registry

    :param description: description of argsparse
    :param version: version of script for argparse
    :param argsparse_groups: list argsparse groupe to load
    :param parts_to_load: group of blok to load
    """
    format_argsparse(argsparse_groups, 'schema')
    registry = anyblok.start(description, version,
                             argsparse_groups=argsparse_groups,
                             parts_to_load=parts_to_load)
    if registry is None:
        return

    format_ = ArgsParseManager.get('schema_format')
    name_ = ArgsParseManager.get('schema_output')
    models_ = format_bloks(ArgsParseManager.get('schema_model'))
    models_ = [] if models_ is None else models_

    models_by_table = {}
    Column = registry.System.Column
    RelationShip = registry.System.RelationShip

    dot = ModelSchema(name_, format=format_)

    # add all the class
    for model, cls in registry.loaded_namespaces.items():
        if not hasattr(cls, '__tablename__'):
            continue

        if not models_:
            dot.add_class(model)
        elif model in models_:
            dot.add_class(model)
        else:
            dot.add_label(model)
        models_by_table[cls.__tablename__] = model

    for model, cls in registry.loaded_namespaces.items():
        if not hasattr(cls, '__tablename__'):
            continue

        if models_ and model not in models_:
            continue

        m = dot.get_class(model)

        columns = Column.query('name', 'ctype', 'foreign_key', 'primary_key',
                               'nullable')
        columns = columns.filter(Column.model == model)
        columns = columns.order_by(Column.primary_key.desc())
        columns = {x[0]: x[1:] for x in columns.all()}

        for k, v in columns.items():
            ctype, foreign_key, primary_key, nullable = v
            if foreign_key:
                multiplicity = "1"
                if nullable:
                    multiplicity = '0..1'
                m2 = models_by_table.get(foreign_key.split('.')[0])
                if m2:
                    m.agregate(m2, label_from=k,
                               multiplicity_from=multiplicity)
            elif primary_key:
                m.add_column('+PK+ %s (%s)' % (k, ctype))
            else:
                m.add_column('%s (%s)' % (k, ctype))

        relations = RelationShip.query('name', 'rtype', 'remote_model',
                                       'remote_name', 'remote')
        relations = relations.filter(RelationShip.model == model)
        relations = {x[0]: x[1:] for x in relations.all()}

        for k, v in relations.items():
            rtype, remote_model, remote_name, remote = v
            if remote:
                continue

            multiplicity_to = None
            if rtype == 'Many2One':
                multiplicity = "m2o"
                if remote_name:
                    multiplicity_to = 'o2m'
            elif rtype == 'Many2Many':
                multiplicity = "m2m"
                if remote_name:
                    multiplicity_to = 'm2m'
            elif rtype == 'One2Many':
                multiplicity = "o2m"
                if remote_name:
                    multiplicity_to = 'm2o'
            elif rtype == 'One2One':
                multiplicity = "o2o"
                multiplicity_to = 'o2o'

            m.associate(remote_model, label_from=k, label_to=remote_name,
                        multiplicity_from=multiplicity,
                        multiplicity_to=multiplicity_to)

        for k, v in inspect.getmembers(cls):
            if k.startswith('__'):
                continue

            if k in ('registry', 'metadata', 'loaded_columns',
                     '_decl_class_registry', '_sa_class_manager'):
                # all the object have the registry
                continue

            if inspect.isclass(v):
                if registry.registry_base in v.__bases__:
                    # no display internal registry
                    continue
            elif k in columns.keys():
                continue
            elif k in relations.keys():
                continue
            elif type(v) is classmethod:
                m.add_method(k)
                continue

            m.add_property(k)

    dot.save()
    registry.rollback()
    registry.close()
