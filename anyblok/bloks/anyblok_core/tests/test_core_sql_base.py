from anyblok.tests.testcase import BlokTestCase


class TestCoreSqlBase(BlokTestCase):

    def test_insert(self):
        Blok = self.registry.System.Blok
        Blok.insert(name='OneBlok', state='undefined')
        blok = Blok.query().filter(Blok.name == 'OneBlok').first()
        self.assertEqual(blok.state, 'undefined')

    def test_multi_insert(self):
        Blok = self.registry.System.Blok
        Blok.multi_insert(dict(name='OneBlok', state='undefined'),
                          dict(name='TwoBlok', state='undefined'),
                          dict(name='ThreeBlok', state='undefined'))
        states = Blok.query('state').filter(Blok.name.in_(['OneBlok',
                                                           'TwoBlok',
                                                           'ThreeBlok'])).all()
        states = [x[0] for x in states]
        self.assertEqual(states, ['undefined', 'undefined', 'undefined'])
