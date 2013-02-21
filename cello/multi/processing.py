#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Process, Queue
from cello.multi.base import BaseWorkerQueue, BaseMultiProcessStage


class WorkerQueue(BaseWorkerQueue):
    def make_queue(self, max_workers):
        return Queue(max_workers)


class MultiProcessStage(BaseMultiProcessStage):
    Queue = Queue
    Process = Process
    WorkerQueue = WorkerQueue
