#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from sure import expect
from cello.multi.thread import WorkerQueue


def test_creates_queue_with_n_elements():
    ("WorkerQueue#make_queue is not implemented by default [threading implementation]")

    queue = WorkerQueue(10)

    queue.max_workers.should.equal(10)
    expect(queue.q).to.be.a('Queue.Queue')
