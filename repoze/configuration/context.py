import pkg_resources

from repoze.configuration.loader import PluginLoader

import os

class Context(object):
    def __init__(self, registry):
        self.registry = registry
        self.actions = []
        self.stack = []
        self.discriminators = {}

    def action(self, info, node):
        discriminator = info['discriminator']
        callback = info['callback']
        if self.stack and not self.stack[-1]['override']:
            if discriminator in self.discriminators:
                conflicting_action = self.discriminators[discriminator]
                raise ConfigurationConflict(node, conflicting_action.node)
                
        self.discriminators
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

    def current_override(self):
        if not self.stack:
            return False
        return self.stack[-1]['override']

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

    def load(self, filename, package, override=False):
        stream = self.stream(filename, package)
        self.stack.append({'filename':filename, 'package':package,
                           'override':override})
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

    def call_later(self, func, *arg, **kw):
        def callback():
            return func(*arg, **kw)
        return callback

class Action(object):
    def __init__(self, discriminator, callback, node):
        self.discriminator = discriminator
        self.callback = callback
        self.node = node
        
    def execute(self):
        self.callback()

class ConfigurationConflict(Exception):
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2
        self.msg = str(self)

    def __str__(self):
        message = []
        message.append('Conflicting declarations: ')
        message.append(self._lineinfo(self.node1))
        message.append('conflicts with')
        message.append(self._lineinfo(self.node2))
        return '\n'.join(message)

    def _lineinfo(self, node):
        msg = ('lines %s:%s-%s:%s of file "%s"' % (
            node.start_mark.line,
            node.start_mark.column,
            node.end_mark.line,
            node.end_mark.column,
            node.start_mark.name,
            )
        )
        return msg

