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
   :linenos:

   def appsettings(declaration):
       expect_names = ['charset', 'debug_mode']
       declaration.expect(dict, names=expect_names)
       charset = declaration.string('charset', 'utf-8')
       debug_mode = declaration.boolean('debug_mode', False)
       def callback():
           declaration.registry['charset'] = charset
           declaration.registry['debug_mode'] = debug_mode
       declaration.action(callback, discriminator='appsettings')

A :mod:`repoze.configuration` directive must accept a "declaration"
object.  A declaration object represents the configuration file info
that calls a specific directive.  It has the following useful
attributes:

structure

  The Python data structure represented by the declaration The
  structure is data that is parsed from a YAML section in the
  configuration file.  It usually a mapping, but can also be a
  sequence or a scalar.  See the :term:`YAML` documentation for more
  information about allowable types within a YAML "document".

registry

  The configuration registry (a dictionary)

context

  An instance of ``repoze.configuration.context.Context`` representing
  the overall meta-state for this configuration session.

A declaration object also has the useful methods, such as ``action``,
``expect``, ``getvalue``, ``boolean``, ``string``, ``integer``,
``resolve``, ``error``, and ``call_later``.  See
:ref:`declaration_api` for more info.

The return value of a :mod:`repoze.configuration` directive is
ignored.  It is called only for its side effects.

Directives are permitted to do arbitrary things, but to be most
effective, they should defer performing any mutation of data directly.
Instead a directive should inject one or more "actions" using the
``declaration.action`` method.

Using ``declaration.action``
----------------------------

``declaration.action`` receives three values: ``callback``,
``discriminator`` and ``override``.  The ``callback`` value should be
a function which, when called (with no arguments) will actually
perform "the work".  All action callbacks will be called by
:mod:`repoze.configuration` after all directives have been loaded and
called.  A ``callback`` passed to ``declaration.action`` often
populates the ``registry`` dictionary attached to the context.  It is
also assumed that a directive will use the provided
"declaration.context" object as a scratchpad for temporary data if it
needs to collaborate in some advanced way with other directives.  The
context object is not "precious" in any way.

The ``discriminator`` argument to ``declaration.action`` is optional.
It defaults to None (meaning no discriminator is saved for this
action).  If a non-None discriminator is passed to
``declaration.action``, it is used to perform conflict resolution
during deferred callback processing.  If more than one action uses the
same discriminator, an error is thrown at parse time.  In effect, the
discriminator provides actions with cardinality: two actions may not
use the same discriminator without the system detecting a conflict,
and raising an error unless the action is passed a True value for
``override``.

If the ``override`` argument to ``directive.action`` is passed a true
value it means that the directive should override any existing
registration, even if it conflicts with an existing registration.
This is meant to allow you to write directives which, for example,
might contain an optional "override" key like so:

.. code-block: text
   :linenos:

   --- !foo
   override: true

For example:

.. code-block:: python
   :linenos:

   def appsettings(declaration):
       expect_names = ['charset', 'debug_mode']
       declaration.expect(dict, names=expect_names)
       charset = declaration.string('charset', 'utf-8')
       debug_mode = declaration.boolean('debug_mode', False)
       override = declaration.boolean('override', False)
       def callback():
           declaration.registry['charset'] = charset
           declaration.registry['debug_mode'] = debug_mode
       declaration.action(callback, discriminator='appsettings', 
                          override=override)

If you parse the ``override`` value out of the structure and call
``declaration.action`` like so, you can allow users to override
conflicting declarations for your custom directives as necessary.

A directive may also just not call ``declaration.action``.  In this
case no deferred callback is performed.

Registering a Directive
-----------------------

A directive callable is useless unless it's registered as a
``repoze.configuration.directive`` setuptools entry point in some
package's "setup.py" file.  For example, a setup.py for a package that
provides a discriminator might have an "entry_points" argument like
so:

.. code-block:: python
   :linenos:

   def setup(
       ....
       entry_points = """\
       [repoze.configuration.directive]
       appsettings = thispackage.directives:appsettings
       tag:example.com,2009:thispackage/appsettings = thispackage.directives:appsettings
       """
      )

Once the package is installed via ``setup.py install``, this directive
can can be used inside a configuration file via its short name, ala:

.. code-block:: python
   :linenos:

   --- !appsettings
   a: 1
   b: 2

Or it can be referred to by its "tag name", ala:

.. code-block:: python
   :linenos:

   --- !<tag:example.com,2009:thispackage/appsettings>
   a: 1
   b: 2

The tag name should follow the `YAML global tag prefix specification
<http://www.yaml.org/spec/1.2/spec.html#ns-global-tag-prefix>`_, which
will allow it to be aliased to a shorter name via a ``%TAG`` directive
at the top of a YAML file, ala:

.. code-block:: python
   :linenos:

   %TAG !app1! tag:example.com,2009:thispackage/

   --- !app1!appsettings
   a: 1
   b: 2


It's best practice to register both a "short name" and a "tag name"
entry point defintion for a single directive, in case the short name
can't be used by configuration file authors due to conflicts between
short names registered by third-party packages.

Loading Configuration Files That Use Directives
-----------------------------------------------

Something that feeds the directive defined inside the first example in
:ref:`definingdirectives` will be defined inside a YAML config file.
This YAML config file might look like so:

.. code-block:: text
   :linenos:

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
   :linenos:

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
   :linenos:

   --- !listdirective
   - milk
   - bread
   - eggs

Each directive defined should check the "structure" type
(``declaration.structure``) it receives and throw a ``ValueError`` if
the type is incorrect (due to someone mistyping configuration, for
instance).

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
   :linenos:

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
   :linenos:

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
   :linenos:

   >>> # load configuration without a package via an absolute path
   >>> from repoze.configuration import load
   >>> context = load('/path/to/configure.yml')
   >>> registry = context.registry

After using ``load`` you can subsequently execute the directive
actions using the ``execute()`` method of the returned context object.
Using ``repoze.configuration.load``, then an immediately subsequent
``context.execute()`` is exactly equivalent to calling
``repoze.configuration.execute``.
