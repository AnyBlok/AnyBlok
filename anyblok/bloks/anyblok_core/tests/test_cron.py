# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase
from datetime import datetime, timedelta
from ..exceptions import CronWorkerException


class TestCron(BlokTestCase):

    def test_add_worker_for(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state")
        worker = Cron.add_worker_for(job)
        self.assertIs(job, worker.job)
        worker.join()

    def test_close_worker_with_success(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state")
        worker = Cron.Worker(job)
        self.assertIsNone(job.done_at)
        Cron.close_worker_with_success(worker)
        self.assertIsNotNone(job.done_at)

    def test_close_worker_on_error(self):
        error = 'One error with this traceback'
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state")
        worker = Cron.Worker(job)
        self.assertIsNone(job.done_at)
        self.assertIsNone(job.error)
        Cron.close_worker_on_error(worker, error)
        self.assertEqual(job.error, error)
        self.assertIsNone(job.done_at)

    def test_lock_one_record_no_existing_record(self):
        Cron = self.registry.System.Cron
        locked_job = Cron.lock_one_job()
        self.assertIsNone(locked_job)

    def test_lock_one_record_lock_existing_record(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state")
        locked_job = Cron.lock_one_job()
        self.assertIs(locked_job, job)

    def test_lock_one_record_ended_existing_record(self):
        Cron = self.registry.System.Cron
        Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state",
            done_at=datetime.now())
        locked_job = Cron.lock_one_job()
        self.assertIsNone(locked_job)

    def test_lock_one_record_upper_dated_existing_record(self):
        Cron = self.registry.System.Cron
        Cron.Job.insert(model="Model.System.Blok", method="list_by_state",
                        available_at=datetime.now() + timedelta(days=1))
        locked_job = Cron.lock_one_job()
        self.assertIsNone(locked_job)

    def test_lock_one_record_lock_existing_record2(self):
        Cron = self.registry.System.Cron
        Cron.Job.insert(model="Model.System.Blok", method="list_by_state",
                        done_at=datetime.now())
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state")
        locked_job = Cron.lock_one_job()
        self.assertIs(locked_job, job)


class TestWorker(BlokTestCase):

    def test_get_model_record(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state",
            params={'primary_keys': {'name': 'anyblok-core'}})
        worker = Cron.Worker(job)
        record = worker.get_model_record()
        self.assertEqual(record.name, 'anyblok-core')

    def test_get_model_record_without_pks(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state")
        worker = Cron.Worker(job)
        with self.assertRaises(CronWorkerException):
            worker.get_model_record()

    def test_get_model_record_with_invalid_pks(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state",
            params={'primary_keys': {'name': 'wrongblok'}})
        worker = Cron.Worker(job)
        with self.assertRaises(CronWorkerException):
            worker.get_model_record()

    def test_get_arg(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state",
            params={'args': 'name'})
        worker = Cron.Worker(job)
        args, kwargs = worker.get_args_and_kwargs()
        self.assertEqual(args, ('name',))
        self.assertEqual(kwargs, {})

    def test_get_args(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state",
            params={'args': ['name']})
        worker = Cron.Worker(job)
        args, kwargs = worker.get_args_and_kwargs()
        self.assertEqual(args, ('name',))
        self.assertEqual(kwargs, {})

    def test_get_invalid_kwargs(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state",
            params={'kwargs': 'name'})
        worker = Cron.Worker(job)
        with self.assertRaises(CronWorkerException):
            worker.get_args_and_kwargs()

    def test_call_method(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state")
        worker = Cron.Worker(job)
        res = worker.call_method()
        self.assertIsNone(res, None)

    def test_call_method2(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="list_by_state",
            params={'args': 'installed'})
        worker = Cron.Worker(job)
        res = worker.call_method()
        self.assertIsNotNone(res)

    def test_call_method3(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="get_short_description",
            is_a_class_method=False,
            params={'primary_keys': {'name': 'anyblok-core'}})
        worker = Cron.Worker(job)
        res = worker.call_method()
        ac = self.registry.System.Blok.from_primary_keys(name='anyblok-core')
        self.assertEqual(res, ac.short_description)

    def test_call_inexisting_method(self):
        Cron = self.registry.System.Cron
        job = Cron.Job.insert(
            model="Model.System.Blok", method="inexisting_method")
        worker = Cron.Worker(job)
        with self.assertRaises(CronWorkerException):
            worker.call_method()
