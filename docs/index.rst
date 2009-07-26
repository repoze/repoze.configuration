Documentation for repoze.configuration
======================================

Introduction
------------

:mod:`repoze.configuration` is a package that software developers can
use as a configuration system.  It allows the use of :term:`YAML` as a
configuration language.  Application-defined "directives" can be
plugged in to it one or more Python setuptools entry points.  For
example, you could make sense out of the following YAML using
repoze.configuration and a custom directive:

.. code-block:: text

   --- !appsettings
   port_number = 8080
   reload_templates = true

   --- !include
   filename = anotherfile.yml

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   config
   directives
   interpolation
   api
   glossary

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
