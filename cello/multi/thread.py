#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from Queue import Queue
from cello.multi.base import BaseWorkerQueue, BaseMultiProcessStage


class WorkerQueue(BaseWorkerQueue):
    def make_queue(self, max_workers):
        return Queue(max_workers)


class MultiThreadStage(BaseMultiProcessStage):
    Queue = Queue
    Process = threading.Thread
    WorkerQueue = WorkerQueue
