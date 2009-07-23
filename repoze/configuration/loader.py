import inspect
import sys

from yaml import SafeLoader
from pkg_resources import iter_entry_points

class PluginLoader(SafeLoader):
    EP_GROUP = 'repoze.configuration.directive'
    def __init__(self, context, stream, iter_entry_points=iter_entry_points):
        self.context = context
        for point in list(iter_entry_points(self.EP_GROUP)):
            directive = point.load()
            self.add_constructor('!' + point.name, wrap_directive(directive))
        self.add_constructor('tag:yaml.org,2002:str', self.interpolate_str)
        SafeLoader.__init__(self, stream)

    def interpolate_str(self, loader, node):
        value = loader.construct_scalar(node)
        try:
            return self.context.interpolate(value).encode('utf-8')
        except KeyError, why:
            key = why[0]
            exc_info = sys.exc_info()
            msg = ('(Cannot interpolate %%(%s)s while processing lines '
                   '%s:%s-%s:%s of file "%s")' % (
                key,
                node.start_mark.line,
                node.start_mark.column,
                node.end_mark.line,
                node.end_mark.column,
                node.start_mark.name,
                )
            )
            why.args += (msg,)
            raise exc_info[0], why, exc_info[2]
            
def wrap_directive(directive):
    def wrapper(loader, node):
        structure_loader = getattr(loader, 'construct_%s' % node.id)

        if 'deep' in inspect.getargspec(structure_loader)[0]:
            structure = structure_loader(node, deep=True)
        else:
            # scalar structures don't support the 'deep' argument, required
            # for mappings XXX there has to be a better way.
            structure = structure_loader(node)

        context = loader.context

        try:
            infos = directive(context, structure)
        except Exception, why:
            exc_info = sys.exc_info()
            msg = ('(while processing lines %s:%s-%s:%s of file "%s")' % (
                node.start_mark.line,
                node.start_mark.column,
                node.end_mark.line,
                node.end_mark.column,
                node.start_mark.name,
                )
            )
            why.args += (msg,)
            raise exc_info[0], why, exc_info[2]

        if isinstance(infos, dict):
            infos = [infos] # b/c

        if infos is not None:
            for info in infos:
                context.action(info, node)
    wrapper.wrapped = directive
    return wrapper


