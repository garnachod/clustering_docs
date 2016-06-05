#!/usr/bin/env python

from distutils.core import setup

setup(name='ConcursoPolicia',
      version='1.0',
      description='Buscador de usuarios en twitter',
      author='Daniel Garnacho',
      author_email='garnachod@gmail.com',
      packages=['Config', 'LuigiTasks', 'ProcesadoresTexto'],
      package_dir={},
    )
