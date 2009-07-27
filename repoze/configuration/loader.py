from yaml import SafeLoader
from pkg_resources import iter_entry_points

from repoze.configuration.exceptions import ConfigurationError
from repoze.configuration.declaration import YAMLDeclaration
from repoze.configuration.declaration import lineinfo

import logging

_marker = object()

class YAMLPluginLoader(SafeLoader):
    EP_GROUP = 'repoze.configuration.directive'
    def __init__(self, context, stream, iter_entry_points=iter_entry_points):
        self.context = context
        for point in list(iter_entry_points(self.EP_GROUP)):
            try:
                directive = point.load()
                if point.name.startswith('tag:'):
                    directive_name = point.name
                else:
                    directive_name = '!' + point.name
                self.add_constructor(directive_name, wrap_directive(directive))
            except ImportError:
                logging.info(
                    'Could not import repoze.configuration.directive '
                    'entry point "%s"' % point)
        self.add_constructor('tag:yaml.org,2002:str', self.interpolate_str)
        SafeLoader.__init__(self, stream)
        while self.check_data():
            self.get_data()

    def interpolate_str(self, loader, node):
        value = loader.construct_scalar(node)
        try:
            value = self.context.interpolate(value)
        except KeyError, why:
            li = lineinfo(node)
            msg = 'Cannot interpolate %%(%s)s found in %s' % (why[0], li)
            raise ConfigurationError(msg)
        return value

def wrap_directive(directive):
    def wrapper(loader, node):
        context = loader.context
        declaration = YAMLDeclaration(context, loader, node)
        directive(declaration)
    wrapper.wrapped = directive
    return wrapper

