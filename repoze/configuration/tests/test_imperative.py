import unittest

class TestImperativeConfig(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.imperative import ImperativeConfig
        return ImperativeConfig

    def _makeOne(self, context, iter):
        return self._getTargetClass()(context, iter)

    def test_ctor(self):
        directive = DummyDirective()
        ep = DummyPoint(directive)
        def dummy_iter(group):
            yield ep

        config = self._makeOne(None, dummy_iter)
        self.failUnless(hasattr(config, 'point'))
        self.assertEqual(config.context['config'], config)

    def test_import_error(self):
        directive = DummyDirective()
        ep = DummyPoint(directive, raise_load_exc=True)
        def dummy_iter(group):
            yield ep

        config = self._makeOne(object(), dummy_iter)
        self.failIf(hasattr(config, 'point'))

    def test_call_directive(self):
        directive = DummyDirective()
        ep = DummyPoint(directive)
        def dummy_iter(group):
            yield ep

        config = self._makeOne(object(), dummy_iter)
        config.point(foo='foo', bar='baz')
        self.assertEqual(directive.declaration.structure,
                         {'foo': 'foo', 'bar': 'baz'})

    def test_ambiguous_directive(self):
        directive = DummyDirective()
        ep = DummyPoint(directive)
        def dummy_iter(group):
            yield ep
            yield ep

        config = self._makeOne(object(), dummy_iter)
        self.assertRaises(AttributeError, config.point)

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
    def __call__(self, declaration):
        self.declaration = declaration

