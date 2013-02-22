#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from StringIO import StringIO
from mock import patch
from cello.multi.base import WorkerLogger


@patch('cello.multi.base.couleur')
@patch('cello.multi.base.datetime')
def test_process_await(datetime, couleur):
    ("WorkerLogger#process_await prints in magenta")

    datetime.now.return_value = "now :)"
    sh = couleur.Shell.return_value

    logger = WorkerLogger(StringIO())

    logger.process_await('some_function', 'some pid')

    sh.bold_white.assert_called_once_with("[now :)] <~ ")
    sh.magenta.assert_called_once_with(
        "Worker some_function (PID some pid) is waiting "
        "for a slot in the queue\n")


@patch('cello.multi.base.couleur')
@patch('cello.multi.base.datetime')
def test_permission_to_run(datetime, couleur):
    ("WorkerLogger#permission_to_run prints in bold yellow")

    datetime.now.return_value = "now :)"
    sh = couleur.Shell.return_value

    logger = WorkerLogger(StringIO())

    logger.permission_to_run('some_function', 'some pid')

    sh.bold_white.assert_called_once_with("[now :)] <~ ")
    sh.bold_yellow.assert_called_once_with(
        "Worker some_function (PID some pid) has permission to run now \n")


@patch('cello.multi.base.couleur')
@patch('cello.multi.base.datetime')
def test_process_done(datetime, couleur):
    ("WorkerLogger#permission_to_run prints in bold cyan")

    datetime.now.return_value = "now :)"
    sh = couleur.Shell.return_value

    logger = WorkerLogger(StringIO())

    logger.process_done('some_function', 'some pid')

    sh.bold_white.assert_called_once_with("[now :)] <~ ")
    sh.bold_cyan.assert_called_once_with(
        "Done with some_function, "
        "process id some pid will exit now\n")
