# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import anyblok
from anyblok.release import version
from anyblok.blok import BlokManager
from anyblok.config import Configuration, get_db_name
from anyblok.registry import RegistryManager, return_list
from anyblok._graphviz import ModelSchema, SQLSchema
from nose import main
import sys
from os.path import join
from os import walk
from argparse import RawDescriptionHelpFormatter
from textwrap import dedent
from sqlalchemy_utils.functions import create_database
from anyblok import (
    load_init_function_from_entry_points,
    configuration_post_load,
)

Configuration.add_application_properties(
    'createdb',
    [
        'unittest',
        'logging',
        'create_db',
        'install-bloks',
        'install-or-update-bloks',
    ],
    prog='AnyBlok create database, version %r' % version,
    description="Create a database and install bloks to populate it"
)

Configuration.add_application_properties(
    'updatedb',
    [
        'unittest',
        'logging',
        'install-bloks',
        'uninstall-bloks',
        'update-bloks',
        'install-or-update-bloks',
    ],
    prog='AnyBlok update database, version %r' % version,
    description="Update a database: install, upgrade or uninstall the bloks "
)

Configuration.add_application_properties(
    'nose', ['logging', 'unittest'],
    prog='AnyBlok nose, version %r' % version,
    description="Run fonctionnal nosetest of the installed bloks"
)

Configuration.add_application_properties(
    'interpreter', ['logging', 'interpreter'],
    prog='AnyBlok interpretor, version %r' % version,
    description="Run an interpreter on the registry",
    formatter_class=RawDescriptionHelpFormatter,
    epilog=dedent("Example\n"
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
)

Configuration.add_application_properties(
    'autodoc', ['logging', 'doc', 'schema'],
    prog='AnyBlok auto documentation, version %r' % version,
)


def anyblok_createdb():
    """Create a database and install blok from config"""
    load_init_function_from_entry_points()
    Configuration.load('createdb')
    configuration_post_load()
    BlokManager.load()
    db_name = get_db_name()

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


def anyblok_updatedb():
    """Update an existing database"""
    registry = anyblok.start('updatedb', loadwithoutmigration=True)

    installed_bloks = registry.System.Blok.list_by_state('installed')
    toupdate_bloks = registry.System.Blok.list_by_state('toupdate')
    required_install_bloks = []
    required_update_bloks = []
    for blok in (Configuration.get('install_or_update_bloks') or []):
        if blok in installed_bloks:
                required_update_bloks.append(blok)
        elif blok not in toupdate_bloks:
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


def anyblok_nose():
    """Run nose unit test for the registry
    """
    registry = anyblok.start('nose', useseparator=True, unittest=True)

    defaultTest = []
    if registry:
        installed_bloks = registry.System.Blok.list_by_state("installed")
        selected_bloks = return_list(
            Configuration.get('selected_bloks')) or installed_bloks

        unwanted_bloks = return_list(
            Configuration.get('unwanted_bloks')) or []

        defaultTest = []
        for blok in installed_bloks:
            if blok not in selected_bloks or blok in unwanted_bloks:
                continue

            startpath = BlokManager.getPath(blok)
            for root, dirs, _ in walk(startpath):
                if 'tests' in dirs:
                    defaultTest.append(join(root, 'tests'))

        registry.close()  # free the registry to force create it again

    sys.exit(main(defaultTest=defaultTest))


def anyblok_interpreter():
    """Execute a script or open an interpreter
    """
    registry = anyblok.start('interpreter')
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


def anyblok2doc():
    """Return auto documentation for the registry
    """
    registry = anyblok.start('autodoc')
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
