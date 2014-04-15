from anyblok.blok import Blok


class AnyBlokCore(Blok):

    autoinstall = True
    priority = 0

    css = [
        'static/css/core.css',
    ]
