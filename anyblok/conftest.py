# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Denis VIVIÈS <dvivies@geoblink.com>
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

logger = getLogger(__name__)


@pytest.fixture(scope='session')
def init_session(request):
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
    registry = init_session

    yield registry

    def clean_up():
        try:
            logger.debug('Invalidating all cache')
            registry.System.Cache.invalidate_all()
        except sqlalchemy.exc.InvalidRequestError:
            logger.warning('Invalid request Error: while invalidating all '
                           'caches after {}'
                           .format(request.function.__name__))
        finally:
            registry.rollback()

    request.addfinalizer(clean_up)
