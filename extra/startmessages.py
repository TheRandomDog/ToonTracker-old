class StartMessage:
    PREFIX_EMOJI = ''
    PREFIX_ASCII = ''

    def __init__(self, text):
        self.message = text

    def __str__(self):
        return self.message

class Info(StartMessage):
    PREFIX_EMOJI = ':grey_exclamation: '
    PREFIX_ASCII = ''

class Warning(StartMessage):
    PREFIX_EMOJI = ':warning: '
    PREFIX_ASCII = '[!] '

class Error(StartMessage):
    PREFIX_EMOJI = ':exclamation: '
    PREFIX_ASCII = '[!!!] '