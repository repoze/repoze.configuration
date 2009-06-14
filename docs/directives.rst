Built-In Directives
===================

:mod:`repoze.configuration` exposes a default directive named
``include``.

.. _include_directive:

The Include Directive
---------------------

:mod:`repoze.configuration` has a built-in directive named "include".
Its usage allows you to include one :mod:`repoze.configuration` YAML
file from within another.

.. code-block:: text

   --- !include
   filename: another.yml
   package: myapplication.subpackage

This directive must resolve to a mapping in the YAML structure.  Two
keys are allowed within this mapping: ``filename`` and ``package``.
``filename`` is a string representing an absolute or relative
filename.  ``package`` is a string representing a Python dotted name
to a package or module.

The ``package`` key is optional when the ``filename`` key is specified
The ``package`` key defaults to the "current" Python package.  The
"current" package is defined as the package in which the YAML file
we're parsing resides.  If we're not parsing a YAML file inside a
package, it defaults to the current working directory.  If the
``package`` key is specified, and its value is a string that starts
with a dot (e.g. ``.foo``), the package is considered relative to the
"current package".

The ``filename`` key is optional when the ``package`` key is
specified.  The ``filename`` key defaults to the string
``configure.yml``.  If the ``filename`` key exists and refers to
absolute pathname, the ``package`` argument is ignored and the file at
the pathname is included into the configuration.  If ``filename`` is
specified, and it's a relative path, it is considered relative to the
"current package" as defined in the paragraph above.

Other legal uses:

.. code-block:: text

   --- !include
   # includes the file in the current package named "another.yml"
   filename = another.yml

   -- !include
   # includes the file in the "anotherpackage" package named "configure.yml"
   package = anotherpackage

   -- !include
   # includes the file in the "anotherpackage" package named "utilities.yml"
   package = anotherpackage
   filename = utilities.yml

   -- !include
   # includes the file at the absolute path "/foo/bar/baz/some.yml"
   filename = /foo/bar/baz/some.yml

.. _include_override:

Include Overrides
~~~~~~~~~~~~~~~~~

The ``include`` directive supports an additional key named
``override``.  Usually if two declarations' discriminators conflict
with each other, a ``ConfigurationConflict`` error will be raised.  If
you include another file using the ``include`` directive and set the
directive's ``override`` key to true, any declaration made within the
included file will override any previously made declaration with the
same discriminator.  For example:

.. code-block:: text

   -- !include
   # includes the file at the absolute path "/foo/bar/baz/some.yml"
   # overriding any previous declarations
   filename = /foo/bar/baz/some.yml
   override = true

