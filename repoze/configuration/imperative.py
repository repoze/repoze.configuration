import logging
from pkg_resources import iter_entry_points

from repoze.configuration.context import Context
from repoze.configuration.declaration import ImperativeDeclaration

_ambiguous = object()

class ImperativeConfig(object):
    """
    Can be used standalone or as a mixin, providing access to any discoverable
    configuration directives as API methods.
    """
    EP_GROUP = 'repoze.configuration.directive'
    CONFIG_ATTR = 'config'
    Declaration = ImperativeDeclaration
    Context = Context

    def __init__(self, context=None,
                 iter_entry_points=iter_entry_points # override for testing
                 ):
        if context is None:
            context = self.Context(**{self.CONFIG_ATTR: self})
        self.context = context
        self.directives = directives = {}

        for point in list(iter_entry_points(self.EP_GROUP)):
            try:
                directive = point.load()
                name = point.name
                if name in directives:
                    logging.warn(
                        "Directive name declared more than once: %s.  " % name
                    )
                    directives[name] = _ambiguous # force explicitness
                else:
                    directives[name] = directive

            except ImportError:
                logging.info(
                    'Could not import repoze.configuration.directive '
                    'entry point "%s"' % point)

    def __getattr__(self, name):
        directive = self.directives.get(name, None)
        if directive is None:
            raise AttributeError(name)

        if directive is _ambiguous:
            def ambiguous(**kw):
                raise AttributeError(
                    "More than one directive uses name: %s" % name
                )
            return ambiguous

        def wrapper(**kw):
            declaration = self.Declaration(self.context, **kw)
            directive(declaration)

        return wrapper
