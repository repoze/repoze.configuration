class ConfigurationError(Exception):
    """ The exception type raised when a configuration file cannot be
    executed or loaded due to a configuration error """
    pass

class ConfigurationConflict(ConfigurationError):
    """ The exception type raised when a configuration contains
    conflicting declarations (the discriminators of two declarations
    conflict) """
    def __init__(self, declaration1, declaration2):
        self.declaration1 = declaration1
        self.declaration2 = declaration2
        self.msg = str(self)

    def __str__(self):
        message = []
        message.append('Conflicting declarations:')
        message.append(self.declaration2.lineinfo)
        message.append('conflicts with')
        message.append(self.declaration1.lineinfo)
        return '\n\n'.join(message)

