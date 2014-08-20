=================
Tables
=================

Tables come in four different flavors:

1. :ref:`BasicTables <basic_table>` allow for any combination of objects and unfold deterministically
2. :ref:`SimpleTables <SimpleTable>` are like BasicTables but allow only one ball at a time
3. :ref:`NoisyTables <noisy_table>` are SimpleTables that utilize stochastic physics from Smith & Vul (2013)
4. :ref:`GravityTables <gravity_table>` are SimpleTables in which objects fall towards the bottom

.. _basic_table:

BasicTable
----------------

.. class:: BasicTable(dims, closed_ends, background_cl, def_ball_rad, def_ball_cl, def_pad_len, def_wall_cl, def_occ_cl, def_pad_cl, active, soffset, defscreen)
   
   
   Initializes and returns a BasicTable object.
   
   :param dims: A tuple (x,y) of table dimensions in pixels
   :param closed_ends: A list of direction constants to determine which sides of the table should be walled off. Defaults to ``[LEFT, RIGHT, BOTTOM, TOP]``
   :param background_cl: Color of the table background. Defaults to ``WHITE``
   :param def_ball_rad: Default radius (in px) for :class:`objects.Ball` objects added to the table. Defaults to ``20``
   :param def_ball_cl: Default color of :class:`objects.Ball` objects added to the table. Defaults to ``BLUE``
   :param def_pad_len: Default length (in px) of :class:`objects.Paddle` objects added to the table. Defaults to ``100``
   :param def_wall_cl: Default color of :class:`objects.Wall` and :class:`objects.AbnormWall` objects added to the table. Defaults to ``BLACK``
   :param def_occ_cl: Default color of :class:`objects.Occlusion` objects added to the table. Defaults to ``GREY``
   :param def_pad_cl: Default color of :class:`objects.Paddle` objects added to the table. Defaults to ``BLACK``
   :param active: Defines the initial activity of the table. See the :func:`BasicTable.activate()` and :func:`BasicTable.deactivate()` methods. Defaults to ``True``
   :param soffset: A tuple (x,y) of the offset from the parent Surface to place this table for drawing. If ``None`` (default), places the table in the middle of the surface
   :param defscreen: A :class:`pygame.Surface` object on which to place the BasicTable. If ``None`` (default) and a pygame window is open, defaults to the display surface


Adding Objects
~~~~~~~~~~~~~~~~~~

.. function:: addBall(initpos, initvel, rad, color, elast)
   :module: BasicTable
   
   Adds a ball to the table, centered at an (x,y) coordinate defined in ``initpos``, with a velocity vector (vx,vy) given to ``initvel``. 
   If not defined, radius and color are set to the table defaults, and elasticity is set to 1. 

.. function:: addWall(upperleft, lowerright, color, elast)
   :module: BasicTable
   
   Adds a rectangular wall to the table, with upperleft and lowerright coordinates given. If not defined, color is set to the table default, and elasticity is set to 1.
   
.. function:: addAbnormWall(vertexlist, color, elast)
   :module: BasicTable
   
   Adds a non-rectangular wall to the table. Vertices are given as a list of (x,y) tuples in ``vertexlist``, and must be convex and counterclockwise. If not defined, color is set to the table default, and elasticity is set to 1.

.. function:: addOcc(upperleft, lowerright, color)
   :module: BasicTable
   
   Adds a rectangular occluder to the table, with upperleft and lowerright coordinates given. Balls can pass through occluders, but cannot be seen through them. If not defined, color is set to the table default.

.. function:: addGoal(upperleft, lowerright,onreturn, color)
   :module: BasicTable
   
   Adds a rectangular goal to the table, with upperleft and lowerright coordinates given. 
   When a ball hits a goal the table will no longer unfold in time, and :func:`BasicTable.step()` calls will return the value defined in ``onreturn``. 
   If a color is not given, the goal will be invisible.

.. function:: addPaddle(p1,p2,padlen, padwid, hitret, active, acol, iacol, pthcol, elast)
   :module: BasicTable
   
   Adds a paddle to the table, that can move between endpoints ``p1`` and ``p2``. The paddle must be verticle or horizontal. 
   If ``padlen`` is not defined, the length of the paddle itself is defined by table defaults. The ``padwid`` argument defines the thickness of the paddle. 
   Paddles can act as goals if ``hitret`` is set - when a ball contacts the paddle, then :func:`BasicTable.step()` calls will return ``hitret``. 
   If ``active`` is set to ``False``, the paddle cannot be moved. Colors can be set for active paddles (``acol``), inactive paddles (``iacol``), and the background path the paddle can travel (``pthcol``).


