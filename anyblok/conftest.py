# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Denis VIVIÈS <dvivies@geoblink.com>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.

from logging import getLogger

import pytest
import sqlalchemy
from sqlalchemy import event

from anyblok.config import Configuration
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
from anyblok.testing import load_configuration

logger = getLogger(__name__)


@pytest.fixture(scope='session')
def configuration_loaded(request):
    load_configuration()


@pytest.fixture(scope='session')
def init_session(request, configuration_loaded):
    # Init registry
    additional_setting = {'unittest': True}

    if len(BlokManager.list()) == 0:
        BlokManager.load()
    registry = RegistryManager.get(Configuration.get('db_name'),
                                   **additional_setting)
    registry.commit()
    # Add savepoint
    registry.begin_nested()

    @event.listens_for(registry.session, 'after_transaction_end')
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.expire_all()
            session.begin_nested()

    logger.info('Creating registry')
    yield registry

    request.addfinalizer(registry.session.close)


@pytest.fixture(scope='function')
def rollback_registry(request, init_session):
    """Provide registry that is rollback between each tests

    If you want to skip test if demo data are not installed you can
    place ``skip_unless_demo_data_installed`` pytest marker::

    @pytest.mark.skip_unless_demo_data_installed
    def test_somthing(rollback_registry):
        registry = rollback_registry
        ...

    If you want to skip test if demo data are installed you can
    place ``skip_while_demo_data_installed`` pytest marker::

    @pytest.mark.skip_while_demo_data_installed
    def test_somthing(rollback_registry):
        registry = rollback_registry
        ...
    """
    registry = init_session

    if (
        request.node.get_closest_marker('skip_unless_demo_data_installed') and
        not registry.System.Parameter.get("with-demo", False)
    ):
        pytest.skip(  # pragma: no cover
            "Demo data are required (Use ``--with-demo`` to create the "
            "test database)."
        )

    if (
        request.node.get_closest_marker('skip_while_demo_data_installed') and
        registry.System.Parameter.get("with-demo", False)
    ):
        pytest.skip(
            "Demo data are present (Do not use ``--with-demo`` to create the "
            "test database)."
        )

    yield registry

    def clean_up():
        try:
            logger.debug('Invalidating all cache')
            registry.System.Cache.invalidate_all()
        except sqlalchemy.exc.InvalidRequestError:  # pragma: no cover
            logger.warning('Invalid request Error: while invalidating all '
                           'caches after {}'
                           .format(request.function.__name__))
        finally:
            registry.rollback()

    request.addfinalizer(clean_up)
