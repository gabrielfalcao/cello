#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import importlib

from cello import models


def persist_async(stage, case_module_name, case_name, data, worker_queue):
    Stage = stage.__class__
    if not data:
        worker_queue.work_done()
        raise models.BadTuneReturnValue(
            models.BadTuneReturnValue.msg.format(
                name=Stage.__name__,
                url=Stage.url,
                value=repr(data),
            )
        )

    module = importlib.import_module(case_module_name)
    Case = getattr(module, case_name)
    try:
        Case(stage).persist(data)
    finally:
        worker_queue.work_done()


def fetch_async(Stage, browser_factory, queue, worker_queue, url=None, parent_response=None):
    work_done = False
    try:
        stage = Stage(browser_factory,
                      worker_queue=worker_queue,
                      url=url,
                      parent_response=parent_response)
        stage.fetch()
        worker_queue.work_done()
        work_done = True
        stage.play()
        if stage.case:
            data = stage.tune() or {}
            data['case.module'] = stage.case.__module__
            data['case.name'] = stage.case.__name__
            data['stage.module'] = Stage.__module__
            data['stage.name'] = Stage.__name__
        else:
            data = {}

    except Exception as e:
        if not work_done:
            worker_queue.work_done()
        name = e.__class__.__name__
        data = (name, e.args)
        if (not hasattr(models, name)
                or isinstance(e, models.CelloJumpToNextStage)):
            raise

    try:
        serialized = json.dumps(data)
    except UnicodeDecodeError as e:
        return

    queue.put(serialized)
