from anyblok.blok import Blok


class TestBlok(Blok):
    """Test blok2"""

    version = '1.0.0'

    required = [
        'test-blok1',
    ]
