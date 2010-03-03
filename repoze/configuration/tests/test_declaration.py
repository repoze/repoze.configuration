import unittest

class TestDeclaration(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.declaration import Declaration
        return Declaration

    def _makeOne(self, **kw):
        return self._getTargetClass()(**kw)

    def test_registry(self):
        context = DummyContext()
        decl = self._makeOne(context = context)
        self.assertEqual(decl.registry, context)

    def test_expect_no_names_wrongtype(self):
        from repoze.configuration.exceptions import ConfigurationError
        decl = self._makeOne(structure=[], lineinfo='')
        self.assertRaises(ConfigurationError, decl.expect, dict)

    def test_expect_no_names_righttype(self):
        decl = self._makeOne(structure={}, lineinfo='')
        decl.expect(dict) # doesnt blow up

    def test_expect_names_wrong(self):
        from repoze.configuration.exceptions import ConfigurationError
        decl = self._makeOne(structure={'foo':'bar'}, lineinfo='')
        self.assertRaises(ConfigurationError, decl.expect, dict, ['a'])

    def test_expect_names_right(self):
        decl = self._makeOne(structure={'foo':'bar'}, lineinfo='')
        decl.expect(dict, ['foo', 'bar']) # doesnt blow up

    def test_getvalue_wrongtype(self):
        from repoze.configuration.exceptions import ConfigurationError
        decl = self._makeOne(structure = {'a':1}, lineinfo='')
        self.assertRaises(ConfigurationError, decl.getvalue, 'a', types=(str,))

    def test_getvalue_default(self):
        decl = self._makeOne(structure={})
        self.assertEqual(decl.getvalue('a'), None)

    def test_getvalue_get(self):
        structure = {'a':'1'}
        decl = self._makeOne(structure=structure)
        self.assertEqual(decl.getvalue('a'), '1')
        self.assertEqual(structure, {'a':'1'})

    def test_getvalue_pop(self):
        structure = {'a':1}
        decl = self._makeOne(structure=structure)
        val = decl.getvalue('a', pop=True)
        self.assertEqual(val, 1)
        self.assertEqual(structure, {})

    def test_boolean_true(self):
        for val in ('t', 'true', 'yes', 'on', '1'):
            decl = self._makeOne(structure = {'a':val})
            val = decl.boolean('a')
            self.assertEqual(val, True)

    def test_boolean_false(self):
        decl = self._makeOne(structure = {'a':'false'})
        val = decl.boolean('a')
        self.assertEqual(val, False)

    def test_boolean_unknown(self):
        decl = self._makeOne(structure = {'a':None})
        val = decl.boolean('a')
        self.assertEqual(val, False)

    def test_boolean_pop(self):
        structure = {'a':'false'}
        decl = self._makeOne(structure=structure)
        val = decl.boolean('a', pop=True)
        self.assertEqual(val, False)
        self.assertEqual(structure, {})

    def test_boolean_get(self):
        structure = {'a':'false'}
        decl = self._makeOne(structure=structure)
        val = decl.boolean('a')
        self.assertEqual(val, False)
        self.assertEqual(structure, {'a':'false'})

    def test_string_get(self):
        structure = {'a':'yo!'}
        decl = self._makeOne(structure=structure)
        val = decl.string('a')
        self.assertEqual(val, 'yo!')
        self.assertEqual(structure, {'a':'yo!'})

    def test_string_wrongtype(self):
        from repoze.configuration.exceptions import ConfigurationError
        decl = self._makeOne(structure = {'a':1}, lineinfo='')
        self.assertRaises(ConfigurationError, decl.string, 'a')

    def test_string_pop(self):
        structure = {'a':'yo!'}
        decl = self._makeOne(structure=structure)
        val = decl.string('a', pop=True)
        self.assertEqual(val, 'yo!')
        self.assertEqual(structure, {})

    def test_integer_get(self):
        structure = {'a':1}
        decl = self._makeOne(structure=structure)
        val = decl.integer('a')
        self.assertEqual(val, 1)
        self.assertEqual(structure, {'a':1})

    def test_integer_pop(self):
        structure = {'a':1}
        decl = self._makeOne(structure=structure)
        val = decl.integer('a', pop=True)
        self.assertEqual(val, 1)
        self.assertEqual(structure, {})

    def test_integer_default(self):
        structure = {}
        decl = self._makeOne(structure=structure)
        val = decl.integer('a')
        self.assertEqual(val, None)

    def test_intger_fromstring(self):
        decl = self._makeOne(structure = {'a':'1'})
        val = decl.integer('a')
        self.assertEqual(val, 1)

    def test_intger_fromstring_error(self):
        from repoze.configuration.exceptions import ConfigurationError
        decl = self._makeOne(structure = {'a':'flub'}, lineinfo='')
        self.assertRaises(ConfigurationError, decl.integer, 'a')

    def test_resolve(self):
        context = DummyContext({})
        decl = self._makeOne(context=context)
        result = decl.resolve('name')
        self.assertEqual(result, 'resolved')

    def test_resolve_importerror(self):
        from repoze.configuration.exceptions import ConfigurationError
        context = DummyContext({}, resolve_err=True)
        decl = self._makeOne(context=context, lineinfo='')
        self.assertRaises(ConfigurationError, decl.resolve, 'name')

    def test_error(self):
        from repoze.configuration.exceptions import ConfigurationError
        decl = self._makeOne(lineinfo='lineinfo')
        self.assertRaises(ConfigurationError, decl.error, 'message')

    def test_call_later(self):
        decl = self._makeOne()
        class Callback:
            def __call__(self, *arg, **kw):
                self.arg = arg
                self.kw = kw
                return True
        callback = Callback()
        sequence = [1,2,3]
        deferred = decl.call_later(callback, 1, 2, name=1, *sequence)
        result = deferred()
        self.assertEqual(result, True)
        self.assertEqual(callback.arg, (1,2,1,2,3))
        self.assertEqual(callback.kw, {'name':1})

    def test_action(self):
        context = DummyContext({})
        decl = self._makeOne(context=context)
        decl.action('callback', discriminator='discriminator',
                    override='override')
        self.assertEqual(context.actions,
                         [(decl, 'callback', 'discriminator', 'override')])

class TestYAMLDeclaration(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.declaration import YAMLDeclaration
        return YAMLDeclaration

    def _makeOne(self, context, loader, node):
        return self._getTargetClass()(context, loader, node)

    def test_lineinfo(self):
        context = None
        loader = None
        node = DummyNode()
        decl = self._makeOne(context, loader, node)
        line = decl.lineinfo
        self.assertEqual(line, 'lines 2-2 of file "dummy"')

    def test_get_structure_deep(self):
        context = DummyContext()
        loader = DummyLoader(context)
        node = DummyNode(id='deep')
        decl = self._makeOne(context, loader, node)
        result = decl.structure
        self.assertEqual(result, 'deep')
        self.assertEqual(decl._structure, 'deep')

    def test_get_structure_shallow(self):
        context = DummyContext()
        loader = DummyLoader(context)
        node = DummyNode(id='shallow')
        decl = self._makeOne(context, loader, node)
        result = decl.structure
        self.assertEqual(result, 'shallow')
        self.assertEqual(decl._structure, 'shallow')

    def test_set_structure(self):
        context = DummyContext()
        loader = DummyLoader(context)
        node = DummyNode(id='shallow')
        decl = self._makeOne(context, loader, node)
        decl.structure = 'structure'
        self.assertEqual(decl._structure, 'structure')

class TestPythonDeclaration(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.declaration import PythonDeclaration
        return PythonDeclaration

    def _makeOne(self, context, **kw):
        return self._getTargetClass()(context, **kw)

    def test_ctor(self):
        context = object()
        target = self._makeOne(context, foo='foo', bar='baz')
        self.assertEqual(target.context, context)
        self.assertEqual(target.structure, {'foo': 'foo', 'bar': 'baz'})
        self.assertEqual(target.lineinfo, '')

class TestImperativeDeclaration(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.configuration.declaration import ImperativeDeclaration
        return ImperativeDeclaration

    def _makeOne(self, context, **kw):
        return self._getTargetClass()(context, **kw)

    def test_action(self):
        calls = []
        def do_this():
            calls.append(1)
        target = self._makeOne(object())
        target.action(do_this)
        self.assertEqual(calls, [1])

class Test_lineinfo(unittest.TestCase):
    def _callFUT(self, node):
        from repoze.configuration.declaration import lineinfo
        return lineinfo(node)

    def test_withfile(self):
        import os
        here = os.path.normpath(os.path.dirname(__file__))
        fixtures = os.path.join(here, 'fixtures')
        filename = os.path.join(fixtures, 'conflict1.yml')

        node = DummyNode()

        node.start_mark.line = 1
        node.start_mark.column = 2
        node.start_mark.index = 0
        node.start_mark.name = filename

        node.end_mark.line = 1
        node.end_mark.column = 2
        node.end_mark.index = 0
        node.end_mark.index = 50
        node.end_mark.name = filename

        msg = self._callFUT(node)

        lines = msg.split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], '--- !abc')
        self.assertEqual(lines[1], 'foo: 1')
        self.assertEqual(lines[2], ' in lines 2-2 of file "%s"' % filename)

    def test_file_exception(self):
        node = DummyNode()
        msg = self._callFUT(node)

        lines = msg.split('\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'lines 2-2 of file "dummy"')

class DummyNode:
    def __init__(self, id='theid'):
        self.id = id
        self.start_mark = DummyMark()
        self.end_mark = DummyMark()

class DummyMark:
    line = 1
    column = 1
    name = 'dummy'

class DummyContext:
    def __init__(self, registry=None, resolve_err=False):
        if registry is None:
            registry = {}
        self.registry = registry
        self.actions = []
        self.resolve_err = resolve_err

    def resolve(self, name):
        if self.resolve_err:
            raise ImportError('whatever')
        return 'resolved'

    def action(self, directive, callback, discriminator=None, override=False):
        self.actions.append((directive, callback, discriminator, override))


class DummyLoader:
    def __init__(self, context):
        self.context = context

    def construct_deep(self, node, deep=True):
        return 'deep'

    def construct_shallow(self, node):
        return 'shallow'