Simulating
~~~~~~~~~~~~~~~~~~~~~

.. function:: step(t, maxtime)
   :module: BasicTable
  
   Simulates the table forward by ``t`` seconds. ``t`` defaults to ``1/50.`` and should be evenly slicable into milliseconds to avoid step rounding.
  
   If nothing happens during this step, this returns ``None``. If a ball hits a goal, the function will return the goal's ``onreturn`` value. 
   If ``maxtime`` is given and the table has been running for more than that value (in seconds), this returns the constant ``TIMEUP``.

Drawing
~~~~~~~~~~~~~~~~~~~~

.. function:: draw(stillshow)
   :module: BasicTable

   Draws the table onto the parent surface, and returns a :class:`pygame.Surface` object with just the table drawing on it. If ``stillshow`` is set to ``True``, the balls will be shown through the :class:`objects.Occlusion` objects.

.. function:: demonstrate(screen, timesteps, retpath, onclick, maxtime)
   :module: BasicTable
   
   Simulates the path of the table forward until a ball hits a goal or time expires, then returns the time it took until expiration.
   
   :param screen: A :class:`pygame.Surface` object to draw on
   :param timesteps: The time (in seconds) between animation frames. Defaults to ``1/50.``
   :param onclick: Can take in a function that takes a :class:`BasicTable` as an argument, then calls that function on this table whenever the mouse is clicked (for debugging)
   :param maxtime: The maximum time (in seconds) the demonstration will run without hitting a goal. If not given, will run (potentially) forever.
   
.. function:: makeMovie(moviename, outputdir, fps, removeframes, maxtime)
   :module: BasicTable
   
   *NOTE: requires ffmpeg to function*
   
   Like :func:`demonstrate()`, but makes the demonstration into a movie file.
   
   :param moviename: Name of the movie file
   :param outputdir: The directory to place the movie in (defaults to current directory)
   :param fps: The frames per second to run the movie at (defaults to 20)
   :param removeframes: If set to ``False``, keeps the individual frames around after the movie is created
   :param maxtime: Like :func:`BasicTable.demonstrate()`, the movie will run until a ball hits a goal, or until it has run for ``maxtime`` seconds

Utilities
~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: activate()
   :module: BasicTable
   
   Sets the table to be active, so the :func:`BasicTable.step` command steps the world forward

.. function:: deactivate()
   :module: BasicTable
   
   Sets the table to be inactive, so that the ball does not move when :func:`BasicTable.step` is called (however, paddle positions, etc. will update)

.. function:: mostlyOcc(ball)
   :module: BasicTable
   
   Tests whether a specific :class:`objects.Ball` is at least half covered by an occluder; returns ``True`` if so, ``False`` otherwise

.. function:: mostlyOccAll()
   :module: BasicTable
   
   Returns a list of boolean values asking whether each of the :attr:`BasicTable.balls` is mostly covered.

.. function:: fullyOcc(ball)
   :module: BasicTable
   
   Tests whether a specific :class:`objects.Ball` is completely covered by an occluder; returns ``True`` if so, ``False`` otherwise

.. function:: fullyOccAll()
   :module: BasicTable
      
   Returns a list of boolean values asking whether each of the :attr:`BasicTable.balls` is fully covered.

.. function:: activatePaddle()
   :module: BasicTable
   
.. function:: deactivatePaddle()
   :module: BasicTable
   
.. function:: togglePaddle()
   :module: BasicTable
   
   Set the paddle to active, inactive, or switches its activity
   
.. function:: getRelativeMousePos()
   :module: BasicTable
   
   Returns the mouse position offset from the upper-left-hand corner of the table as an (x,y) tuple.
   
.. function:: assignSurface(surface, offset)
   :module: BasicTable
   
   Reassigns the parent surface to ``surface``, with a given offset
   
.. function:: set_timestep(ts)
   :module: BasicTable
   
   Sets the minimum time between physical simulation steps to ``ts``. This will by default be set to 1ms. Do not change this value lightly: 
   higher values will cause the simulation to run faster, but run the risk of creating wonky, non-physical events if too coarse

   
