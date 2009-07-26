.. _interpolation:

Interpolation
=============

Scalar values (strings) in :mod:`repoze.configuration` directives can
include interpolation markers.  Interpolation markers are in the
Python interpolation form ``%(replaceme)s``.  Interpolation expands
values by attempting to resolve the name being replaced by treating
the registry of the configuration context as a dictionary.

If the registry of the context does not have the name, a few built-in
names are tried:

here

  The directory in which the configuration file lives.

For example, the value %(here)s will be interpolated as necessary in
the following repoze.configuration config file:

.. code-block:: python
   :linenos:

   --- !mydirective
   filename: %(here)s/etc/named.conf

If the filename of the above configuration file was
"/etc/mydirectives.yml", the value that ``%(here)s`` would be expanded
to would be ``/etc``.
