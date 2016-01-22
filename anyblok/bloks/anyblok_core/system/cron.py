# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import Integer, DateTime, Json, String, Boolean, Text
from threading import Thread
from datetime import datetime
from time import sleep
from sqlalchemy import or_
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound
from ..exceptions import CronWorkerException
from logging import getLogger
logger = getLogger(__name__)


register = Declarations.register
System = Declarations.Model.System


@register(System)
class Cron:
    started = True

    @classmethod
    def add_worker_for(cls, record):
        worker = cls.registry.System.Cron.Worker(record)
        worker.start()
        return worker

    @classmethod
    def close_worker_with_success(cls, worker):
        worker.job.update(done_at=datetime.now())

    @classmethod
    def close_worker_on_error(cls, worker, error):
        worker.job.update(error=error)

    @classmethod
    def lock_one_job(cls):
        Job = cls.registry.System.Cron.Job
        query = Job.query().filter(Job.done_at.is_(None))
        query = query.filter(or_(Job.available_at.is_(None),
                                 Job.available_at <= datetime.now()))
        nb_available_line = query.count()
        if not nb_available_line:
            return None

        query = query.limit(1)
        for offset in range(nb_available_line):
            try:
                job = query.offset(offset).with_for_update(nowait=True).one()
                return job
            except (OperationalError, NoResultFound):
                cls.registry.rollback()

        return None

    @classmethod
    def run(cls, sleep_time=60, timeout=None):
        sleep_time = 60
        while cls.started:
            job = cls.lock_one_job()
            if job is not None:
                cls.registry.System.Cache.clear_invalidate_cache()
                worker = cls.add_worker_for(job)
                worker.join(timeout)
                error = worker.get_error()
                if error:
                    cls.close_worker_on_error(worker, error)
                else:
                    cls.close_worker_with_success(worker)

                cls.registry.commit()
            else:
                sleep(sleep_time)


@register(System.Cron)
class Job:

    id = Integer(primary_key=True)
    available_at = DateTime()
    done_at = DateTime()
    model = String(nullable=False, foreign_key=System.Model.use('name'))
    method = String(nullable=False)
    is_a_class_method = Boolean(default=True)
    params = Json()
    error = Text()

    def __repr__(self):
        msg = "<Cron job %s.%s" % (self.model, self.method)
        if self.is_a_class_method:
            msg += "(CM)"

        if self.available_at:
            msg += " available at %s" % self.available_at

        msg += " with params %r>" % (self.params)
        return msg


@register(System.Cron)
class Worker(Thread):

    def __init__(self, job):
        super(Worker, self).__init__()
        self.job = job
        self.error = None

    def get_model_record(self):
        params = self.job.params
        if not params or 'primary_keys' not in params:
            raise CronWorkerException("%r : No primary key found in params" %
                                      self.job)
        obj = self.registry.get(self.job.model).from_primary_keys(
            **params['primary_keys'])

        if obj is None:
            raise CronWorkerException("%r : Wrong primary key %r" % (
                self.job, params['primary_keys']))

        return obj

    def get_args_and_kwargs(self):
        params = self.job.params
        args = ()
        kwargs = {}
        if params and 'args' in params:
            args = params['args']

        if isinstance(args, list):
            args = tuple(args)
        elif not isinstance(args, tuple):
            args = (args,)

        if params and 'kwargs' in params:
            kwargs = params['kwargs']

        if not isinstance(kwargs, dict):
            raise CronWorkerException("%r : Kwargs %r must be a dict" % (
                self.job, kwargs))

        return args, kwargs

    def call_method(self):
        if self.job.is_a_class_method:
            record = self.registry.get(self.job.model)
        else:
            record = self.get_model_record()

        func = getattr(record, self.job.method, None)
        if func is None:
            raise CronWorkerException("%r : Inexisting method" % self.job)

        args, kwargs = self.get_args_and_kwargs()
        return func(*args, **kwargs)

    def get_error(self):
        return self.error

    def run(self):
        logger.info("Start worker for %r", self.job)
        try:
            self.call_method()
            self.registry.commit()
        except Exception as e:
            logger.error('Error during execution of %r : %r', self.job, e)
            self.error(str(e))
            self.registry.rollback()
        else:
            logger.info("Worker for %r finish with success", self.job)
        finally:
            self.registry.session.close()
