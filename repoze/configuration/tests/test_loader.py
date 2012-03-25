import unittest

class TestYAMLPluginLoader(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.loader import YAMLPluginLoader
        return YAMLPluginLoader

    def _makeOne(self, context, stream, iter):
        return self._getTargetClass()(context, stream, iter)

    def test_ctor_load_import_error(self):
        import os
        from repoze.configuration.tests import fixtures
        directory = os.path.dirname(os.path.abspath(fixtures.__file__))
        file = os.path.join(directory, 'configure.yml')
        def include(declaration): return 'success'
        inc_point = DummyPoint(include)
        inc_point.name = 'include'
        def directive(context, structure): return 'success'
        point = DummyPoint(directive, raise_load_exc=True)
        def iter_entry_points(group, suffix=None):
            yield inc_point
            yield point
        context = DummyContext()
        loader = self._makeOne(context, open(file), iter_entry_points)
        self.assertEqual(loader.context, context)
        self.failIf('!point' in loader.yaml_constructors) # doesnt blow up

    def test_ctor_shortname(self):
        import os
        from repoze.configuration.tests import fixtures
        directory = os.path.dirname(os.path.abspath(fixtures.__file__))
        file = os.path.join(directory, 'configure.yml')
        def include(declaration): return 'success'
        inc_point = DummyPoint(include)
        inc_point.name = 'include'
        def directive(context, structure): return 'success'
        point = DummyPoint(directive)
        def iter_entry_points(group, suffix=None):
            yield inc_point
            yield point
        context = DummyContext()
        loader = self._makeOne(context, open(file), iter_entry_points)
        self.assertEqual(loader.context, context)
        self.assertEqual(loader.yaml_constructors['!point'].wrapped, directive)

    def test_ctor_tagname(self):
        import os
        from repoze.configuration.tests import fixtures
        directory = os.path.dirname(os.path.abspath(fixtures.__file__))
        file = os.path.join(directory, 'configure.yml')
        def include(declaration): return 'success'
        inc_point = DummyPoint(include)
        inc_point.name = 'include'
        def directive(context, structure): return 'success'
        point = DummyPoint(directive)
        point.name = 'tag:point'
        def iter_entry_points(group, suffix=None):
            yield inc_point
            yield point
        context = DummyContext()
        loader = self._makeOne(context, open(file), iter_entry_points)
        self.assertEqual(loader.context, context)
        self.assertEqual(loader.yaml_constructors['tag:point'].wrapped,
                         directive)

    def test_interpolate_str(self):
        from yaml.nodes import ScalarNode
        import StringIO
        context = DummyContext()
        loader = DummyLoader(context)
        node = ScalarNode('foo', 'scalar')
        f = StringIO.StringIO()
        loader = self._makeOne(context, f, lambda *arg: ())
        self.assertEqual(loader.interpolate_str(loader, node), 'scalar')
        
    def test_interpolate_str_exc(self):
        from repoze.configuration.exceptions import ConfigurationError
        from yaml.nodes import ScalarNode
        import StringIO
        context = DummyContext(interpolation_exc=True)
        loader = DummyLoader(context)
        node = ScalarNode('foo', 'scalar', DummyMark(), DummyMark())
        f = StringIO.StringIO()
        loader = self._makeOne(context, f, lambda *arg: ())
        self.assertRaises(ConfigurationError,
                          loader.interpolate_str, loader, node)

class Test_wrap_directive(unittest.TestCase):
    def _callFUT(self, directive):
        from repoze.configuration.loader import wrap_directive
        return wrap_directive(directive)

    def test_it(self):
        directive = DummyDirective()
        wrapper = self._callFUT(directive)
        self.assertEqual(wrapper.wrapped, directive)
        loader = DummyLoader(None)
        wrapper(loader, None)
        self.assertEqual(directive.declaration.context, loader.context)
        self.assertEqual(directive.declaration._loader, loader)
        self.assertEqual(directive.declaration._node, None)

class DummyLoader:
    def __init__(self, context):
        self.context = context

class DummyContext:
    def __init__(self, interpolation_exc=False):
        self.actions = []
        self.interpolation_exc = interpolation_exc

    def interpolate(self, value):
        if self.interpolation_exc:
            raise KeyError(value)
        return value

    def load(self, filename, package=None, override=False):
        self.loaded = (filename, package, override)

    def current_package(self):
        return None

    def current_override(self):
        return False
        
class DummyPoint:
    name = 'point'
    def __init__(self, directive, raise_load_exc=False):
        self.directive = directive
        self.raise_load_exc = raise_load_exc

    def load(self):
        if self.raise_load_exc:
            raise ImportError('foo')
        return self.directive

class DummyMark:
    line = 1
    column = 1
    name = 'dummy'
    
class DummyDirective:
    def __call__(self, declaration):
        self.declaration = declaration
        
