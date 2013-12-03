#!/usr/bin/env python
from distutils.core import setup

setup(name = 'PhysicsTable',
      version = '0.13',
      description = '2-D physics tables for intuitive physics psychology experiments',
      author = 'Kevin A Smith',
      author_email = 'k2smith@ucsd.edu',
      url = 'https://code.google.com/p/physics-tables/',
      packages = ['physicsTable','physicsTable.objects','physicsTable.utils','physicsTable.constants'],
      requires = ['pygame','pymunk','numpy','scipy']
      )