#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from mock import Mock, call, patch
from cello.models import CelloStopScraping
from cello.multi.base import BaseMultiProcessStage as Stage
from cello.multi.base import fetch_async, persist_async


def test_get_response_with_sleepyhollow_responses():
    ("MultiProcessStage#get_response uses .html from "
     "a SleepyHollow response")

    class ResponseFromSleepyHollow(object):
        html = 'HTML coming from SleepyHollow().get().html'

    browser_factory = Mock()
    browser_factory.return_value.get.return_value = ResponseFromSleepyHollow()

    worker_queue = Mock()

    s = Stage(browser_factory, worker_queue)

    response = s.get_response('http://some-url.com')

    response.should.equal('HTML coming from SleepyHollow().get().html')


def test_get_response_with_requests_responses():
    ("MultiProcessStage#get_response uses .content from "
     "a requests response")

    class ResponseFromRequestsModule(object):
        content = 'HTML coming from requests.get().content'

    browser_factory = Mock()
    browser_factory.return_value.get.return_value = ResponseFromRequestsModule()

    worker_queue = Mock()

    s = Stage(browser_factory, worker_queue)

    response = s.get_response('http://some-url.com')

    response.should.equal('HTML coming from requests.get().content')


def test_proceed_to_next_returns_a_process_with_current_stage_if_not_next():
    ("MultiProcessStage#process_next returns a new process pointing to "
     "the current Stage if there are no next stages")

    process_mock = Mock()

    class NoNextStage(Stage):
        Process = process_mock

    browser_factory = Mock()
    worker_queue = Mock()
    queue = Mock()

    s = NoNextStage(
        browser_factory,
        worker_queue,
        queue=queue,
    )

    process = s.proceed_to_next(
        'http://some-link.com/link1',
        using_response='some response',
    )

    process.should.equal(process_mock.return_value)

    process_mock.assert_called_once_with(
        target=fetch_async,
        name='http://some-link.com/link1',
        args=(NoNextStage, browser_factory),
        kwargs={
            'url': 'http://some-link.com/link1',
            'parent_response': 'some response',
            'queue': queue,
            'worker_queue': worker_queue,
        }
    )


def test_proceed_to_next_returns_a_process_with_next_stage():
    ("MultiProcessStage#process_next returns a new process pointing to "
     "the current Stage if there are no next stages")

    process_mock = Mock()

    class TheNextOne(Stage):
        pass

    class HasNextStage(Stage):
        next_stage = TheNextOne
        Process = process_mock

    browser_factory = Mock()
    worker_queue = Mock()
    queue = Mock()

    s = HasNextStage(
        browser_factory,
        worker_queue,
        queue=queue,
    )

    process = s.proceed_to_next('http://some-link.com/link1',
                                using_response='some response')

    process.should.equal(process_mock.return_value)

    process_mock.assert_called_once_with(
        target=fetch_async,
        name='http://some-link.com/link1',
        args=(TheNextOne, browser_factory),
        kwargs={
            'url': 'http://some-link.com/link1',
            'parent_response': 'some response',
            'queue': queue,
            'worker_queue': worker_queue,
        }
    )


def test_scrape_list_of_links():
    ("MultiProcessStage.scrape should create a worker for each link")

    consume_queue_mock = Mock()

    worker_start = Mock()

    class ScrapableStage(Stage):
        consume_queue = consume_queue_mock

        def proceed_to_next(self, link, using_response):
            attrs = {}
            attrs['name'] = 'Worker for {}'.format(link)
            attrs['url'] = link
            attrs['using_response'] = using_response
            attrs['start'] = worker_start

            return type(b'FakeWorker', (object,), attrs)

    browser_factory = Mock()
    worker_queue = Mock()

    st = ScrapableStage(browser_factory, worker_queue)

    st.scrape(['url1', 'url2'])

    worker_queue.wait_for_slot.assert_has_calls([
        call('fetch_async("Worker for url1")', 'tests.unit.multi.test_multiprocess_stage'),
        call('fetch_async("Worker for url2")', 'tests.unit.multi.test_multiprocess_stage'),
    ])

    worker_start.call_count.should.equal(2)


def test_scrape_single_url_string():
    ("MultiProcessStage.scrape should consider a single string")

    consume_queue_mock = Mock()

    worker_start = Mock()

    class ScrapableStage(Stage):
        consume_queue = consume_queue_mock

        def proceed_to_next(self, link, using_response):
            attrs = {}
            attrs['name'] = 'Worker for {}'.format(link)
            attrs['url'] = link
            attrs['using_response'] = using_response
            attrs['start'] = worker_start

            return type(b'FakeWorker', (object,), attrs)

    browser_factory = Mock()
    worker_queue = Mock()

    st = ScrapableStage(browser_factory, worker_queue)

    st.scrape('the url')

    worker_queue.wait_for_slot.assert_called_once_with(
        'fetch_async("Worker for the url")',
        'tests.unit.multi.test_multiprocess_stage')

    worker_start.assert_called_once_with()


