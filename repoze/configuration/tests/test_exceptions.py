import unittest

class TestConfigurationConflict(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.exceptions import ConfigurationConflict
        return ConfigurationConflict

    def _makeOne(self, node1, node2):
        error = self._getTargetClass()(node1, node2)
        return error

    def test_ctor(self):
        declaration1 = DummyDeclaration()
        declaration2 = DummyDeclaration()
        error = self._makeOne(declaration1, declaration2)
        self.assertEqual(error.declaration1, declaration1)
        self.assertEqual(error.declaration2, declaration2)
        lines = error.msg.split('\n')
        self.assertEqual(len(lines), 7)
        self.assertEqual(lines[0], 'Conflicting declarations:')
        self.assertEqual(lines[1], '')
        self.assertEqual(lines[2], 'lineinfo')
        self.assertEqual(lines[3], '')
        self.assertEqual(lines[4], 'conflicts with')
        self.assertEqual(lines[5], '')
        self.assertEqual(lines[6], 'lineinfo')


class DummyDeclaration(object):
    lineinfo = 'lineinfo'
    
