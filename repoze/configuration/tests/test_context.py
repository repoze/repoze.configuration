import unittest

class TestContext(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration import Context
        return Context

    def _makeOne(self, data=None, loader=None):
        if data is None:
            data = {}
        return self._getTargetClass()(data, _loader=loader)

    def test_ctor(self):
        data = {}
        context = self._makeOne(data, 'loader')
        self.assertEqual(context.loader, 'loader')
        self.assertEqual(context.stack, [])
        self.assertEqual(context.actions, [])

    def test_registry(self):
        context = self._makeOne()
        self.assertEqual(context.registry, context)

    def test_interpolate_from_data(self):
        data = {'here':'/here', 'there':'/there'}
        context = self._makeOne(data)
        result = context.interpolate('Here is %(here)s, there is %(there)s')
        self.assertEqual(result, 'Here is /here, there is /there')

    def test_interpolate_from_data_overrides_stack(self):
        data = {'here':'/here', 'there':'/there'}
        context = self._makeOne(data)
        context.stack = [{'here':'stack_here', 'there':'stack_there'}]
        result = context.interpolate('Here is %(here)s, there is %(there)s')
        self.assertEqual(result, 'Here is /here, there is /there')

    def test_interpolate_from_data_falls_back_to_stack(self):
        data = {'here':'/here'}
        context = self._makeOne(data)
        context.stack = [{'here':'stack_here', 'there':'stack_there'}]
        result = context.interpolate('Here is %(here)s, there is %(there)s')
        self.assertEqual(result, 'Here is /here, there is stack_there')

    def test_interpolate_nothing_to_interpolate(self):
        data = {'here':'/here', 'there':'/there'}
        context = self._makeOne(data)
        result = context.interpolate('Here is %(here')
        self.assertEqual(result, 'Here is %(here')

    def test_interpolate_keyerror(self):
        data = {}
        context = self._makeOne(data)
        self.assertRaises(KeyError, context.interpolate, 'Here is %(here)s')

    def test_action(self):
        context = self._makeOne()
        context.action('declaration', 'callback', discriminator='discriminator')
        self.assertEqual(len(context.actions), 1)
        action = context.actions[0]
        self.assertEqual(action.discriminator, 'discriminator')
        self.assertEqual(action.callback, 'callback')
        self.assertEqual(action.declaration, 'declaration')
        self.assertEqual(context.discriminators['discriminator'],
                         context.actions[0])

    def test_action_no_discriminator_doesnt_conflict(self):
        context = self._makeOne()
        context.action('declaration', 'callback')
        self.assertEqual(len(context.actions), 1)
        context.action('declaration', 'callback')
        # no ConfigurationConflict raised
        self.assertEqual(len(context.actions), 2)

    def test_action_withconflict(self):
        from repoze.configuration.context import ConfigurationConflict
        context = self._makeOne()
        context.discriminators['discriminator'] = DummyAction()
        context.stack = [{'override':False}]
        declaration = DummyDeclaration()
        self.assertRaises(ConfigurationConflict,
                          context.action,
                          declaration, 'callback', 'discriminator')

    def test_action_withconflict_local_override_no_stack_override(self):
        context = self._makeOne()
        context.discriminators['discriminator'] = DummyAction()
        context.stack = [{'override':False}]
        context.action('declaration', 'callback', discriminator='discriminator',
                       override=True)
        self.assertEqual(len(context.actions), 1)
        action = context.actions[0]
        self.assertEqual(action.discriminator, 'discriminator')
        self.assertEqual(action.callback, 'callback')
        self.assertEqual(action.declaration, 'declaration')
        self.assertEqual(context.discriminators['discriminator'],
                         context.actions[0])

    def test_action_withconflict_stack_override_no_local_override(self):
        context = self._makeOne()
        context.discriminators['discriminator'] = DummyAction()
        context.stack = [{'override':True}]
        context.action('declaration', 'callback', discriminator='discriminator',
                       override=False)
        self.assertEqual(len(context.actions), 1)
        action = context.actions[0]
        self.assertEqual(action.discriminator, 'discriminator')
        self.assertEqual(action.callback, 'callback')
        self.assertEqual(action.declaration, 'declaration')
        self.assertEqual(context.discriminators['discriminator'],
                         context.actions[0])

    def test_resolve_absolute(self):
        from repoze.configuration.tests.fixtures import fixturefunc
        context = self._makeOne()
        result = context.resolve(
            'repoze.configuration.tests.fixtures:fixturefunc')
        self.assertEqual(result, fixturefunc)
        
    def test_irrresolveable_absolute(self):
        context = self._makeOne()
        self.assertRaises(ImportError, context.resolve,
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
        self.assertRaises(ImportError, context.resolve, '.fixturefunc')

    def test_irrresolveable_relative(self):
        from repoze.configuration.tests import fixtures
        context = self._makeOne()
        context.stack.append({'package':fixtures})
        self.assertRaises(ImportError, context.resolve, ':notexisting')

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

    def test_stream_nopackage_nocurrentpackage(self):
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
        
    def test_stream_nopackage_currentpackage(self):
        import os
        from repoze.configuration.tests import fixtures
        context = self._makeOne()
        context.stack.append({'package':fixtures})
        fixtures = os.path.dirname(os.path.abspath(fixtures.__file__))
        filename = os.path.join(fixtures, '__init__.py')
        expected = open(filename).read()
        self.assertEqual(context.stream('__init__.py').read(), expected)

    def test_abs_filename_absolute(self):
        import os
        from repoze.configuration.tests import fixtures
        filename = os.path.join(os.path.dirname(
            os.path.abspath(fixtures.__file__)), '__init__.py')
        context = self._makeOne()
        result = context.abs_filename(filename)
        self.assertEqual(result, filename)

    def test_abs_filename_nopackage_nocurrentpackage(self):
        import os
        from repoze.configuration.tests import fixtures
        old_cwd = os.getcwd()
        fixtures = os.path.dirname(os.path.abspath(fixtures.__file__))
        filename = os.path.join(fixtures, '__init__.py')
        try:
            os.chdir(fixtures)
            context = self._makeOne()
            result = context.abs_filename('__init__.py')
            self.assertEqual(result, filename)
        finally:
            os.chdir(old_cwd)
        
    def test_abs_filename_nopackage_currentpackage(self):
        import os
        from repoze.configuration.tests import fixtures
        context = self._makeOne()
        context.stack.append({'package':fixtures})
        fixtures = os.path.dirname(os.path.abspath(fixtures.__file__))
        filename = os.path.join(fixtures, '__init__.py')
        self.assertEqual(context.abs_filename('__init__.py'), filename)

    def test_load_standard_loader(self):
        def loader(context, stream):
            context.loaded = True
        context = self._makeOne(loader=loader)
        from repoze.configuration.tests import fixtures
        context.load('configure.yml', fixtures)
        self.assertEqual(context.stack, [])
        self.assertEqual(context.loaded, True)

    def test_load_custom_loader(self):
        def loader(context, stream):
            context.loaded = True
        context = self._makeOne()
        from repoze.configuration.tests import fixtures
        context.load('configure.yml', fixtures, loader=loader)
        self.assertEqual(context.stack, [])
        self.assertEqual(context.loaded, True)
        # doesn't blow up

    def test_load_sets_stack(self):
        import os
        result = []
        def loader(context, stream):
            result.append(context.stack[-1])
        context = self._makeOne()
        from repoze.configuration.tests import fixtures
        context.stack = [{'package':fixtures}]
        context.load('configure.yml', fixtures, loader=loader)
        result = result[0]
        expect_here = os.path.dirname(os.path.abspath(fixtures.__file__))
        self.assertEqual(result['here'], expect_here)
        self.assertEqual(result['override'], False)
        self.assertEqual(result['filename'], 'configure.yml')
        self.assertEqual(result['package'], fixtures)

    def test_execute(self):
        data = {}
        context = self._makeOne(data)
        actions = [ DummyAction(), DummyAction()]
        context.actions = actions
        context.execute()
        self.assertEqual([action.executed for action in actions], [True, True])

class TestAction(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.context import Action
        return Action

    def _makeOne(self, discriminator, callback, node):
        return self._getTargetClass()(discriminator, callback, node)

    def test_ctor(self):
        action = self._makeOne('discriminator', 'callback', 'declaration')
        self.assertEqual(action.discriminator, 'discriminator')
        self.assertEqual(action.callback, 'callback')
        self.assertEqual(action.declaration, 'declaration')

    def test_execute(self):
        class Callback:
            def __call__(self):
                self.called = True
        callback = Callback()
        action = self._makeOne('discriminator', callback, 'declaration')
        action.execute()
        self.assertEqual(callback.called, True)

    def test_execute_exception(self):
        class Callback:
            def __call__(self):
                raise ValueError('foo')
        callback = Callback()
        declaration = DummyDeclaration()
        action = self._makeOne('discriminator', callback, declaration)
        self.assertRaises(ValueError, action.execute)

class DummyAction:
    executed = False
    def __init__(self):
        self.declaration = DummyDeclaration()

    def execute(self):
        self.executed = True

class DummyDeclaration:
    lineinfo = 'lineinfo'
    
