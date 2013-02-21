#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from mock import MagicMock, Mock, patch
from cello.storage import Case
from cello.models import BadTuneReturnValue
from cello.models import CelloJumpToNextStage
from cello.models import CelloStopScraping
from cello.models import InvalidURLMapping
from cello.models import InvalidStateURLError
from cello.multi.workers import persist_async
from cello.multi.workers import fetch_async


class MockedCase(Case):
    persist = Mock()


def test_persist_async_with_data():
    ("cello.multi.workers.persist_async should "
     "persist the given data appropriately")
    MockedCase.persist.reset_mock()

    stage = Mock()
    worker_queue = Mock()

    data = {
        'name': 'Gabriel',
    }
    persist_async(
        stage=stage,
        case_module_name='tests.unit.multi.test_workers',
        case_name='MockedCase',
        data=data,
        worker_queue=worker_queue,
    )

    MockedCase.persist.assert_called_once_with(data)
    worker_queue.work_done.assert_called_once_with()


def test_persist_async_without_data():
    ("cello.multi.workers.persist_async should "
     "raise when there is no data, but should also clear the queue")
    MockedCase.persist.reset_mock()

    class FakeStage(object):
        url = 'foobar.com'

    worker_queue = Mock()

    persist_async.when.called_with(
        stage=FakeStage(),
        case_module_name='tests.unit.multi.test_workers',
        case_name='MockedCase',
        data={},
        worker_queue=worker_queue,
    ).should.throw(BadTuneReturnValue)

    MockedCase.persist.called.should.be.false

    worker_queue.work_done.assert_called_once_with()


def test_fetch_async_persisting_afterwards():
    ("cello.multi.workers.fetch_async in a stage that has a "
     "case will persist the data after running the scraping methods")

    browser_factory, queue, worker_queue = (Mock(), ) * 3

    MockStage = Mock()
    MockStage.__name__ = 'AMockedStage'
    stage = MockStage.return_value
    stage.case = MockedCase
    stage.tune.return_value = {'data': 0x010101}
    fetch_async(MockStage, browser_factory, queue, worker_queue,
                url="some-url", parent_response="parent response")

    stage.fetch.assert_called_once_with()
    worker_queue.work_done.assert_called_once_with()
    stage.play.assert_called_once_with()

    queue.put.assert_called_once_with(json.dumps({
        'data': 0x010101,
        "case.module": "tests.unit.multi.test_workers",
        "case.name": "MockedCase",
        "stage.module": "mock",
        "stage.name": "AMockedStage",
    }))


def test_fetch_without_a_case():
    ("cello.multi.workers.fetch_async in a stage that does not have a "
     "case will simply run the scraping methods without taking action "
     "towards data persistence")

    browser_factory, queue, worker_queue = (Mock(), ) * 3

    MockStage = Mock()
    stage = MockStage.return_value
    stage.case = None
    stage.tune.return_value = {'data': 0x010101}
    fetch_async(MockStage, browser_factory, queue, worker_queue,
                url="some-url", parent_response="parent response")

    stage.fetch.assert_called_once_with()
    worker_queue.work_done.assert_called_once_with()
    stage.play.assert_called_once_with()

    queue.put.assert_called_once_with('{}')


def test_fetch_upon_error_sends_exception_information_to_queue_stage_fetch():
    ("cello.multi.workers.fetch_async captures any cello-specific exceptions "
     "(the ones declared inside `cello.models`) happened inside "
     "`stage.fetch()`")

    browser_factory, queue, worker_queue = (Mock(), ) * 3

    MockStage = Mock()
    MockStage.return_value.fetch.side_effect = InvalidStateURLError('stop now!', 0x101010)

    fetch_async(MockStage, browser_factory, queue, worker_queue,
                url="some-url", parent_response="parent response")

    worker_queue.work_done.assert_called_once_with()
    queue.put.assert_called_once_with(json.dumps(['InvalidStateURLError', ['stop now!', 0x101010]]))


def test_fetch_upon_error_sends_exception_information_to_queue_stage_play():
    ("cello.multi.workers.play_async captures any cello-specific exceptions "
     "(the ones declared inside `cello.models`) happened inside "
     "`stage.play()`")

    browser_factory, queue, worker_queue = (Mock(), ) * 3

    MockStage = Mock()
    stage = MockStage.return_value
    stage.case = MockedCase
    stage.play.side_effect = CelloStopScraping('stop now!', 0x101010)

    fetch_async(MockStage, browser_factory, queue, worker_queue,
                url="some-url", parent_response="parent response")

    worker_queue.work_done.assert_called_once_with()
    queue.put.assert_called_once_with(json.dumps(['CelloStopScraping', ['stop now!', 0x101010]]))


def test_fetch_upon_error_sends_exception_information_to_queue_stage_tune():
    ("cello.multi.workers.tune_async captures any cello-specific exceptions "
     "(the ones declared inside `cello.models`) happened inside "
     "`stage.tune()`")

    browser_factory, queue, worker_queue = (Mock(), ) * 3

    MockStage = Mock()
    stage = MockStage.return_value
    stage.tune.side_effect = InvalidURLMapping('stop now!', 0x101010)

    fetch_async(MockStage, browser_factory, queue, worker_queue,
                url="some-url", parent_response="parent response")

    worker_queue.work_done.assert_called_once_with()
    queue.put.assert_called_once_with(json.dumps(['InvalidURLMapping', ['stop now!', 0x101010]]))


def test_fetch_upon_jump_to_next_exception_just_raises():
    ("cello.multi.workers.tune_async just raises in case the exception raised is CelloJumpToNextStage")

    browser_factory, queue, worker_queue = (Mock(), ) * 3

    MockStage = Mock()
    stage = MockStage.return_value
    stage.tune.side_effect = CelloJumpToNextStage('just jump to next')

    fetch_async.when.called_with(
        MockStage, browser_factory, queue, worker_queue,
        url="some-url", parent_response="parent response").should.throw(
            CelloJumpToNextStage, "just jump to next")

    worker_queue.work_done.assert_called_once_with()


def test_fetch_upon_system_exception_just_raises():
    ("cello.multi.workers.tune_async just raises in case the exception "
     "raised is not defined in `cello.models`")

    browser_factory, queue, worker_queue = (Mock(), ) * 3

    MockStage = Mock()
    stage = MockStage.return_value
    stage.tune.side_effect = TypeError('whatever')

    fetch_async.when.called_with(
        MockStage, browser_factory, queue, worker_queue,
        url="some-url", parent_response="parent response").should.throw(
            TypeError, "whatever")

    worker_queue.work_done.assert_called_once_with()


@patch('cello.multi.workers.json')
def test_fetch_async_upon_unicode_decode_error_of_serialization(json):
    ("cello.multi.workers.fetch_async captures an `UnicodeDecodeError` "
     "and simply swallows it")

    json.dumps.side_effect = [UnicodeDecodeError('hitchhiker', "", 42, 43, 'the universe and everything else'), 'fake json']
    browser_factory, queue, worker_queue = (Mock(), ) * 3

    MockStage = Mock()
    stage = MockStage.return_value
    stage.case = None

    fetch_async(MockStage, browser_factory, queue, worker_queue,
                url="some-url", parent_response="parent response")

    worker_queue.work_done.assert_called_once_with()
    queue.put.called.should.be.false
