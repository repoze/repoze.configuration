import pkg_resources

from repoze.configuration.loader import PluginLoader

import os

class Context(object):
    def __init__(self, registry):
        self.registry = registry
        self.actions = []
        self.stack = []

    def action(self, discriminator, callback, node):
        self.actions.append(Action(discriminator, callback, node))

    def resolve(self, dottedname):
        if dottedname.startswith('.') or dottedname.startswith(':'):
            package = self.current_package()
            if not package:
                raise ValueError('name "%s" is irresolveable (no package)' %
                                 dottedname)
            dottedname = package.__name__ + dottedname
        try:
            return pkg_resources.EntryPoint.parse(
                'x=%s' % dottedname).load(False)
        except ImportError, why:
            raise ValueError(
                unicode(why) + ' for derived dotted name %s' % dottedname)

    def current_package(self):
        if not self.stack:
            return None
        return self.stack[-1]['package']

    def stream(self, filename, package=None):
        if os.path.isabs(filename):
            return open(filename)
        if package is None:
            package = self.current_package()
        if package is None:
            return open(filename)
        else:
            return pkg_resources.resource_stream(package.__name__, filename)
        
    def execute(self):
        for action in self.actions:
            action.execute()
        return self.registry

    def load(self, filename, package):
        stream = self.stream(filename, package)
        self.stack.append({'filename':filename, 'package':package})
        try:
            loader = PluginLoader(self, stream)
            while loader.check_data():
                loader.get_data()
        finally:
            self.stack.pop()

    def diffnames(self, provided, expected):
        names_provided = set(provided)
        names_expected = set(expected)
        diff = names_provided.difference(names_expected)
        return list(diff)

    def getvalue(self, structure, name, default=None, type=basestring):
        value = structure.get(name, default)
        if value is default:
            return default
        if not isinstance(value, type):
            raise ValueError('"%s" attribute is not a %s: %r' % (
                name, type.__name__, value))
        return value

class Action(object):
    def __init__(self, discriminator, callback, node):
        self.discriminator = discriminator
        self.callback = callback
        self.node = node
        
    def execute(self):
        self.callback()