Object Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attribute:: balls
   :module: BasicTable
   
   Returns a list of :class:`object.Ball` objects attached to the table
   
.. attribute:: walls
   :module: BasicTable
   
   Returns a list of :class:`object.Wall` and :class:`object.AbnormWall` objects attached to the table
   
.. attribute:: occludes
   :module: BasicTable
   
   Returns a list of :class:`object.Occlusion` objects attached to the table
   
.. attribute:: goals
   :module: BasicTable
   
   Returns a list of the :class:`object.Goal` objects attached to the table

.. attribute:: goalrettypes
   :module: BasicTable
   
   Returns a list of the possible values that can be returned when a ball hits a goal on this table. 
   Use the function :func:`physicsTable.Constants.getConst()` to interpret these values.

.. attribute:: paddle
   :module: BasicTable
   
   Returns the :class:`object.Paddle` object on this table if it exists; otherwise, returns ``None``
   
.. _SimpleTable:

SimpleTable
----------------

:class:`SimpleTable` objects are very similar to :class:`BasicTable` objects with one exception: they cannot contain more than one ball. 
All functions are the same as :class:`BasicTable` except where noted below

.. class:: SimpleTable(dims, closed_ends, background_cl, def_ball_rad, def_ball_cl, def_pad_len, def_wall_cl, def_occ_cl, def_pad_cl, active, soffset, defscreen)
   
   Identical to :class:`BasicTable`, but returns a :class:`SimpleTable` instead

.. function:: addBall(initpos, initvel, rad, color, elast, dispwarn)
   :module: SimpleTable
      
   As :func:`BasicTable.addBall` except that if an :class:`objects.Ball` already exists on the table, 
   it will be overwritten. If ``dispwarn`` is set to ``True``, you will be warned in the console if this happens.
   
.. function:: mostlyOcc()
   :module: SimpleTable

.. function:: mostlyOccAll()
   :module: SimpleTable

.. function:: fullyOcc()
   :module: SimpleTable

.. function:: fullyOccAll()
   :module: SimpleTable

   As the same named methods from :class:`BasicTable` except none take arguments and they all return a single boolean representing 
   the occlusion state of the one ball on the :class:`SimpleTable`

.. _noisy_table:

NoisyTable
----------------

:class:`NoisyTable` objects are :class:`SimpleTable` objects that do not unfold deterministically. Instead each ball is placed 
with uncertainty in the position and velocity, and the physics unfolds noisily at each time step and whenever the ball bounces. 
Noise is defined by four parameters:

* ``perr``: When a ball is placed, its location is slightly uncertain, and thus gets displaced from its real value. ``perr`` is the standard deviation of a 2-D Gaussian defining the noise in that position
* ``kapv``: When a ball is placed, its direction of motion is also uncertain. Its velocity thus is drawn from a vonMises distribution centered around the actual direction with concentration parameter ``kapv``
* ``kapm``: At each point in time that the ball's motion can be 'jittered' by redrawing it from a vonMises distribution centered around the current direction with concentration parameter ``kapm``. *NOTE: if the physics timesteps are changed with* :func:`BasicTable.set_timestep`, *the impact of this parameter will change*
* ``kapb``: Whenever the ball hits a wall, it can bounce at an odd angle. Therefore its direction is redrawn from a vonMises distribution centered around the direction it should travel with concentration parameter ``kapv``

See Smith & Vul (2013) for further description of these noise parameters. All parameters default to the values used in that paper

Typically, :class:`NoisyTable` objects are created by "making" a :class:`SimpleTable` noisy through the :func:`makeNoisy` function:

.. function:: makeNoisy(table, kapv, kapb, kapm, perr)

   Takes in a :class:`SimpleTable` and uncertainty parameters and returns a :class:`NoisyTable`. If uncertainty 
   parameters are not given, they default to the values of Smith & Vul (2013)

If constructed de novo, :class:`NoisyTable` objects are created like parent tables

.. class:: NoisyTable(dims, kapv, kapb, kapm, perr, closed_ends, background_cl, def_ball_rad, def_ball_cl, def_pad_len, def_wall_cl, def_occ_cl, def_pad_cl, active, soffset, defscreen)
   
   All parameters are the same as :class:`BasicTable`, with additional parameters as described above.

.. _gravity_table:

GravityTable
----------------

*TO ADD - Not much going on with this type of table yet*