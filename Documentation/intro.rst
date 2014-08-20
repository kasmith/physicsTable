=================
Introduction
=================

.. _PyGame: http://www.pygame.org/
.. _Pymunk: http://www.pymunk.org/

The `PhysicsTable` package has been designed as a way to create and model the motion of objects bouncing around 2-D tables for psychological experiments.
It forms a wrapper around `PyGame`_ and `Pymunk`_ to offer a simple way of modeling and displaying objects with 2-D physics.

There are three core types of objects in the PhysicsTable package:

1. **Tables** are the workhorse object of the package - they contain a collection of **Objects** confined to a space, and have methods to evolve over time and display their contents.
2. **Trials** are for storing and instantiating Tables. Trials are static definitions of the initial state of a table (they do not have methods that evolve over time), but can be easily saved and loaded.
3. **Models** are for getting posterior predictive distributions over the future states of a Table. They come in two flavors: **PointSimulation** calculates the posterior predictive at a single point in time, while **PathFilter** models track how simulation changes over time.

