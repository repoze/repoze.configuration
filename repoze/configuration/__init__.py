from repoze.configuration.context import Context

def load(filename='configure.yml', package=None, context=None):
    if context is None:
        registry = {}
        context = Context(registry)
    context.load(filename, package)
    return context

def execute(filename='configure.yml', package=None, context=None):
    context = load(filename, package, context)
    context.execute()
    return context

    
        


    


