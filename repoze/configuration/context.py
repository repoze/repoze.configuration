import os
import pkg_resources
import re

from repoze.configuration.exceptions import ConfigurationConflict
from repoze.configuration.loader import YAMLPluginLoader

_INTERP = re.compile(r"%\(([^)]*)\)s")

class Context(dict):

    def __init__(self, *data, **kw):
        loader = kw.pop('_loader', None)
        if loader is None:
            loader = YAMLPluginLoader
        dict.__init__(self, *data, **kw)
        self.loader = loader
        self.actions = []
        self.stack = []
        self.discriminators = {}

    @property
    def registry(self): # bw compat shim
        return self

    def interpolate(self, value):
        def _interpolation_replace(match):
            s = match.group(1)
            if s in self:
                return self[s]
            if self.stack and s in self.stack[-1]:
                return self.stack[-1][s]
            raise KeyError(s)
        if '%(' in value:
            value = _INTERP.sub(_interpolation_replace, value)
        return value.encode('utf-8')

    def action(self, declaration, callback, discriminator=None, override=False):
        stack_override = self.stack and self.stack[-1]['override']
        effective_override = override or stack_override
        if not effective_override and discriminator is not None:
            if discriminator in self.discriminators:
                conflicting_action = self.discriminators[discriminator]
                raise ConfigurationConflict(declaration,
                                            conflicting_action.declaration)

        action = Action(discriminator, callback, declaration)
        self.actions.append(action)
        if discriminator is not None:
            self.discriminators[discriminator] = action

    def resolve(self, dottedname):
        if dottedname.startswith('.') or dottedname.startswith(':'):
            package = self.current_package()
            if not package:
                raise ImportError('name "%s" is irresolveable (no package)' %
                    dottedname)
            if dottedname in ['.', ':']:
                dottedname = package.__name__
            else:
                dottedname = package.__name__ + dottedname
        return pkg_resources.EntryPoint.parse(
            'x=%s' % dottedname).load(False)

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

    def abs_filename(self, filename, package=None):
        if os.path.isabs(filename):
            return filename
        if package is None:
            package = self.current_package()
        if package is None:
            return os.path.abspath(filename)
        else:
            return pkg_resources.resource_filename(package.__name__, filename)
        
    def load(self, filename, package, override=False, loader=None):
        fn = self.abs_filename(filename, package)
        here = os.path.dirname(fn)
        stream = self.stream(filename, package)
        self.stack.append({'filename':filename, 'package':package,
                           'override':override, 'here':here})
        if loader is None:
            loader = self.loader
        try:
            loader(self, stream)
        finally:
            self.stack.pop()

    def execute(self):
        for action in self.actions:
            action.execute()

class Action(object):
    def __init__(self, discriminator, callback, declaration):
        self.discriminator = discriminator
        self.callback = callback
        self.declaration = declaration
        
    def execute(self):
        if self.callback is not None:
            self.callback()

