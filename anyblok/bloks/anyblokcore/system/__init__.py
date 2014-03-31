from AnyBlok import target_registry, Model


@target_registry(Model)
class System:
    pass

from . import model  # noqa
from . import column  # noqa
from . import blok  # noqa
