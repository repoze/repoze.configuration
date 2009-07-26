repoze.configuration README
===========================

``repoze.configuration`` is a package that software developers can use
as a configuration system.  It allows the use of ``YAML`` as a
configuration language.  Application-defined "directives" can be
plugged in to ``repoze.configuration`` using one or more Python
setuptools entry points.  For example, you could make sense out of the
following YAML using repoze.configuration and a custom "appsettings"
directive::

   --- !appsettings
   port_number = 8080
   reload_templates = true

   --- !include
   filename = anotherfile.yml

Please see docs/index.rst or `http://docs.repoze.org/configuration
<http://docs.repoze.org/configuration>`_ for more documentation.