def test_consume_queue():
    ("MultiProcessStage#consume_queue will persist next "
     "queued item until the queue is empty")

    browser_factory = Mock()
    worker_queue = Mock()
    scrape_queue = Mock()

    scrape_queue.empty.side_effect = [False, False, False, True]

    class MyStage(Stage):
        persist_next_queued_item = Mock()

    MyStage(browser_factory, worker_queue, queue=scrape_queue).consume_queue()

    MyStage.persist_next_queued_item.call_count.should.equal(3)


def test_persist_next_queued_item_without_error_and_case():
    ("MultiProcessStage#persist_next_queued_item with no error and no case")

    browser_factory = Mock()
    worker_queue = Mock()
    scrape_queue = Mock()
    scrape_queue.get.return_value = json.dumps({
        'function': 'some_function',
        'module': 'some.module',
        'pid': 66,
    })

    st = Stage(browser_factory, worker_queue, queue=scrape_queue)

    scrape_queue.task_done.called.should.be.false

    st.persist_next_queued_item()

    scrape_queue.task_done.called.should.be.true


def test_persist_next_queued_item_without_error():
    ("MultiProcessStage#persist_next_queued_item with no error and no case")

    browser_factory = Mock()
    worker_queue = Mock()
    scrape_queue = Mock()
    scrape_queue.get.return_value = json.dumps(['CelloStopScraping', ('the message',)])

    st = Stage(browser_factory, worker_queue, queue=scrape_queue)

    scrape_queue.task_done.called.should.be.false

    st.persist_next_queued_item.when.called.to.throw(
        CelloStopScraping, 'the message')

    scrape_queue.task_done.called.should.be.true


def test_persist_next_queued_item_with_case():
    ("MultiProcessStage#persist_next_queued_item with a case "
     "will spawn a worker for persisting that data")

    process_mock = Mock()

    class MyStage(Stage):
        Process = process_mock
        import_stage = Mock()
        make_children_stage = Mock()

    browser_factory = Mock()
    worker_queue = Mock()
    scrape_queue = Mock()
    scrape_queue.get.return_value = json.dumps({
        'foo': 'bar',
        'case.module': 'some.module',
        'case.name': 'SomeCase',
        'stage.name': 'WhateverStage',
        'stage.module': 'what.ever',
    })

    st = MyStage(browser_factory, worker_queue, queue=scrape_queue)

    scrape_queue.task_done.called.should.be.false

    st.persist_next_queued_item()

    process_mock.assert_called_once_with(
        target=persist_async,
        kwargs={
            "worker_queue": worker_queue,
            "case_module_name": 'some.module',
            "case_name": 'SomeCase',
            "data": {'foo': 'bar'},
            "stage": MyStage.make_children_stage.return_value,
        }
    )
    process_mock.return_value.start.assert_called_once_with()
    worker_queue.wait_for_slot.assert_called_once_with(
        'persist_async', 'tests.unit.multi.test_multiprocess_stage')

    scrape_queue.task_done.called.should.be.true
    MyStage.import_stage.assert_called_once_with('what.ever', 'WhateverStage')
    MyStage.make_children_stage.assert_called_once_with(
        MyStage.import_stage.return_value)


def test_visit():
    ("MultiProcessStage#play creates a worker queue and plays the stage")

    class MyStage(Stage):
        url = "http://foo.com"

        fetch = Mock()
        play = Mock()
        WorkerQueue = Mock()

    browser_factory = Mock()

    MyStage.visit(browser_factory, max_workers=30)

    MyStage.play.assert_called_once_with()
    MyStage.WorkerQueue.assert_called_once_with(30)


@patch('cello.multi.base.couleur')
def test_visit_with_keyboard_interrupt(couleur):
    ("MultiProcessStage#play creates a worker queue and plays the stage")

    class MyStage(Stage):
        url = "http://foo.com"

        fetch = Mock()
        play = Mock(side_effect=KeyboardInterrupt())
        WorkerQueue = Mock()

    browser_factory = Mock()

    MyStage.visit(browser_factory, max_workers=30)

    MyStage.play.assert_called_once_with()
    MyStage.WorkerQueue.assert_called_once_with(30)

    couleur.Shell.return_value.bold_red.assert_called_once_with("User pressed CONTROL-C\n")


def test_make_children_stage():
    ("MultiProcessStage#make_children_stage should use "
     "its own data to create a child")

    browser_factory = Mock()
    worker_queue = Mock()

    stage = Stage(
        browser_factory,
        worker_queue,
        parent_response='parent response',
        queue='some queue',
    )

    StageClassMock = Mock()

    child = stage.make_children_stage(StageClassMock)

    child.should.equal(StageClassMock.return_value)

    StageClassMock.assert_called_once_with(
        browser_factory,
        worker_queue,
        parent_response='parent response',
        queue='some queue',
    )


@patch('cello.multi.base.importlib')
def test_import_stage(importlib):
    ("MultiProcessStage.import_stage should "
     "import the given module and get the member from it")
    importlib.import_module.return_value.SomeMember = 'YAY'

    GivenStage = Stage.import_stage('some.module', 'SomeMember')

    importlib.import_module.assert_called_once_with('some.module')

    GivenStage.should.equal("YAY")
