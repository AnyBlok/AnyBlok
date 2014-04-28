import anyblok
from anyblok.blok import BlokManager
from anyblok._argsparse import ArgsParseManager
from anyblok.registry import RegistryManager
from zope.component import getUtility
import code


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

    adapter = getUtility(anyblok.AnyBlok.Interface.ISqlAlchemyDataBase,
                         drivername)
    if adapter:
        adapter.createdb(dbname)

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


def interpreter(description, version, argsparse_groups, parts_to_load):
    """ Execute a script of give an interpreter

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
