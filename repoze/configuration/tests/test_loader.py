import unittest

class TestPluginLoader(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.loader import PluginLoader
        return PluginLoader

    def _makeOne(self, context, stream, iter):
        return self._getTargetClass()(context, stream, iter)

    def test_ctor_load_import_error(self):
        import os
        from repoze.configuration.tests import fixtures
        directory = os.path.dirname(os.path.abspath(fixtures.__file__))
        file = os.path.join(directory, 'configure.yml')
        def directive(context, structure):
            return 'success'
        point = DummyPoint(directive, raise_load_exc=True)
        def iter_entry_points(group, suffix=None):
            yield point
        context = DummyContext()
        loader = self._makeOne(context, open(file), iter_entry_points)
        self.assertEqual(loader.context, context)
        self.failIf('!point' in loader.yaml_constructors) # doesnt blow up

    def test_ctor_ok(self):
        import os
        from repoze.configuration.tests import fixtures
        directory = os.path.dirname(os.path.abspath(fixtures.__file__))
        file = os.path.join(directory, 'configure.yml')
        def directive(context, structure):
            return 'success'
        point = DummyPoint(directive)
        def iter_entry_points(group, suffix=None):
            yield point
        context = DummyContext()
        loader = self._makeOne(context, open(file), iter_entry_points)
        self.assertEqual(loader.context, context)
        self.assertEqual(loader.yaml_constructors['!point'].wrapped, directive)

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
        from yaml.nodes import ScalarNode
        import StringIO
        context = DummyContext(interpolation_exc=True)
        loader = DummyLoader(context)
        node = ScalarNode('foo', 'scalar', DummyMark(), DummyMark())
        f = StringIO.StringIO()
        loader = self._makeOne(context, f, lambda *arg: ())
        self.assertRaises(KeyError, loader.interpolate_str, loader, node)

class Test_wrap_directive(unittest.TestCase):
    def _callFUT(self, point):
        from repoze.configuration.loader import wrap_directive
        return wrap_directive(point)

    def test_directive_returns_list(self):
        directive = DummyDirective([('a', 'b')])
        constructor = self._callFUT(directive)
        node = DummyNode()
        context = DummyContext()
        loader = DummyLoader(context)
        result = constructor(loader, node)
        self.assertEqual(context.actions, [(('a', 'b'), node)] )

    def test_directive_returns_dict(self):
        directive = DummyDirective({'a':'1'})
        constructor = self._callFUT(directive)
        node = DummyNode()
        context = DummyContext()
        loader = DummyLoader(context)
        result = constructor(loader, node)
        self.assertEqual(context.actions, [({'a':'1'}, node)] )

    def test_withexception(self):
        directive = DummyDirective([('a', 'b')], raise_exc=True)
        constructor = self._callFUT(directive)
        node = DummyNode()
        context = DummyContext()
        loader = DummyLoader(context)
        self.assertRaises(KeyError, constructor, loader, node)

    def test_construct_mapping_uses_deep(self):
        directive = DummyDirective({'a':1})
        constructor = self._callFUT(directive)
        node = DummyNode('mapping')
        context = DummyContext()
        loader = DummyLoader(context)
        constructor(loader, node)
        self.assertEqual(context.actions, [({'a':1}, node)] )
        self.assertEqual(loader.deep, True)

class DummyContext:
    def __init__(self, interpolation_exc=False):
        self.actions = []
        self.interpolation_exc = interpolation_exc
    def action(self, info, node):
        self.actions.append((info, node))
    def interpolate(self, value):
        if self.interpolation_exc:
            raise KeyError(value)
        return value
        
class DummyPoint:
    name = 'point'
    def __init__(self, directive, raise_load_exc=False):
        self.directive = directive
        self.raise_load_exc = raise_load_exc

    def load(self):
        if self.raise_load_exc:
            raise ImportError('foo')
        return self.directive

class DummyDirective:
    def __init__(self, result, raise_exc=False):
        self.result = result
        self.raise_exc = raise_exc
        
    def __call__(self, context, structure, node):
        if self.raise_exc:
            raise KeyError('yo')
        return self.result

class DummyLoader:
    def __init__(self, context):
        self.context = context

    def construct_theid(self, node):
        return {}

    def construct_mapping(self, node, deep=False):
        self.deep = deep
        return {}

    def construct_scalar(self, node):
        return 'scalar'

class DummyMark:
    line = 1
    column = 1
    name = 'dummy'
    
class DummyNode:
    def __init__(self, id='theid'):
        self.id = id
        self.start_mark = DummyMark()
        self.end_mark = DummyMark()
        
        
