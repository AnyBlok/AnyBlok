from anyblok.blok import Blok


class TestBlok(Blok):

    version = '1.0.0'

    conditional = [
        'test-blok1',
        'test-blok4',
    ]
