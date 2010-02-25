import unittest

class TestLoad(unittest.TestCase):
    def _callFUT(self, filename, package, context):
        from repoze.configuration import load
        return load(filename, package, context)

    def test_no_context(self):
        from repoze.configuration.tests import fixtures
        context = self._callFUT('configure.yml', fixtures, None)
        self.assertEqual(context, {})

    def test_with_context(self):
        context = DummyContext()
        result = self._callFUT('configure.yml', None, context)
        self.assertEqual(result, context)
        self.failUnless(result.loaded, ('configure.yml', None))

class TestExecute(unittest.TestCase):
    def _callFUT(self, filename, package, context):
        from repoze.configuration import execute
        return execute(filename, package, context)

    def test_no_context(self):
        from repoze.configuration.tests import fixtures
        context = self._callFUT('configure.yml', fixtures, None)
        self.assertEqual(context, {})

    def test_with_context(self):
        context = DummyContext()
        result = self._callFUT('configure.yml', None, context)
        self.assertEqual(result, context)
        self.failUnless(result.loaded, ('configure.yml', None))
        self.failUnless(result.executed)

class DummyContext:
    def load(self, filename, package):
        self.loaded = (filename, package)

    def execute(self):
        self.executed = True
        
