import unittest

class TestInclude(unittest.TestCase):
    def _callFUT(self, context, structure, node):
        from repoze.configuration.directives import include
        return include(context, structure, node)

    def test_bad_structure(self):
        context = DummyContext()
        structure = 'abc'
        node = DummyNode()
        self.assertRaises(ValueError, self._callFUT, context, structure, node)

    def test_diff(self):
        context = DummyContext(['123'])
        structure = {}
        node = DummyNode()
        self.assertRaises(ValueError, self._callFUT, context, structure, node)
        
    def test_package_not_none_filename_none(self):
        context = DummyContext()
        structure = {'package':'here'}
        node = DummyNode()
        self._callFUT(context, structure, node)
        self.assertEqual(context.loaded, ('configure.yml', 'here', False))

    def test_package_not_none_filename_not_none(self):
        context = DummyContext()
        structure = {'package':'here', 'filename':'here.yml'}
        node = DummyNode()
        self._callFUT(context, structure, node)
        self.assertEqual(context.loaded, ('here.yml', 'here', False))

    def test_package_none_filename_none(self):
        context = DummyContext()
        structure = {}
        node = DummyNode()
        self._callFUT(context, structure, node)
        self.assertEqual(context.loaded, ('configure.yml', 'package', False))

    def test_package_none_filename_not_none(self):
        context = DummyContext()
        structure = {'filename':'here.yml'}
        node = DummyNode()
        self._callFUT(context, structure, node)
        self.assertEqual(context.loaded, ('here.yml', 'package', False))

    def test_withoverride(self):
        context = DummyContext()
        structure = {'filename':'here.yml', 'override':True}
        node = DummyNode()
        self._callFUT(context, structure, node)
        self.assertEqual(context.loaded, ('here.yml', 'package', True))

class DummyContext:
    def __init__(self, diff=None):
        if diff is None:
            diff = []
        self.diff = diff
    
    def getvalue(self, structure, name, default=None):
        return structure.get(name, default)

    def diffnames(self, structure, names):
        return self.diff

    def resolve(self, dottedname):
        return dottedname

    def current_package(self):
        return 'package'

    def current_override(self):
        return False

    def load(self, filename, package, override):
        self.loaded = (filename, package, override)

    def error(self, node, msg):
        raise ValueError(node, msg)
    
class DummyNode:
    pass
