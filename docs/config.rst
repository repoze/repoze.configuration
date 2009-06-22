Using the :mod:`repoze.configuration` Configuration System
==========================================================

:mod:`repoze.configuration` comes with a configuration system that
makes it possible to populate a dictionary and perform other arbitrary
actions by loading a configuration file.  The configuration file
format is :term:`YAML`.  Each "document" (a section that begins with
the marker "---') in the YAML file represents one call to a
:mod:`repoze.configuration` :term:`directive`.

.. _definingdirectives:

Defining Directives
-------------------

A :term:`directive` is a callable object that is registered as a
setuptools entry point.  Here's an example directive:

.. code-block:: python

   def boolean(val):
       if isinstance(val, basestring):
           if val.lower() in ('t', 'true', 'yes', 'on'):
               return True
       return bool(val)

   def appsettings(context, structure):
       if not isinstance(structure, dict):
            raise ValueError('"appsettings" section must be a mapping in YAML')
       charset = structure.get('charset', 'utf-8')
       debug_mode = boolean(structure.get('debug_mode', None))
       def callback():
           context.registry['charset'] = charset
           contex.registry['debug_mode'] = debug_mode
       discriminator = 'appsettings'
       return [ {'discriminator':discriminator, 'callback':callback} ]

A :mod:`repoze.configuration` directive must accept a "context" object
(a :mod:`repoze-plugin` ``repoze.configuration.Context`` instance,
which by default happens to have a dictionary as its ``registry``
attribute) and a "structure".  The structure is data that is parsed
from a YAML section in the configuration file.  It usually a mapping,
but can also be a sequence or a scalar.  See the :term:`YAML`
documentation for more information about allowable types within a YAML
"document".

A :mod:`repoze.configuration` directive must return either a single
dictionary, a sequence of dictionaries or ``None``.  If the directive
returns a dictionary, it must contain the keys ``discriminator`` and
``callback``.  If the directive returns a sequence, the sequence must
consist entirely of dictionaries and each dictionary in the sequence
must contain the keys ``discriminator`` and ``callback``

Directives are permitted to do arbitrary things, but to be most
effective, they should defer performing any mutation of data by
returning a set of callbacks (the ``callback`` value within each
dictionary returned by the directive) which actually perform "the
work".  These callbacks will be called by :mod:`repoze.configuration`
after all directives have been loaded and called.

Each ``callback`` within the the dictionaries returned from a
:mod:`repoze.configuration` direcive often populates the ``registry``
dictionary attached to the context.  It is also assumed that a
directive will use the provided "context" object as a scratchpad for
temporary data if it needs to collaborate in some advanced way with
other directives.  The context object is not "precious" in any way.

The ``discriminator`` value within a dictionary in the sequence that a
directive returns is used to perform conflict resolution during
deferred callback processing.  If more than one dictionary contains
the same discriminator, an error is thrown at parse time.  In effect,
the discriminator provides directives with cardinality: two directives
may not return the same discriminator without the system detecting a
conflict, and raising an error unless the directive is an override
(see :ref:`include_override`).

A directive may also return ``None``, in which case no deferred
callback is performed, nor is a discriminator registered for the
directive.

Registering a Directive
-----------------------

A directive callable is useless unless it's registered as a
``repoze.configuration.directive`` setuptools entry point in some
package's "setup.py" file.  For example, a setup.py for a package that
provides a discriminator might have an "entry_points" argument like
so:

.. code-block:: python

   def setup(
       ....
       entry_points = """\
       [repoze.configuration.directive]
       appsettings = thispackage.directives:appsettings
       """
      )

Once the package is installed via ``setup.py install``, this directive
can can be used inside a configuration file.

Loading Configuration Files That Use Directives
-----------------------------------------------

Something that feeds the directive defined inside the first example in
:ref:`definingdirectives` will be defined inside a YAML config file.
This YAML config file might look like so:

.. code-block:: text

   --- !appsettings
   charset: utf-8
   debug_mode: true

When this configuration file is loaded, the ``!appsettings`` following
the ``---`` in the YAML file is interpreted by the
:mod:`repoze.configuration` YAML loader to mean that it should look for a
setuptools entry point in the group ``repoze.configuration.directive`` named
``appsettings`` (via the ``pkg_resources`` API).  If it finds such an
entry point, the function it refers to is loaded and called.  If it
does not find such an entry point, an error is raised.  If it finds
more than one entry point in the ``repoze.configuration.directive`` group
with the same name, an error is raised.  

In the above example, the registry dictionary will eventually be
populated with two key-value pairs: ``charset`` will be set to the
string ``utf-8`` and ``debug_mode`` will be set to the boolean
``True`` value.

A configuration file can contain many calls to the same directive (at
least if the directive's discriminators don't conflict), and calls to
as many directives as necessary, e.g.:

.. code-block:: text

   --- !somedirective
   a = 1
   n = 2

   --- !somedirective
   b = 2
   c = 3

   --- !anotherdirective
   c = 3
   f = 6

The use of YAML implies structuring.  The YAML type expected by each
directive can be chosen arbitrarily.  For example, the "structure"
provided to the following "!listdirective" will be a list.

.. code-block:: text

   --- !listdirective
   - milk
   - bread
   - eggs

Each directive defined should check the "structure" type it receives
and throw a ``ValueError`` if the type is incorrect (due to someone
mistyping configuration, for instance).

If a file cannot be recognized as valid YAML at all at load time, an
error is thrown before any directives are called.

Using the ``load`` and ``execute`` commands
-------------------------------------------

You use the :mod:`repoze.configuration` configuration file loader functions
to load and execute configuration.

Using ``repoze.configuration.execute``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``execute`` accepts a filename argument and a package argument.  The
``package`` argument is optional.  If it is not specified, the
filename is found in the current working directory.

.. code-block:: python

   >>> # load configuration without a package via an absolute path
   >>> from repoze.configuration import execute
   >>> context = execute('/path/to/configure.yml')

   >>> # load configuration from the 'configure.yml' file within 'somepackage'
   >>> from repoze.configuration import load
   >>> import somepackage
   >>> context = execute('configure.yml', package=somepackge)

``execute`` loads the configuration, executes the actions implied by
the configuration, and returns a context.  You can access the fully
populated registry dictionary by referring to the context's
``registry`` attribute:

.. code-block:: python

   >>> # load configuration without a package via an absolute path
   >>> from repoze.configuration import load
   >>> context = execute('/path/to/configure.yml')
   >>> registry = context.registry

You can then use the registry dictionary within your application.

Using ``repoze.configuration.load``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can load configuration without executing it (without calling any
callbacks) by using the ``load`` command instead of the ``execute``
command.  ``load`` accepts a filename argument and a package argument.
The ``package`` argument is optional.  If it is not specified, the
filename is found in the current working directory.


.. code-block:: python

   >>> # load configuration without a package via an absolute path
   >>> from repoze.configuration import load
   >>> context = load('/path/to/configure.yml')
   >>> registry = context.registry

After using ``load`` you can subsequently execute the directive
actions using the ``execute()`` method of the returned context object.
Using ``repoze.configuration.load``, then an immediately subsequent
``context.execute()`` is exactly equivalent to calling
``repoze.configuration.execute``.
