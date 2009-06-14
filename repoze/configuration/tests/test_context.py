import unittest

class TestContext(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration import Context
        return Context

    def _makeOne(self, registry=None):
        if registry is None:
            registry = {}
        return self._getTargetClass()(registry)

    def test_ctor(self):
        registry = {}
        context = self._makeOne(registry)
        self.assertEqual(context.registry, registry)
        self.assertEqual(context.stack, [])
        self.assertEqual(context.actions, [])

    def test_action(self):
        context = self._makeOne()
        context.action({'discriminator':'discriminator',
                        'callback':'callback'}, 'node')
        self.assertEqual(len(context.actions), 1)
        action = context.actions[0]
        self.assertEqual(action.discriminator, 'discriminator')
        self.assertEqual(action.callback, 'callback')
        self.assertEqual(action.node, 'node')

    def test_action_withconflict(self):
        from repoze.configuration.context import ConfigurationConflict
        context = self._makeOne()
        context.discriminators['discriminator'] = DummyAction()
        context.stack = [{'override':False}]
        self.assertRaises(ConfigurationConflict,
                          context.action,
                          {'discriminator':'discriminator',
                           'callback':'callback'},
                          DummyNode())

    def test_resolve_absolute(self):
        from repoze.configuration.tests.fixtures import fixturefunc
        context = self._makeOne()
        result = context.resolve(
            'repoze.configuration.tests.fixtures:fixturefunc')
        self.assertEqual(result, fixturefunc)
        
    def test_irrresolveable_absolute(self):
        context = self._makeOne()
        self.assertRaises(ValueError, context.resolve,
            'repoze.configuration.tests.fixtures:nonexisting')

    def test_resolve_relative_startswith_colon(self):
        from repoze.configuration.tests import fixtures
        from repoze.configuration.tests.fixtures import fixturefunc
        context = self._makeOne()
        context.stack.append({'package':fixtures})
        result = context.resolve(':fixturefunc')
        self.assertEqual(result, fixturefunc)

    def test_resolve_relative_startswith_dor(self):
        from repoze.configuration import tests
        from repoze.configuration.tests.fixtures import fixturefunc
        context = self._makeOne()
        context.stack.append({'package':tests})
        result = context.resolve('.fixtures:fixturefunc')
        self.assertEqual(result, fixturefunc)
        
    def test_resolve_relative_nocurrentpackage(self):
        context = self._makeOne()
        self.assertRaises(ValueError, context.resolve, '.fixturefunc')

    def test_irrresolveable_relative(self):
        from repoze.configuration.tests import fixtures
        context = self._makeOne()
        context.stack.append({'package':fixtures})
        self.assertRaises(ValueError, context.resolve, ':notexisting')

    def test_current_package_nostack(self):
        context = self._makeOne()
        self.assertEqual(context.current_package(), None)

    def test_current_package_withstack(self):
        context = self._makeOne()
        context.stack.append({'package':'abc'})
        self.assertEqual(context.current_package(), 'abc')

    def test_current_override_nostack(self):
        context = self._makeOne()
        self.assertEqual(context.current_override(), False)

    def test_current_override_withstack(self):
        context = self._makeOne()
        context.stack.append({'override':True})
        self.assertEqual(context.current_override(), True)
        
    def test_stream_absolute(self):
        import os
        from repoze.configuration.tests import fixtures
        filename = os.path.join(os.path.dirname(
            os.path.abspath(fixtures.__file__)), '__init__.py')
        context = self._makeOne()
        stream = context.stream(filename)
        self.assertEqual(stream.read(), open(filename).read())

    def test_path_nopackage_nocurrentpackage(self):
        import os
        from repoze.configuration.tests import fixtures
        old_cwd = os.getcwd()
        fixtures = os.path.dirname(os.path.abspath(fixtures.__file__))
        filename = os.path.join(fixtures, '__init__.py')
        try:
            os.chdir(fixtures)
            context = self._makeOne()
            stream = context.stream('__init__.py')
            self.assertEqual(stream.read(), open(filename).read())
        finally:
            os.chdir(old_cwd)
        
    def test_path_nopackage_currentpackage(self):
        import os
        from repoze.configuration.tests import fixtures
        context = self._makeOne()
        context.stack.append({'package':fixtures})
        fixtures = os.path.dirname(os.path.abspath(fixtures.__file__))
        filename = os.path.join(fixtures, '__init__.py')
        expected = open(filename).read()
        self.assertEqual(context.stream('__init__.py').read(), expected)

    def test_execute(self):
        registry = {}
        context = self._makeOne(registry)
        actions = [ DummyAction(), DummyAction()]
        context.actions = actions
        result = context.execute()
        self.assertEqual([action.executed for action in actions], [True, True])
        self.failUnless(result is registry)

    def test_load(self):
        context = self._makeOne()
        from repoze.configuration.tests import fixtures
        context.load('configure.yml', fixtures)
        # doesn't blow up

    def test_diffnames(self):
        expected = [1, 2, 3]
        provided = [2]
        context = self._makeOne()
        self.assertEqual(context.diffnames(expected, provided), [1,3])

    def test_getvalue_wrongtype(self):
        context = self._makeOne()
        structure = {'a':1}
        self.assertRaises(ValueError, context.getvalue, structure, 'a')
        
    def test_getvalue_default(self):
        context = self._makeOne()
        structure = {}
        self.assertEqual(context.getvalue(structure, 'a'), None)
        
    def test_getvalue(self):
        context = self._makeOne()
        structure = {'a':'1'}
        self.assertEqual(context.getvalue(structure, 'a'), '1')

    def test_call_later(self):
        context = self._makeOne()
        class Callback:
            def __call__(self, *arg, **kw):
                self.arg = arg
                self.kw = kw
                return True
        callback = Callback()
        sequence = [1,2,3]
        deferred = context.call_later(callback, 1, 2, name=1, *sequence)
        result = deferred()
        self.assertEqual(result, True)
        self.assertEqual(callback.arg, (1,2,1,2,3))
        self.assertEqual(callback.kw, {'name':1})

class TestAction(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.context import Action
        return Action

    def _makeOne(self, discriminator, callback, node):
        return self._getTargetClass()(discriminator, callback, node)

    def test_ctor(self):
        action = self._makeOne('discriminator', 'callback', 'node')
        self.assertEqual(action.discriminator, 'discriminator')
        self.assertEqual(action.callback, 'callback')
        self.assertEqual(action.node, 'node')

    def test_execute(self):
        class Callback:
            def __call__(self):
                self.called = True
        callback = Callback()
        action = self._makeOne('discriminator', callback, 'node')
        action.execute()
        self.assertEqual(callback.called, True)

class TestConfigurationConflict(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.context import ConfigurationConflict
        return ConfigurationConflict

    def _makeOne(self, node1, node2):
        error = self._getTargetClass()(node1, node2)
        return error

    def test_ctor(self):
        node1 = DummyNode()
        node2 = DummyNode()
        error = self._makeOne(node1, node2)
        self.assertEqual(error.node1, node1)
        self.assertEqual(error.node2, node2)
        self.failUnless(error.msg.startswith('Conflicting declarations'))

class DummyMark:
    line = 1
    column = 1
    name = 'dummy'

class DummyNode:
    start_mark = DummyMark()
    end_mark = DummyMark()

class DummyAction:
    executed = False
    def __init__(self):
        self.node = DummyNode()

    def execute(self):
        self.executed = True
        

        
