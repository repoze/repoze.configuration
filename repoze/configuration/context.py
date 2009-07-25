import pkg_resources

from repoze.configuration.loader import PluginLoader

import os
import re
import sys

_KEYCRE = re.compile(r"%\(([^)]*)\)s")

class Context(object):
    def __init__(self, registry):
        self.registry = registry
        self.actions = []
        self.stack = []
        self.discriminators = {}

    def interpolate(self, value):
        def _interpolation_replace(match):
            s = match.group(1)
            return self.registry[s]
        if '%(' in value:
            value = _KEYCRE.sub(_interpolation_replace, value)
        return value

    def action(self, info, node):
        discriminator = info['discriminator']
        callback = info['callback']
        override = info.get('override')
        stack_override = self.stack and self.stack[-1]['override']
        effective_override = override or stack_override
        if not effective_override:
            if discriminator in self.discriminators:
                conflicting_action = self.discriminators[discriminator]
                raise ConfigurationConflict(node, conflicting_action.node)

        action = Action(discriminator, callback, node)
        self.actions.append(action)
        self.discriminators[discriminator] = action

    def resolve(self, dottedname):
        if dottedname.startswith('.') or dottedname.startswith(':'):
            package = self.current_package()
            if not package:
                raise ValueError('name "%s" is irresolveable (no package)' %
                                 dottedname)
            if dottedname in ['.', ':']:
                dottedname = package.__name__
            else:
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

    def popvalue(self, structure, name, default=None, type=basestring):
        value = structure.pop(name, default)
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
        try:
            self.callback()
        except Exception, why:
            exc_info = sys.exc_info()
            msg = 'While executing %s' % lineinfo(self.node)
            why.args += (msg,)
            raise exc_info[0], why, exc_info[2]

class ConfigurationConflict(Exception):
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2
        self.msg = str(self)

    def __str__(self):
        message = []
        message.append('Conflicting declarations:')
        message.append(lineinfo(self.node1))
        message.append('conflicts with')
        message.append(lineinfo(self.node2))
        return '\n\n'.join(message)

def lineinfo(node):
    start_mark = node.start_mark
    end_mark = node.end_mark
    filename = start_mark.name
    try:
        f = open(filename, 'r')
        f.seek(start_mark.index)
        data = f.read(end_mark.index - start_mark.index) + 'in '
    except (OSError, IOError):
        data = ''
    msg = ('%slines %s:%s-%s:%s of file "%s"' % (
        data,
        start_mark.line,
        start_mark.column,
        end_mark.line,
        end_mark.column,
        start_mark.name,
        )
    )
    return msg
