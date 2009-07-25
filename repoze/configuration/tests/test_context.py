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

    def test_interpolate(self):
        registry = {'here':'/here', 'there':'/there'}
        context = self._makeOne(registry)
        result = context.interpolate('Here is %(here)s, there is %(there)s')
        self.assertEqual(result, 'Here is /here, there is /there')

    def test_interpolate_nothing_to_interpolate(self):
        registry = {'here':'/here', 'there':'/there'}
        context = self._makeOne(registry)
        result = context.interpolate('Here is %(here')
        self.assertEqual(result, 'Here is %(here')

    def test_action(self):
        context = self._makeOne()
        context.action({'discriminator':'discriminator',
                        'callback':'callback'}, 'node')
        self.assertEqual(len(context.actions), 1)
        action = context.actions[0]
        self.assertEqual(action.discriminator, 'discriminator')
        self.assertEqual(action.callback, 'callback')
        self.assertEqual(action.node, 'node')
        self.assertEqual(context.discriminators['discriminator'],
                         context.actions[0])

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

    def test_action_withconflict_local_override_no_stack_override(self):
        context = self._makeOne()
        context.discriminators['discriminator'] = DummyAction()
        context.stack = [{'override':False}]
        context.action({'discriminator':'discriminator',
                        'callback':'callback', 'override':True},
                       'node')
        self.assertEqual(len(context.actions), 1)
        action = context.actions[0]
        self.assertEqual(action.discriminator, 'discriminator')
        self.assertEqual(action.callback, 'callback')
        self.assertEqual(action.node, 'node')
        self.assertEqual(context.discriminators['discriminator'],
                         context.actions[0])

    def test_action_withconflict_stack_override_no_local_override(self):
        context = self._makeOne()
        context.discriminators['discriminator'] = DummyAction()
        context.stack = [{'override':True}]
        context.action({'discriminator':'discriminator',
                        'callback':'callback'},
                       'node')
        self.assertEqual(len(context.actions), 1)
        action = context.actions[0]
        self.assertEqual(action.discriminator, 'discriminator')
        self.assertEqual(action.callback, 'callback')
        self.assertEqual(action.node, 'node')
        self.assertEqual(context.discriminators['discriminator'],
                         context.actions[0])

    def test_error(self):
        from repoze.configuration.context import ConfigurationError
        context = self._makeOne()
        node = DummyNode()
        self.assertRaises(ConfigurationError, context.error, node, 'message')

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

    def test_resolve_relative_startswith_dot(self):
        from repoze.configuration import tests
        from repoze.configuration.tests.fixtures import fixturefunc
        context = self._makeOne()
        context.stack.append({'package':tests})
        result = context.resolve('.fixtures:fixturefunc')
        self.assertEqual(result, fixturefunc)

    def test_resolve_relative_is_dot(self):
        from repoze.configuration import tests
        context = self._makeOne()
        context.stack.append({'package':tests})
        result = context.resolve('.')
        self.assertEqual(result, tests)
        
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

    def test_popvalue_wrongtype(self):
        context = self._makeOne()
        structure = {'a':1}
        self.assertRaises(ValueError, context.popvalue, structure, 'a')
        
    def test_popvalue_default(self):
        context = self._makeOne()
        structure = {}
        self.assertEqual(context.popvalue(structure, 'a'), None)
        
    def test_popvalue(self):
        context = self._makeOne()
        structure = {'a':'1'}
        self.assertEqual(context.popvalue(structure, 'a'), '1')
        self.assertEqual(structure, {})

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

    def test_execute_exception(self):
        class Callback:
            def __call__(self):
                raise ValueError('foo')
        callback = Callback()
        node = DummyNode()
        action = self._makeOne('discriminator', callback, node)
        self.assertRaises(ValueError, action.execute)

class TestConfigurationConflict(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.context import ConfigurationConflict
        return ConfigurationConflict

    def _makeOne(self, node1, node2):
        error = self._getTargetClass()(node1, node2)
        return error

    def test_ctor_no_file(self):
        node1 = DummyNode()
        node2 = DummyNode()
        error = self._makeOne(node1, node2)
        self.assertEqual(error.node1, node1)
        self.assertEqual(error.node2, node2)
        lines = error.msg.split('\n')
        self.assertEqual(len(lines), 7)
        self.assertEqual(lines[0], 'Conflicting declarations:')
        self.assertEqual(lines[1], '')
        self.assertEqual(lines[2], 'lines 1:1-1:1 of file "dummy"')
        self.assertEqual(lines[3], '')
        self.assertEqual(lines[4], 'conflicts with')
        self.assertEqual(lines[5], '')
        self.assertEqual(lines[6], 'lines 1:1-1:1 of file "dummy"')

    def test_ctor_with_file(self):
        import os
        here = os.path.normpath(os.path.dirname(__file__))
        fixtures = os.path.join(here, 'fixtures')

        node1 = DummyNode()
        node2 = DummyNode()

        node1.start_mark.line = 1
        node1.end_mark.line = 2
        node1.start_mark.index = 0
        node1.end_mark.index = 50
        file1 = os.path.join(fixtures, 'conflict1.yml')
        node1.start_mark.name = file1

        node2.end_mark.line = 1
        node2.end_mark.line = 2
        node2.start_mark.index = 0
        node2.end_mark.index = 50
        file2 = os.path.join(fixtures, 'conflict2.yml')
        node2.start_mark.name = file2

        error = self._makeOne(node1, node2)

        self.assertEqual(error.node1, node1)
        self.assertEqual(error.node2, node2)

        lines = error.msg.split('\n')
        self.assertEqual(len(lines), 11)
        self.assertEqual(lines[0], 'Conflicting declarations:')
        self.assertEqual(lines[1], '')
        self.assertEqual(lines[2], '--- !abc')
        self.assertEqual(lines[3], 'foo: 1')
        self.assertEqual(lines[4], 'in lines 1:1-2:1 of file "%s"' % file1)
        self.assertEqual(lines[5], '')
        self.assertEqual(lines[6], 'conflicts with')
        self.assertEqual(lines[7], '')
        self.assertEqual(lines[8], '--- !abc')
        self.assertEqual(lines[9], 'foo: 1')
        self.assertEqual(lines[10], 'in lines 1:1-2:1 of file "%s"' % file2)


class DummyMark:
    line = 1
    column = 1
    name = 'dummy'

class DummyNode:
    def __init__(self):
        self.start_mark = DummyMark()
        self.end_mark = DummyMark()

class DummyAction:
    executed = False
    def __init__(self):
        self.node = DummyNode()

    def execute(self):
        self.executed = True
        

        
