#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from StringIO import StringIO
from mock import Mock, patch
from cello.multi.base import BaseWorkerQueue


def test_base_make_queue_not_implemented():
    ("BaseWorkerQueue#make_queue is not implemented by default")
    BaseWorkerQueue.when.called_with(10, StringIO()).should.throw(NotImplementedError)


@patch('cello.multi.base.os')
@patch('cello.multi.base.WorkerLogger')
def test_wait_for_slot_puts_enqueues_process_information(WorkerLogger, os):
    ("BaseWorkerQueue#wait_for_slot enqueues process "
     "information and logs appropriately")
    output = StringIO()
    make_queue_mock = Mock()

    os.getpid.return_value = 42
    log = WorkerLogger.return_value
    make_queue_mock.return_value.put.side_effect = (
        lambda *a, **k: log.permission_to_run.called.should.be.false)

    class MockQueue(BaseWorkerQueue):
        make_queue = make_queue_mock

    queue = MockQueue(10, output)
    queue.wait_for_slot('my_patient_function', 'cool.scraper.module')

    log.process_await('my_patient_function', 42)
    queue.q.put.assert_called_once_with({
        'function': 'my_patient_function',
        'module_name': 'cool.scraper.module',
        'pid': 42,
    }, block=True, timeout=None)

    log.permission_to_run.assert_called_once_with('my_patient_function', 42)

    output.getvalue().should.equal('')


@patch('cello.multi.base.os')
@patch('cello.multi.base.WorkerLogger')
def test_work_done_gets_from_queue(WorkerLogger, os):
    ("BaseWorkerQueue#work_done consumes queue and logs "
     "process_done with given data")

    output = StringIO()
    make_queue_mock = Mock()
    log = WorkerLogger.return_value

    make_queue_mock.return_value.get.return_value = {
        'function': 'quick_function',
        'pid': 42,
        'module_name': 'some.module'
    }

    class MockQueue(BaseWorkerQueue):
        make_queue = make_queue_mock

    queue = MockQueue(10, output)
    queue.work_done()

    queue.q.get.assert_called_once_with(block=True, timeout=None)

    log.process_done.assert_called_once_with(
        function_name='quick_function',
        pid=42,
    )
    output.getvalue().should.equal('')


def test_close():
    ("BaseWorkerQueue#close closes the queue and joins the thread")
    output = StringIO()

    make_queue_mock = Mock()

    class MockQueue(BaseWorkerQueue):
        make_queue = make_queue_mock

    queue = MockQueue(10, output)
    queue.close()

    queue.q.close.assert_called_once_with()
    queue.q.join_thread.assert_called_once_with()
    output.getvalue().should.equal('')
