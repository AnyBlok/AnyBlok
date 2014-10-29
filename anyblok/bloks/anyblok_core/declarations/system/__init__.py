from anyblok import Declarations


@Declarations.target_registry(Declarations.Model)
class System:
    pass

from . import model  # noqa
from . import field  # noqa
from . import column  # noqa
from . import relationship  # noqa
from . import blok  # noqa
from . import cache  # noqa
