from repoze.configuration.exceptions import ConfigurationError # API
from repoze.configuration.exceptions import ConfigurationConflict # API
from repoze.configuration.context import Context # API

def load(filename='configure.yml', package=None, context=None, loader=None):
    """
    You can load configuration without executing it (without calling
    any callbacks) by using the ``load`` function.  ``load`` accepts a
    filename argument and a package argument.  The ``package``
    argument is optional.  If it is not specified, the filename is
    found in the current working directory.

    .. code-block:: python
       :linenos:

       >>> # load configuration without a package via an absolute path
       >>> from repoze.configuration import load
       >>> context = load('/path/to/configure.yml')
       >>> registry = context.registry

    After using ``load`` you can subsequently execute the directive
    actions using the ``execute()`` method of the returned context
    object.  Using ``repoze.configuration.load``, then an immediately
    subsequent ``context.execute()`` is exactly equivalent to calling
    ``repoze.configuration.execute``.

    See the ``execute`` documentation for the meanings of the
    arguments passed to this function.
    """
    if context is None:
        registry = {}
        context = Context(registry, loader)
    context.load(filename, package)
    return context

def execute(filename='configure.yml', package=None, context=None, loader=None):
    """
    ``execute`` loads the configuration, executes the actions
    implied by the configuration, and returns a context.  After
    successful execution, you can access the populated registry
    dictionary by referring to the context's ``registry`` attribute:

    ``execute`` accepts a ``filename`` argument and a ``package``
    argument.  The ``package`` argument is optional.  If it is not
    specified, the filename is found in the current working directory.

    For example:

    .. code-block:: python
       :linenos:

       >>> # load configuration without a package via an absolute path
       >>> from repoze.configuration import execute
       >>> context = execute('/path/to/configure.yml')
       >>> registry = context.registry

       >>> # load configuration from the 'configure.yml' file within 'somepackage'
       >>> from repoze.configuration import load
       >>> import somepackage
       >>> context = execute('configure.yml', package=somepackge)
       >>> registry = context.registry
    """
    context = load(filename, package, context, loader)
    context.execute()
    return context

    
        


    


