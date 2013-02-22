#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import json
import couleur
import importlib

from datetime import datetime
from cello import models
from cello.models import Stage
from cello.multi.workers import persist_async, fetch_async
from multiprocessing import cpu_count


DEFAULT_MAX_WORKERS = cpu_count()


class WorkerLogger(object):
    def __init__(self, output):
        self.sh = couleur.Shell(output=output)

    def log_prefix(self):
        self.sh.bold_white("[{0}] <~ ".format(datetime.now()))

    def process_await(self, function_name, pid):
        self.log_prefix()
        self.sh.magenta(
            "Worker {0} (PID {1}) is waiting "
            "for a slot in the queue\n".format(function_name, pid))

    def permission_to_run(self, function_name, pid):
        self.log_prefix()
        self.sh.bold_yellow(
            "Worker {0} (PID {1}) has permission to run now \n"
            .format(function_name, pid))

    def process_done(self, function_name, pid):
        self.log_prefix()
        self.sh.bold_cyan(
            "Done with {0}, "
            "process id {1} will exit now\n".format(function_name, pid))


class BaseWorkerQueue(object):
    def __init__(self, max_workers, output):
        self.q = self.make_queue(int(max_workers))
        self.max_workers = max_workers
        self.log = WorkerLogger(output)

    def make_queue(self, max_workers):
        raise NotImplementedError

    def close(self):
        self.q.close()
        self.q.join_thread()

    def work_done(self):
        data = self.q.get(block=True, timeout=None)

        self.log.process_done(
            function_name=data['function'],
            pid=data['pid'],
        )

    def wait_for_slot(self, function_name, module_name):
        PID = os.getpid()

        self.log.process_await(function_name, PID)

        self.q.put({
            'function': function_name,
            'module_name': module_name,
            'pid': PID}, block=True, timeout=None)

        self.log.permission_to_run(function_name, PID)


class BaseMultiProcessStage(Stage):
    case = None

    WorkerQueue = None
    Queue = None
    Process = None

    def __init__(self, browser_factory, worker_queue,
                 url=None, parent_response=None, queue=None, *args, **kw):

        self.browser_factory = browser_factory
        self.parent_response = parent_response
        self.worker_queue = worker_queue
        self.queue = queue or worker_queue.make_queue(DEFAULT_MAX_WORKERS)

        super(BaseMultiProcessStage, self).__init__(None, url=url, *args, **kw)

    def get_response(self, url):
        http = self.browser_factory()
        return http.get(url)

    def proceed_to_next(self, link, using_response=None):
        Stage = self.get_next_stage()
        if Stage == self.__class__:
            parent = self.parent
        else:
            parent = self

        return self.Process(target=fetch_async,
                            name=link,
                            args=(Stage, self.browser_factory),
                            kwargs=dict(
                                url=link,
                                parent=parent,
                                parent_response=using_response,
                                queue=self.queue,
                                worker_queue=self.worker_queue))

    def scrape(self, links, using_response=None):
        if isinstance(links, basestring):
            links = [links]

        for link in links:
            worker = self.proceed_to_next(link, using_response)
            self.worker_queue.wait_for_slot('fetch_async("{0}")'.format(worker.name), self.__class__.__module__)
            worker.start()

        self.consume_queue()

    def make_children_stage(self, StageClass):
        return StageClass(
            self.browser_factory,
            self.worker_queue,
            parent=self,
            parent_response=self.parent_response,
            queue=self.queue,
        )

    @classmethod
    def import_stage(cls, module_name, stage_name):
        stage_module = importlib.import_module(module_name)
        return getattr(stage_module, stage_name)

    def persist_next_queued_item(self):
        raw = self.queue.get()
        data = json.loads(raw)

        is_error = isinstance(data, list)
        if is_error:
            name, args = data
            ExceptionClass = getattr(models, name)
            raise ExceptionClass(*args)

        if 'case.module' in data and 'case.name' in data:
            stage_module_name = data.pop('stage.module')
            stage_name = data.pop('stage.name')

            Stage = self.import_stage(stage_module_name, stage_name)
            stage = self.make_children_stage(Stage)

            p = self.Process(
                target=persist_async,
                kwargs={
                    "stage": stage,
                    "worker_queue": self.worker_queue,
                    "results_queue": self.queue,
                    "case_module_name": data.pop('case.module'),
                    "case_name": data.pop('case.name'),
                    "data": data})
            self.worker_queue.wait_for_slot('persist_async', self.__class__.__module__)
            p.start()

    def consume_queue(self):
        while not self.queue.empty():
            self.persist_next_queued_item()

    @classmethod
    def visit(Stage, browser_factory,
              max_workers=DEFAULT_MAX_WORKERS, output=None, *args, **kw):

        worker_queue = Stage.WorkerQueue(max_workers, output=output or sys.stdout)
        waits = [worker_queue.wait_for_slot('preparing worker {0} for {1}'.format(x, Stage.__name__), Stage.__module__) for x in range(1, max_workers)]

        kw['worker_queue'] = worker_queue
        try:
            super(BaseMultiProcessStage, Stage).visit(
                browser_factory, *args, **kw)

            while waits:
                worker_queue.work_done()
                waits.pop()

        except KeyboardInterrupt:
            sh = couleur.Shell()
            sh.bold_red("User pressed CONTROL-C\n")
