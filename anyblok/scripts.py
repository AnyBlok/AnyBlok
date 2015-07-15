# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import anyblok
from anyblok.blok import BlokManager
from anyblok.config import Configuration
from anyblok.registry import RegistryManager
from anyblok._graphviz import ModelSchema, SQLSchema
from anyblok.common import format_bloks
from nose import main
import inspect
import sys
from os.path import join, exists


def format_configuration(configuration_groups, *confs):
    if configuration_groups is None:
        configuration_groups = []

    for conf in confs:
        if conf not in configuration_groups:
            configuration_groups.append(conf)


def createdb(description, configuration_groups):
    """ Create a database and install blok from config

    :param description: description of configuration
    :param configuration_groups: list configuration groupe to load
    """
    format_configuration(configuration_groups, 'install-bloks')
    BlokManager.load()
    Configuration.load(description=description,
                       configuration_groups=configuration_groups)
    drivername = Configuration.get('db_driver_name')
    db_name = Configuration.get('db_name')

    bdd = anyblok.BDD[drivername]
    bdd.createdb(db_name)

    registry = RegistryManager.get(db_name)
    if registry is None:
        return

    if Configuration.get('install_all_bloks'):
        bloks = registry.System.Blok.list_by_state('uninstalled')
    else:
        bloks = format_bloks(Configuration.get('install_bloks'))

    registry.upgrade(install=bloks)
    registry.commit()
    registry.close()


def updatedb(description, version, configuration_groups):
    """ Update an existing database

    :param description: description of configuration
    :param version: version of script for argparse
    :param configuration_groups: list configuration groupe to load
    """
    format_configuration(configuration_groups, 'install-bloks',
                         'uninstall-bloks', 'update-bloks')

    registry = anyblok.start(description, version,
                             configuration_groups=configuration_groups,
                             loadwithoutmigration=True)

    if Configuration.get('install_all_bloks'):
        install_bloks = registry.System.Blok.list_by_state('uninstalled')
    else:
        install_bloks = format_bloks(Configuration.get('install_bloks'))

    if Configuration.get('update_all_bloks'):
        update_bloks = registry.System.Blok.list_by_state('installed')
    else:
        update_bloks = format_bloks(Configuration.get('update_bloks'))

    uninstall_bloks = format_bloks(Configuration.get('uninstall_bloks'))
    if registry:
        registry.upgrade(install=install_bloks, update=update_bloks,
                         uninstall=uninstall_bloks)
        registry.commit()
        registry.close()


def run_exit(description, version, configuration_groups):
    """ Update an existing database

    :param description: description of configuration
    :param version: version of script for argparse
    :param configuration_groups: list configuration groupe to load
    """
    format_configuration(configuration_groups, 'unittest')
    registry = anyblok.start(description, version,
                             configuration_groups=configuration_groups,
                             useseparator=True)

    defaultTest = []
    if registry:
        installed_bloks = registry.System.Blok.list_by_state("installed")
        selected_bloks = format_bloks(Configuration.get('selected_bloks'))
        if not selected_bloks:
            selected_bloks = installed_bloks

        unwanted_bloks = format_bloks(Configuration.get('unwanted_bloks'))
        if unwanted_bloks is None:
            unwanted_bloks = []

        defaultTest = [path
                       for blok in installed_bloks
                       if blok in selected_bloks and blok not in unwanted_bloks
                       for path in [join(BlokManager.getPath(blok), 'tests')]
                       if exists(path)]

    sys.exit(main(defaultTest=defaultTest))


def interpreter(description, version, configuration_groups):
    """ Execute a script or open an interpreter

    :param description: description of configuration
    :param version: version of script for argparse
    :param configuration_groups: list configuration groupe to load
    """
    format_configuration(configuration_groups, 'interpreter')
    registry = anyblok.start(description, version,
                             configuration_groups=configuration_groups)
    if registry:
        registry.commit()
        python_script = Configuration.get('python_script')
        if python_script:
            with open(python_script, "r") as fh:
                exec(fh.read(), None, locals())
        else:
            try:
                from IPython import embed
                embed()
            except ImportError:
                import code
                code.interact(local=locals())


def cron_worker(description, version, configuration_groups):
    """ Execute a script or open an interpreter

    :param description: description of configuration
    :param version: version of script for argparse
    :param configuration_groups: list configuration groupe to load
    """
    registry = anyblok.start(description, version,
                             configuration_groups=configuration_groups)
    if registry:
        registry.commit()
        registry.System.Cron.run()


def registry2rst(description, version, configuration_groups):
    """ Execute a script or open an interpreter

    :param description: description of configuration
    :param version: version of script for argparse
    :param configuration_groups: list configuration groupe to load
    """
    format_configuration(configuration_groups, 'doc')
    registry = anyblok.start(description, version,
                             configuration_groups=configuration_groups)
    if registry:
        registry.commit()
        doc = registry.Documentation()
        doc.auto_doc()
        with open(Configuration.get('doc_output'), 'w') as fp:
            if Configuration.get('doc_format') == 'RST':
                doc.toRST(fp)


