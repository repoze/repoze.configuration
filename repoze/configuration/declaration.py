import inspect
from repoze.configuration.exceptions import ConfigurationError

_marker = object()

class Declaration(object):
    """ Abstract base class for declaration objects: __init__ only
    supplied for unit tests."""
    def __init__(self, **kw):
        self.__dict__.update(kw)

    @property
    def registry(self): # bw compat shim only
        return self.context

    def expect(self, typ, names=None):
        """ Raise a ConfigurationError if:

        - The type of the declaration structure is not of the same
          type as the object passed as 'typ'.

        - ``names`` is not None and the names provided in the
          ``structure`` don't match the sequence of names supplied as
          ``names``.  This only works when the structure is a mapping
          type.

        Otherwise return None.
        """
        if not isinstance(self.structure, typ):
            self.error(
                'Bad structure for directive (%s instead of %s)' %
                (type(self.structure), typ))

        if names is not None:
            names_provided = set(self.structure.keys())
            diff = names_provided.difference(names)

            if diff:
                self.error('Unknown key(s) in directive: %r' % diff)

    def getvalue(self, name, default=None, types=(), pop=False):
        """
        Return the value corresponding to ``name`` in the structure of
        this declaration.  If the ``types`` value is not empty, and
        the value found is not if a type listed in ``types``, raise a
        configuration error.  If the value does not exist, return the
        default.  If ``pop`` is true, pop the value from the structure
        before returning it.  Return the value.  This method only
        works if the declaration's structure is a mapping type.
        """
        if pop:
            value = self.structure.pop(name, default)
        else:
            value = self.structure.get(name, default)
        if value is default:
            return default
        if types:
            if not isinstance(value, types):
                self.error(
                    '"%s" attribute type is not one of the types %s: %r' % (
                    name, types, value))
        return value

    def boolean(self, name, default=False, pop=False):
        """ Return a boolean value based on the ``name`` passed.  This
        method only works if the declaration's structure is a mapping
        type.

        If ``name`` does not exist in the structure, return ``default``.

        If ``name`` exists in the structure, and is a string or
        unicode type, return a boolean True if the string is any of
        ``('t', 'true', 'yes', 'on', '1')``, otherwise return False.

        If the ``name`` exists in the structure and is not a string or
        unicode type, return Python's bool(value).  If ``pop`` is
        true, pop the value from the structure before returning it."""
        val = self.getvalue(name, default, pop=pop)
        if isinstance(val, basestring):
            if val.lower() in ('t', 'true', 'yes', 'on', '1'):
                return True
            return False
        return bool(val)

    def string(self, name, default=None, pop=False):
        """
        Return the value corresponding to ``name`` in the structure of
        this declaration.  If the value exists and its type is not
        ``basestring``, raise a configuration error.  If the value
        does not exist, return the default.  If ``pop`` is true, pop
        the value from the structure before returning it.  This method
        only works if the declaration's structure is a mapping type.
        """
        return self.getvalue(name, default, types=(basestring,), pop=pop)

    def integer(self, name, default=None, pop=False):
        """
        Return the value corresponding to ``name`` in the structure of
        this declaration.  If the value exists and it cannot be
        converted to a Python integer, raise a configuration error.
        If the value does not exist, return the default.  If ``pop``
        is true, pop the value from the structure before returning it.
        This method only works if the declaration's structure is a
        mapping type.
        """
        value = self.getvalue(name, default, types=(basestring, int), pop=pop)
        if value is default:
            return default
        try:
            return int(value)
        except:
            self.error(
                '%s with value %s cannot be converted to an integer' %
                (name, value))

    def resolve(self, dottedname):
        """ Resolve a setuptools-style dotted name
        (e.g. ``module1.module2:moduelevel_attr``) to a Python object.
        If the name cannot be resolved, a ``ConfigurationError`` is
        raised."""
        try:
            return self.context.resolve(dottedname)
        except ImportError, why:
            self.error(
                str(why) + ' for dotted name %s' % dottedname)

    def error(self, msg):
        """ Raise a ``ConfigurationError`` with the message ``msg`` """
        msg = '%s\n%s' % (msg , self.lineinfo)
        raise ConfigurationError(msg)

    def call_later(self, func, *arg, **kw):
        """ Return a callback accepting no arguments which calls
        ``func`` (any callable) with *arg, **kw when called. """
        def callback():
            return func(*arg, **kw)
        return callback

    def action(self, callback, discriminator=None, override=False):
        """ Insert a deferred processing action.  ``callback`` is a
        callback that accepts no arguments.  ``discriminator`` is any
        hashable value which makes the action unique amongst all other
        actions during processing.  ``override``, if True, means that
        this action should override previous actions during
        processing."""
        return self.context.action(self, callback,
                                   discriminator=discriminator,
                                   override=override)

class YAMLDeclaration(Declaration):
    """
    Instances of this kind of object are passed to a directive.  A
    declaration represents the data parsed from a configuration file.
    It also has helper methods made available for use in directives.

    A declaration always has the following attributes:

    - structure: the Python data structure representing the parsed
      configuration file content.

    - lineinfo: a string representing line (column/row) information for the
      parsed directive content

    - context: a ``repoze.configuration.context.Context`` object
      representing 'global` state for this configuration session
    """
    def __init__(self, context, loader, node):
        self.context = context # required by superclass
        self._loader = loader
        self._node = node
        self._structure = _marker

    @property
    def lineinfo(self):
        return lineinfo(self._node)

    def get_structure(self):
        if self._structure is _marker:
            loader = self._loader
            structure_ctor = getattr(loader, 'construct_%s' % self._node.id)
            # scalar structures don't support the 'deep' argument, required
            # for mappings XXX there has to be a better way.
            if 'deep' in inspect.getargspec(structure_ctor)[0]:
                structure = structure_ctor(self._node, deep=True)
            else:
                structure = structure_ctor(self._node)
            self._structure = structure
        return self._structure

    def set_structure(self, structure):
        self._structure = structure

    structure = property(get_structure, set_structure)

class PythonDeclaration(Declaration):
    lineinfo = ''

    def __init__(self, context, **kw):
        self.context = context
        self.structure = dict(kw)

class ImperativeDeclaration(PythonDeclaration):
    def action(self, callback, discriminator=None, override=False):
        """
        Execute immediately, don't discriminate.
        """
        callback()

def lineinfo(node):
    start_mark = node.start_mark
    end_mark = node.end_mark
    filename = start_mark.name
    try:
        f = open(filename, 'r')
        f.seek(start_mark.index)
        data = f.read(end_mark.index - start_mark.index) + ' in '
    except (OSError, IOError):
        data = ''
    msg = ('%slines %s-%s of file "%s"' % (
        data,
        start_mark.line+1,
        end_mark.line+1,
        start_mark.name,
        )
    )
    return msg
