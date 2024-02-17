# this file is a part of the anyblok project
#
#    copyright (c) 2024 jean-sebastien suzanne <js.suzanne@gmail.com>
#
# this source code form is subject to the terms of the mozilla public license,
# v. 2.0. if a copy of the mpl was not distributed with this file,you can
# obtain one at http://mozilla.org/mpl/2.0/.
try:
    from pkg_resources import iter_entry_points
except ImportError:
    from importlib.metadata import entry_points

    def iter_entry_points(group):
        return entry_points(group=group)
