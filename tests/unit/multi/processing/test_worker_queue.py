#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from StringIO import StringIO
from cello.multi.processing import WorkerQueue


def test_creates_queue_with_n_elements():
    ("WorkerQueue#make_queue is not implemented by default [multiprocessing implementation]")

    queue = WorkerQueue(10, StringIO())

    queue.max_workers.should.equal(10)
    queue.q.should.be.a('multiprocessing.queues.Queue')
