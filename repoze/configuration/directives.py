def include(context, structure):
    if not isinstance(structure, dict):
        raise ValueError('Bad structure for include directive')

    diff = context.diffnames(structure, ['package', 'filename'])
    if diff:
        raise ValueError('Unknown key(s) in "include" directive: %r' % diff)

    package = context.getvalue(structure, 'package')
    if package is not None:
        package = context.resolve(package)
    else:
        package = context.current_package()
    filename = context.getvalue(structure, 'filename', 'configure.yml')
    context.load(filename, package)
