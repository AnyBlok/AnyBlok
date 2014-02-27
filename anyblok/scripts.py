import anyblok
from anyblok.blok import BlokManager
from anyblok._argsparse import ArgsParseManager
from anyblok import release
from anyblok.registry import RegistryManager
from zope.component import getUtility
import code


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
    bloks = ArgsParseManager.get('install_bloks')
    if bloks == '':
        bloks = None

    if bloks is not None:
        bloks = bloks.split(',')

    adapter = getUtility(anyblok.AnyBlok.Interface.ISqlAlchemyDataBase,
                         drivername)
    if adapter:
        adapter.createdb(dbname)

    registry = RegistryManager.get(dbname)
    registry.update_blok(install_bloks=bloks)
    registry.commit()
    registry.close()


def interpreter():
    registry = anyblok.start(
        'Interpreter', release.version,
        argsparse_groups=['config', 'database', 'interpreter'],
        parts_to_load=['AnyBlok'])
    python_script = ArgsParseManager.get('python_script')
    if python_script:
        execfile(python_script)
    else:
        code.interact(local=locals())
