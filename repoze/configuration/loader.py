import sys

from yaml import Loader
from pkg_resources import iter_entry_points

EP_GROUP = 'repoze.configuration.directive'

class PluginLoader(Loader):
    def __init__(self, context, stream):
        self.context = context
        Loader.__init__(self, stream)
        self.add_multi_constructor('!', ep_multi_constructor)

def ep_multi_constructor(loader, suffix, node, iterator=None):
    if iterator is None:
        iterator = iter_entry_points
    points = list(iterator(EP_GROUP, name=suffix))
    if not points:
        raise ValueError('No such plugin directive %s' % suffix)
    if len(points) > 1:
        raise ValueError(
            'Multiple entry points for directive %s: %r' % (suffix, points))
    point = points[0].load()

    structure_loader = getattr(loader, 'construct_%s' % node.id)
    structure = structure_loader(node, deep=True)
    context = loader.context

    try:
        infos = point(context, structure)
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
            
