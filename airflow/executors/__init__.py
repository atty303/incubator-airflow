# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys

from airflow import configuration
from airflow.executors.base_executor import BaseExecutor
from airflow.executors.local_executor import LocalExecutor
from airflow.executors.sequential_executor import SequentialExecutor

try:
    from airflow.executors.celery_executor import CeleryExecutor
except:
    pass

from airflow.exceptions import AirflowException

DEFAULT_EXECUTOR = None

def _integrate_plugins():
    """Integrate plugins to the context."""
    from airflow.plugins_manager import executors_modules
    for executors_module in executors_modules:
        sys.modules[executors_module.__name__] = executors_module
        globals()[executors_module._name] = executors_module

def GetDefaultExecutor():
    """Creates a new instance of the configured executor if none exists and returns it"""
    global DEFAULT_EXECUTOR

    if DEFAULT_EXECUTOR is not None:
        return DEFAULT_EXECUTOR

    executor_name = configuration.get('core', 'EXECUTOR')

    DEFAULT_EXECUTOR = _get_executor(executor_name)

    logging.info("Using executor " + executor_name)

    return DEFAULT_EXECUTOR


def _get_executor(executor_name):
    """
    Creates a new instance of the named executor. In case the executor name is not know in airflow, 
    look for it in the plugins
    """
    if executor_name == 'LocalExecutor':
        return LocalExecutor()
    elif executor_name == 'SequentialExecutor':
        return SequentialExecutor()
    elif executor_name == 'CeleryExecutor':
        from airflow.executors.celery_executor import CeleryExecutor
        return CeleryExecutor()
    elif executor_name == 'MesosExecutor':
        from airflow.contrib.executors.mesos_executor import MesosExecutor
        return MesosExecutor()
    else:
        # Loading plugins
        _integrate_plugins()
        executor_path = executor_name.split('.')
        if len(executor_path) != 2:
            raise AirflowException(
                "Executor {0} not supported: please specify in format plugin_module.executor".format(executor_name))

        if executor_path[0] in globals():
            return globals()[executor_path[0]].__dict__[executor_path[1]]()
        else:
            raise AirflowException("Executor {0} not supported.".format(executor_name))


