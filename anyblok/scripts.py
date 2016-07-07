# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import anyblok
from anyblok.release import version
from anyblok.blok import BlokManager
from anyblok.config import Configuration
from anyblok.registry import RegistryManager
from anyblok._graphviz import ModelSchema, SQLSchema
from nose import main
import sys
from os.path import join, exists
from argparse import RawDescriptionHelpFormatter
from textwrap import dedent
from sqlalchemy_utils.functions import create_database
from anyblok import load_init_function_from_entry_points

Configuration.applications.update({
    'createdb': {
        'prog': 'AnyBlok create database, version %r' % version,
        'description': "Create a database and install bloks to populate it",
        'configuration_groups': ['config', 'database', 'unittest'],
    },
    'updatedb': {
        'prog': 'AnyBlok update database, version %r' % version,
        'description': ("Update a database: install, upgrade or uninstall the "
                        "bloks "),
        'configuration_groups': ['config', 'database', 'unittest'],
    },
    'nose': {
        'prog': 'AnyBlok nose, version %r' % version,
        'description': "Run fonctionnal nosetest of the installed bloks",
    },
    'interpreter': {
        'prog': 'AnyBlok interpretor, version %r' % version,
        'description': "Run an interpreter on the registry",
        'formatter_class': RawDescriptionHelpFormatter,
        'epilog': dedent("Example\n"
                         "-------\n"
                         "  $ anyblok_interpreter [anyblok arguments] \n"
                         "  $ => registry \n"
                         "  ... <registry> \n\n"
                         "  The interpretor add in the local the registry of "
                         "the selected database \n\n"
                         "Note\n"
                         "----\n"
                         "  if the ipython is in the python path, then "
                         "the interpretor will be an ipyton interpretor")
    },
    'worker': {
        'prog': 'AnyBlok cron worker, version %r' % version,
    },
})


def format_configuration(configuration_groups, *confs):
    if configuration_groups is None:
        configuration_groups = []

    for conf in confs:
        if conf not in configuration_groups:
            configuration_groups.append(conf)


def createdb(application, configuration_groups, **kwargs):
    """ Create a database and install blok from config

    :param application: name of the application
    :param configuration_groups: list configuration groupe to load
    :param \**kwargs: ArgumentParser named arguments
    """
    format_configuration(configuration_groups,
                         'create_db', 'install-bloks',
                         'install-or-update-bloks')
    load_init_function_from_entry_points()
    Configuration.load(application, configuration_groups=configuration_groups,
                       **kwargs)
    BlokManager.load()
    db_name = Configuration.get('db_name')
    db_template_name = Configuration.get('db_template_name', None)
    url = Configuration.get('get_url')(db_name=db_name)
    create_database(url, template=db_template_name)
    registry = RegistryManager.get(db_name)
    if registry is None:
        return

    if Configuration.get('install_all_bloks'):
        bloks = registry.System.Blok.list_by_state('uninstalled')
    else:
        install_bloks = Configuration.get('install_bloks') or []
        iou_bloks = Configuration.get('install_or_update_bloks') or []
        bloks = list(set(install_bloks + iou_bloks))

    registry.upgrade(install=bloks)
    registry.commit()
    registry.close()


def updatedb(application, configuration_groups, **kwargs):
    """ Update an existing database

    :param application: name of the application
    :param configuration_groups: list configuration groupe to load
    :param \**kwargs: ArgumentParser named arguments
    """
    format_configuration(configuration_groups, 'install-bloks',
                         'uninstall-bloks', 'update-bloks',
                         'install-or-update-bloks')

    registry = anyblok.start(application,
                             configuration_groups=configuration_groups,
                             loadwithoutmigration=True, **kwargs)

    installed_bloks = registry.System.Blok.list_by_state('installed')
    required_install_bloks = []
    required_update_bloks = []
    for blok in (Configuration.get('install_or_update_bloks') or []):
        if blok in installed_bloks:
                required_update_bloks.append(blok)
        else:
            required_install_bloks.append(blok)

    if Configuration.get('install_all_bloks'):
        install_bloks = registry.System.Blok.list_by_state('uninstalled')
    else:
        install_bloks = Configuration.get('install_bloks') or []
        install_bloks = list(set(install_bloks + required_install_bloks))

    if Configuration.get('update_all_bloks'):
        update_bloks = registry.System.Blok.list_by_state('installed')
    else:
        update_bloks = Configuration.get('update_bloks') or []
        update_bloks = list(set(update_bloks + required_update_bloks))

    uninstall_bloks = Configuration.get('uninstall_bloks')

    if registry:
        registry.update_blok_list()  # case, new blok added
        registry.upgrade(install=install_bloks, update=update_bloks,
                         uninstall=uninstall_bloks)
        registry.commit()
        registry.close()


def run_exit(application, configuration_groups, **kwargs):
    """Run nose unit test for the registry

    :param application: name of the application
    :param configuration_groups: list configuration groupe to load
    :param \**kwargs: ArgumentParser named arguments
    """
    format_configuration(configuration_groups, 'unittest')
    registry = anyblok.start(application,
                             configuration_groups=configuration_groups,
                             useseparator=True, unittest=True, **kwargs)

    defaultTest = []
    if registry:
        installed_bloks = registry.System.Blok.list_by_state("installed")
        selected_bloks = Configuration.get('selected_bloks')
        if not selected_bloks:
            selected_bloks = installed_bloks

        unwanted_bloks = Configuration.get('unwanted_bloks') or []

        defaultTest = [path
                       for blok in installed_bloks
                       if blok in selected_bloks and blok not in unwanted_bloks
                       for path in [join(BlokManager.getPath(blok), 'tests')]
                       if exists(path)]
        registry.close()  # free the registry to force create it again

    sys.exit(main(defaultTest=defaultTest))


def interpreter(application, configuration_groups, **kwargs):
    """Execute a script or open an interpreter

    :param application: name of the application
    :param configuration_groups: list configuration groupe to load
    :param \**kwargs: ArgumentParser named arguments
    """
    format_configuration(configuration_groups, 'interpreter')
    registry = anyblok.start(application,
                             configuration_groups=configuration_groups,
                             **kwargs)
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


def cron_worker(application, configuration_groups, **kwargs):
    """Execute a cron worker

    :param application: name of the application
    :param configuration_groups: list configuration groupe to load
    :param \**kwargs: ArgumentParser named arguments
    """
    registry = anyblok.start(application,
                             configuration_groups=configuration_groups,
                             **kwargs)
    if registry:
        registry.commit()
        registry.System.Cron.run()


def registry2doc(application, configuration_groups, **kwargs):
    """Return auto documentation for the registry

    :param application: name of the application
    :param configuration_groups: list configuration groupe to load
    :param \**kwargs: ArgumentParser named arguments
    """
    format_configuration(configuration_groups, 'doc', 'schema')
    registry = anyblok.start(application,
                             configuration_groups=configuration_groups,
                             **kwargs)
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
    createdb('createdb', ['logging'])


def anyblok_updatedb():
    updatedb('updatedb', ['logging'])


def anyblok_nose():
    run_exit("nose", ['logging'])


def anyblok_interpreter():
    interpreter('interpreter', ['logging'])


def anyblok_cron_worker():
    cron_worker('worker', ['logging'])


def anyblok2doc():
    registry2doc('autodoc', ['logging'])
