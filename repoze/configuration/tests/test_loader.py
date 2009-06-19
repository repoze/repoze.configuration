import unittest

class TestPluginLoader(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.loader import PluginLoader
        return PluginLoader

    def _makeOne(self, context, stream):
        return self._getTargetClass()(context, stream)

    def test_ctor(self):
        import os
        from repoze.configuration.tests import fixtures
        directory = os.path.dirname(os.path.abspath(fixtures.__file__))
        file = os.path.join(directory, 'configure.yml')
        loader = self._makeOne(None, open(file))
        # doesnt blow up

class Test_ep_multi_constructor(unittest.TestCase):
    def _callFUT(self, loader, suffix, node, iterator=None):
        from repoze.configuration.loader import ep_multi_constructor
        return ep_multi_constructor(loader, suffix, node, iterator)

    def test_no_points(self):
        self.assertRaises(ValueError, self._callFUT, None, 'notexist', None)

    def test_too_many_points(self):
        def iterator(group, name=None):
            return [1,2,3]
        self.assertRaises(ValueError, self._callFUT, None, 'notexist', None,
                          iterator=iterator)

    def test_directive_returns_list(self):
        point = DummyPoint([('a', 'b')])
        def iterator(group, name=None):
            return [point]
        node = DummyNode()
        context = DummyContext()
        loader = DummyLoader(context)
        self._callFUT(loader, 'whatever', node, iterator)
        self.assertEqual(context.actions, [(('a', 'b'), node)] )

    def test_directive_returns_dict(self):
        point = DummyPoint({'a':1})
        def iterator(group, name=None):
            return [point]
        node = DummyNode()
        context = DummyContext()
        loader = DummyLoader(context)
        self._callFUT(loader, 'whatever', node, iterator)
        self.assertEqual(context.actions, [({'a':1}, node)] )

    def test_withexception(self):
        point = DummyPoint([('a', 'b')], raise_exc=True)
        def iterator(group, name=None):
            return [point]
        node = DummyNode()
        context = DummyContext()
        loader = DummyLoader(context)
        self.assertRaises(KeyError, self._callFUT, loader, 'whatever',
                          node, iterator)

class DummyContext:
    def __init__(self):
        self.actions = []
    def action(self, info, node):
        self.actions.append((info, node))
        
class DummyPoint:
    def __init__(self, result, raise_exc=False):
        self.result = result
        self.raise_exc = raise_exc

    def load(self):
        return self

    def __call__(self, context, structure):
        if self.raise_exc:
            raise KeyError('yo')
        return self.result

class DummyLoader:
    def __init__(self, context):
        self.context = context
    def construct_theid(self, node, deep=True):
        return {}

class DummyMark:
    line = 1
    column = 1
    name = 'dummy'
    
class DummyNode:
    id = 'theid'
    def __init__(self):
        self.start_mark = DummyMark()
        self.end_mark = DummyMark()
        
        
