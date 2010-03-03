import unittest

class TestInclude(unittest.TestCase):
    def _callFUT(self, declaration):
        from repoze.configuration.directives import include
        return include(declaration)

    def test_bad_structure(self):
        declaration = DummyDeclaration(badstructure=True)
        self.assertRaises(ValueError, self._callFUT, declaration)

    def test_expect_names(self):
        declaration = DummyDeclaration(diff=True)
        self.assertRaises(ValueError, self._callFUT, declaration)
        
    def test_package_not_none_filename_none(self):
        structure = {'package':'here'}
        declaration = DummyDeclaration(structure=structure)
        self._callFUT(declaration)
        self.assertEqual(declaration.context.loaded,
                         ('configure.yml', 'here', False))

    def test_package_not_none_filename_not_none(self):
        structure = {'package':'here', 'filename':'here.yml'}
        declaration = DummyDeclaration(structure=structure)
        self._callFUT(declaration)
        self.assertEqual(declaration.context.loaded,
                         ('here.yml', 'here', False))

    def test_package_none_filename_none(self):
        structure = {}
        declaration = DummyDeclaration(structure=structure)
        self._callFUT(declaration)
        self.assertEqual(
            declaration.context.loaded, ('configure.yml', 'package', False))

    def test_package_none_filename_not_none(self):
        structure = {'filename':'here.yml'}
        declaration = DummyDeclaration(structure=structure)
        self._callFUT(declaration)
        self.assertEqual(declaration.context.loaded,
                         ('here.yml', 'package', False))

    def test_withoverride(self):
        structure = {'filename':'here.yml', 'override':True}
        declaration = DummyDeclaration(structure=structure)
        self._callFUT(declaration)
        self.assertEqual(declaration.context.loaded,
                         ('here.yml', 'package', True))

class DummyDeclaration:
    def __init__(self, **kw):
        self.diff = kw.get('diff', False)
        self.structure = kw.get('structure', {})
        self.badstructure = kw.get('badstructure', False)
        self.context = DummyContext()
        self.__dict__.update(kw)

    def expect(self, typ, names=()):
        if self.badstructure:
            raise ValueError
        if self.diff:
            raise ValueError

    def getvalue(self, name, default=None, pop=False):
        return self.structure.get(name, default)

    string = getvalue

    def resolve(self, dottedname):
        return dottedname

class DummyContext:
    loaded = None
    def current_package(self):
        return 'package'

    def current_override(self):
        return False

    def load(self, filename, package, override):
        self.loaded = (filename, package, override)

