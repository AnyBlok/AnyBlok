# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import anyblok
from anyblok.release import version
from anyblok.blok import BlokManager
from anyblok.config import Configuration, get_db_name
from anyblok.registry import RegistryManager
from anyblok.common import return_list
from anyblok._graphviz import ModelSchema, SQLSchema
from argparse import RawDescriptionHelpFormatter
from textwrap import dedent
from sqlalchemy_utils.functions import create_database
import warnings
import sys
from os.path import join
from logging import getLogger
from os import walk
from anyblok import (
    load_init_function_from_entry_points,
    configuration_post_load,
)

logger = getLogger(__name__)

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
    'interpreter', ['logging', 'interpreter'],
    prog='AnyBlok interpreter, version %r' % version,
    description="Run an interpreter on the registry",
    formatter_class=RawDescriptionHelpFormatter,
    epilog=dedent("Example\n"
                  "-------\n"
                  "  $ anyblok_interpreter [anyblok arguments] \n"
                  "  $ => anyblok_registry \n"
                  "  ... <registry> \n\n"
                  "  The interpreter gives you a python console with the "
                  "registry of the selected database \n\n"
                  "Note\n"
                  "----\n"
                  "  If 'ipython' is installed, then the interpreter will be "
                  "an interactive ipython one.")
)

Configuration.add_application_properties(
    'autodoc', ['logging', 'doc', 'schema'],
    prog='AnyBlok auto documentation, version %r' % version,
)


Configuration.add_application_properties(
    'nose', ['logging', 'unittest'],
    prog='AnyBlok nose, version %r' % version,
    description="Run functional nosetest against installed bloks."
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
    anyblok_registry = RegistryManager.get(db_name)
    if anyblok_registry is None:
        return

    anyblok_registry.System.Parameter.set(
        "with-demo", Configuration.get('with_demo', False))

    if Configuration.get('install_all_bloks'):
        bloks = anyblok_registry.System.Blok.list_by_state('uninstalled')
    else:
        install_bloks = Configuration.get('install_bloks') or []
        iou_bloks = Configuration.get('install_or_update_bloks') or []
        bloks = list(set(install_bloks + iou_bloks))

    anyblok_registry.upgrade(install=bloks)
    anyblok_registry.commit()
    anyblok_registry.close()


def anyblok_updatedb():
    """Update an existing database"""
    anyblok_registry = anyblok.start('updatedb', loadwithoutmigration=True)

    installed_bloks = anyblok_registry.System.Blok.list_by_state('installed')
    toupdate_bloks = anyblok_registry.System.Blok.list_by_state('toupdate')
    required_install_bloks = []
    required_update_bloks = []
    for blok in (Configuration.get('install_or_update_bloks') or []):
        if blok in installed_bloks:
            required_update_bloks.append(blok)
        elif blok not in toupdate_bloks:
            required_install_bloks.append(blok)

    if Configuration.get('install_all_bloks'):
        install_bloks = anyblok_registry.System.Blok.list_by_state(
            'uninstalled')
    else:
        install_bloks = Configuration.get('install_bloks') or []
        install_bloks = list(set(install_bloks + required_install_bloks))

    if Configuration.get('update_all_bloks'):
        update_bloks = anyblok_registry.System.Blok.list_by_state('installed')
    else:
        update_bloks = Configuration.get('update_bloks') or []
        update_bloks = list(set(update_bloks + required_update_bloks))

    uninstall_bloks = Configuration.get('uninstall_bloks')

    if anyblok_registry:
        anyblok_registry.update_blok_list()  # case, new blok added
        anyblok_registry.upgrade(install=install_bloks, update=update_bloks,
                                 uninstall=uninstall_bloks)
        anyblok_registry.commit()
        anyblok_registry.close()


class RegistryWrapper:

    def __init__(self, anyblok_registry):
        self.anyblok_registry = anyblok_registry

    def __getattr__(self, key, **kwargs):
        logger.warning(
            'registry in local is déprécated, use anyblok_registry')
        return getattr(self.anyblok_registry, key, **kwargs)


def anyblok_interpreter():
    """Execute a script or open an interpreter
    """
    anyblok_registry = anyblok.start('interpreter')
    if anyblok_registry:
        anyblok_registry.commit()
        registry = RegistryWrapper(anyblok_registry)
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
    anyblok_registry = anyblok.start('autodoc')
    if anyblok_registry:
        anyblok_registry.commit()
        doc = anyblok_registry.Documentation()
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


def anyblok_nose():
    """Run nose unit test after giving it the registry
    """
    warnings.simplefilter('default')
    warnings.warn(
        "This script is deprecated and will be removed soon. "
        "The Nose test machinery has been removed from the framework in order "
        "to be replaced with Pytest. "
        "If you need to run your tests with nose, install the Nose package.",
        DeprecationWarning, stacklevel=2)

    try:
        from nose import main
    except ImportError:
        logger.error('"Nosetest" is not installed, try: pip install nose')

    anyblok_registry = anyblok.start('nose', useseparator=True, unittest=True)

    if anyblok_registry:
        installed_bloks = anyblok_registry.System.Blok.list_by_state(
            "installed")
        selected_bloks = return_list(
            Configuration.get('selected_bloks')) or installed_bloks

        unwanted_bloks = return_list(
            Configuration.get('unwanted_bloks')) or []
        unwanted_bloks.extend(['anyblok-core', 'anyblok-test', 'model_authz'])

        defaultTest = []
        for blok in installed_bloks:
            if blok not in selected_bloks or blok in unwanted_bloks:
                continue

            startpath = BlokManager.getPath(blok)
            for root, dirs, _ in walk(startpath):
                if 'tests' in dirs:
                    defaultTest.append(join(root, 'tests'))

        anyblok_registry.close()  # free the registry to force create it again

    sys.exit(main(defaultTest=defaultTest))