def add_tables(dot, registry, models_):
    for model, cls in registry.loaded_namespaces.items():
        if not hasattr(cls, '__tablename__'):
            continue

        if not models_:
            dot.add_table(cls.__tablename__)
        elif model in models_:
            dot.add_table(cls.__tablename__)
        else:
            dot.add_label(cls.__tablename__)


def add_columns(dot, registry, models_):
    Column = registry.System.Column
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


def sqlschema(description, version, configuration_groups):
    """ Create a Table model schema of the registry

    :param description: description of configuration
    :param version: version of script for argparse
    :param configuration_groups: list configuration groupe to load
    """
    format_configuration(configuration_groups, 'schema')
    registry = anyblok.start(description, version,
                             configuration_groups=configuration_groups)
    if registry is None:
        return

    format_ = Configuration.get('schema_format')
    name_ = Configuration.get('schema_output')
    models_ = format_bloks(Configuration.get('schema_models'))
    models_ = [] if models_ is None else models_
    dot = SQLSchema(name_, format=format_)
    # add all the class
    add_tables(dot, registry, models_)
    add_columns(dot, registry, models_)
    dot.save()
    registry.rollback()
    registry.close()


def add_models(dot, registry, models_, models_by_table):
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


def add_attributes_columns(dot, registry, model, models_by_table):
    m = dot.get_class(model)
    Column = registry.System.Column
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

    return columns


def add_attributes_relation(dot, registry, model, models_by_table):
    m = dot.get_class(model)
    RelationShip = registry.System.RelationShip
    relations = RelationShip.query('name', 'rtype', 'remote_model',
                                   'remote_name', 'remote')
    relations = relations.filter(RelationShip.model == model)
    relations = {x[0]: x[1:] for x in relations.all()}

    mappers = {
        ('Many2One', True): ("m2o", "o2m"),
        ('Many2One', False): ("m2o", None),
        ('Many2Many', True): ("m2m", "m2m"),
        ('Many2Many', False): ("m2m", None),
        ('One2Many', True): ("o2m", "m2o"),
        ('One2Many', False): ("o2m", None),
        ('One2One', True): ("o2o", "o2o"),
        ('One2One', False): ("o2o", "o2o"),
    }

    for k, v in relations.items():
        rtype, remote_model, remote_name, remote = v
        if remote:
            continue

        multiplicity, multiplicity_to = mappers[(
            rtype, True if remote_name else False)]
        m.associate(remote_model, label_from=k, label_to=remote_name,
                    multiplicity_from=multiplicity,
                    multiplicity_to=multiplicity_to)

    return relations


def add_attributes(dot, registry, models_, models_by_table):
    for model, cls in registry.loaded_namespaces.items():
        if not hasattr(cls,
                       '__tablename__') or (models_ and model not in models_):
            continue

        columns = add_attributes_columns(dot, registry, model, models_by_table)
        relations = add_attributes_relation(
            dot, registry, model, models_by_table)

        m = dot.get_class(model)
        for k, v in inspect.getmembers(cls):
            if k.startswith('__') or k in ('registry', 'metadata',
                                           'loaded_columns',
                                           '_decl_class_registry',
                                           '_sa_class_manager'):
                # all the object have the registry
                continue

            if inspect.isclass(v) and registry.registry_base in v.__bases__:
                # no display internal registry
                continue
            elif k in columns.keys() + relations.keys():
                continue
            elif type(v) is classmethod:
                m.add_method(k)
                continue

            m.add_property(k)


def modelschema(description, version, configuration_groups):
    """ Create a UML model schema of the registry

    :param description: description of configuration
    :param version: version of script for argparse
    :param configuration_groups: list configuration groupe to load
    """
    format_configuration(configuration_groups, 'schema')
    registry = anyblok.start(description, version,
                             configuration_groups=configuration_groups)
    if registry is None:
        return

    format_ = Configuration.get('schema_format')
    name_ = Configuration.get('schema_output')
    models_ = format_bloks(Configuration.get('schema_models'))
    models_ = [] if models_ is None else models_

    models_by_table = {}
    dot = ModelSchema(name_, format=format_)
    models_by_table = {}
    # add all the class
    add_models(dot, registry, models_, models_by_table)
    add_attributes(dot, registry, models_, models_by_table)
    dot.save()
    registry.rollback()
    registry.close()


def anyblok_createdb():
    from anyblok.release import version
    description = "Anyblok-%s create db" % version
    createdb(description, ['config', 'database', 'unittest', 'logging'])


def anyblok_updatedb():
    from anyblok.release import version
    updatedb("AnyBlok - update db", version,
             ['config', 'database', 'unittest', 'logging'])


def anyblok_nose():
    from anyblok.release import version
    run_exit("Nose test for AnyBlok", version,
             ['config', 'database', 'logging'])


def anyblok_interpreter():
    from anyblok.release import version
    interpreter('AnyBlok interpreter', version,
                ['config', 'database', 'interpreter', 'logging'])


def anyblok_cron_worker():
    from anyblok.release import version
    cron_worker('AnyBlok interpreter', version,
                ['config', 'database', 'logging'])


def anyblok2rst():
    from anyblok.release import version
    registry2rst('AnyBlok extract rst documentation', version,
                 ['config', 'database', 'logging'])
