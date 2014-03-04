import anyblok
from anyblok.blok import BlokManager
from anyblok._argsparse import ArgsParseManager
from anyblok import release
from anyblok.registry import RegistryManager
from zope.component import getUtility
import code


def format_bloks(bloks):
    if bloks == '':
        bloks = None

    if bloks is not None:
        bloks = bloks.split(',')

    return bloks


def createdb():
    BlokManager.load('AnyBlok')
    description = '%s - %s : Create database' % ('AnyBlok', release.version)
    ArgsParseManager.load(description=description,
                          argsparse_groups=[
                              'config', 'database', 'install-bloks'],
                          parts_to_load=['AnyBlok'])
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


def updatedb():
    registry = anyblok.start(
        'Update data base', release.version,
        argsparse_groups=['config', 'database', 'install-bloks',
                          'uninstall-bloks', 'update-bloks'],
        parts_to_load=['AnyBlok'])

    install_bloks = format_bloks(ArgsParseManager.get('install_bloks'))
    uninstall_bloks = format_bloks(ArgsParseManager.get('uninstall_bloks'))
    update_bloks = format_bloks(ArgsParseManager.get('update_bloks'))
    registry.upgrade(install=install_bloks, update=update_bloks,
                     uninstall=uninstall_bloks)


def interpreter():
    registry = anyblok.start(
        'Interpreter', release.version,
        argsparse_groups=['config', 'database', 'interpreter'],
        parts_to_load=['AnyBlok'])
    python_script = ArgsParseManager.get('python_script')
    if python_script:
        with open(python_script, "r") as fh:
            exec(fh.read(), None, locals())
    else:
        code.interact(local=locals())
