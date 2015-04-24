from anyblok.blok import Blok
from anyblok.release import version


class mockblok(Blok):
    version = version

    @classmethod
    def import_declaration_module(cls):
        from . import mockfile  # noqa
        from . import mockpackage  # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        from . import mockfile
        reload(mockfile)
        from . import mockpackage
        reload(mockpackage)
        reload(mockpackage.mockfile1)
        reload(mockpackage.mockfile2)
        reload(mockpackage.submockpackage)
        reload(mockpackage.submockpackage.mockfile1)
        reload(mockpackage.submockpackage.mockfile2)
