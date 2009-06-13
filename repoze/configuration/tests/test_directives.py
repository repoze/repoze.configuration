import unittest

class TestInclude(unittest.TestCase):
    def _callFUT(self, context, structure):
        from repoze.configuration.directives import include
        return include(context, structure)

    def test_bad_structure(self):
        context = DummyContext()
        structure = 'abc'
        self.assertRaises(ValueError, self._callFUT, context, structure)

    def test_diff(self):
        context = DummyContext(['123'])
        structure = {}
        self.assertRaises(ValueError, self._callFUT, context, structure)
        
    def test_package_not_none_filename_none(self):
        context = DummyContext()
        structure = {'package':'here'}
        self._callFUT(context, structure)
        self.assertEqual(context.loaded, ('configure.yml', 'here', False))

    def test_package_not_none_filename_not_none(self):
        context = DummyContext()
        structure = {'package':'here', 'filename':'here.yml'}
        self._callFUT(context, structure)
        self.assertEqual(context.loaded, ('here.yml', 'here', False))

    def test_package_none_filename_none(self):
        context = DummyContext()
        structure = {}
        self._callFUT(context, structure)
        self.assertEqual(context.loaded, ('configure.yml', 'package', False))

    def test_package_none_filename_not_none(self):
        context = DummyContext()
        structure = {'filename':'here.yml'}
        self._callFUT(context, structure)
        self.assertEqual(context.loaded, ('here.yml', 'package', False))

    def test_withoverride(self):
        context = DummyContext()
        structure = {'filename':'here.yml', 'override':True}
        self._callFUT(context, structure)
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
        
    
