Repy
====

Repy is a turing-complete subset of Python that allows to run in a sandboxed environment.

Python and Repy
---------------

The Python programming language is documented at `docs.python.org/reference <http://docs.python.org/reference/index.html>`_.
Repy is a reduced version of the Python programming language that allows to run scripts in a sandboxed environment. Repy is part of the `Seattle Testbed <http://seattle.cs.washington.edu>`_ and has an `extensive documentation <http://seattle.cs.washington.edu/wiki/ProgrammersPage>`_ in the Seattle Wiki.

Difference between Repy and Python
----------------------------------

* No imports, no external libraries. The ``import`` statement is forbidden in Repy.
  Some functionality from Python libraries is made available via special identifiers. (see below)
* No ``global`` variables. Instead Repy has a dictionary ``mycontext`` that can be used to store global variables.
* No user input via ``input`` or ``raw_input``.
* Some Python builtins are not available. The most important are
   * ``print``
   * ``eval`` and ``execfile``
   * ``lambda``
   * ``reload``
   * ``reversed`` and ``sorted``
   * ``staticmethod``
   * ``super``
   * ``unicode``
   * ``yield``
   * ``hasattr``, ``getattr`` and ``setattr``
* Parameters are passed as ``callargs`` instead of ``sys.argv`` and start with index 0 instead of 1 (``sys.argv[0]`` is the script itself).


Methods available to Repy scripts
---------------------------------

Output methods
**************
.. py:function:: echo(message)

   will print the message (followed by a newline) to the console.

.. py:function:: print_exc(exception)
 
   will print an exception and a stack trace to the console.


Threading/Locking methods
*************************
.. py:function:: createlock()

.. py:function:: getthreadname()

.. py:function:: createthread()


Misc. methods
*************

.. py:function:: exitall()

.. py:function:: sleep(time)

.. py:function:: randombytes()

.. py:function:: getruntime()

.. py:function:: getlasterror()


Networking methods
******************

.. py:function:: tuntap_read(dev, timeout=None)

   will read one packet from the given network device `dev` and return this packet as a byte string.
   The method will block until a packet arrives at the device but at most `timeout` seconds (forever if `timeout=None`). If no packet has been received before the timeout, `None` will be returned.
   It is an error if the device does not exist.

   
.. py:function:: tuntap_read_any(timeout=None)

   will read one packet from any network device and return it.
   The return value will be a tuple `(dev, packet)` of the incoming device and the packet as a byte string. 
   The first packet that arrives at a network device will be returned.
   The method will block until a packet arrives at a device but at most `timeout` seconds (forever if `timeout=None`). If no packet has been received before the timeout, `(None, None)` will be returned.
   It is an error to call this method if no network devices exist.

   
.. py:function:: tuntap_send(dev, data)

   will send the packet `data` via the network device `dev`. The packet must be a byte string.
   It is an error if the device does not exist.

   
.. py:function:: tuntap_list()

   will return a list of all available network devices.

   
.. py:function:: tuntap_info(dev)

   will return a dictionary containing detailed information about the networking device `dev`.

Struct
******

The `struct library <http://docs.python.org/library/struct.html>`_ is available via `struct` (no import needed). This library can be used to encode and decode binary data structures.


ToMaTo library
--------------

The `tomato library <http://github.com/dswd/ToMaTo/tree/master/repy/tomatolib>`_ contains implementations of protocols and nodes. This library is extensible, so please feel free to contribute.