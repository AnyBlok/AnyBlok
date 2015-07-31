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
    Configuration.load(description=description,
                       configuration_groups=configuration_groups)
    BlokManager.load()
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
    """Run nose unit test for the registry

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
    """Execute a script or open an interpreter

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
    """Execute a cron worker

    :param description: description of configuration
    :param version: version of script for argparse
    :param configuration_groups: list configuration groupe to load
    """
    registry = anyblok.start(description, version,
                             configuration_groups=configuration_groups)
    if registry:
        registry.commit()
        registry.System.Cron.run()


def registry2doc(description, version, configuration_groups):
    """Return auto documentation for the registry

    :param description: description of configuration
    :param version: version of script for argparse
    :param configuration_groups: list configuration groupe to load
    """
    format_configuration(configuration_groups, 'doc', 'schema')
    registry = anyblok.start(description, version,
                             configuration_groups=configuration_groups)
    if registry:
        registry.commit()
        doc = registry.Documentation()
        doc.auto_doc()
        if Configuration.get('doc_format') == 'RST':
            with open(Configuration.get('doc_output'), 'w') as fp:
                doc.toRST(fp)
        elif Configuration.get('doc_format') == 'UML':
            format_ = Configuration.get('schema_format')
            name_ = Configuration.get('schema_output')
            dot = ModelSchema(name_, format=format_)
            doc.toUML(dot)
            dot.save()
        elif Configuration.get('doc_format') == 'SQL':
            format_ = Configuration.get('schema_format')
            name_ = Configuration.get('schema_output')
            dot = SQLSchema(name_, format=format_)
            doc.toSQL(dot)
            dot.save()


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


def anyblok2doc():
    from anyblok.release import version
    registry2doc('AnyBlok extract rst documentation', version,
                 ['config', 'database', 'logging'])
