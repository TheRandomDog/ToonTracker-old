class Command:
    NAME = None
    RANK = 0

    @staticmethod
    def execute(client, module, message, *args):
        pass

class CommandResponse:
    def __init__(self, target, message, deleteIn=0, priorMessage=None, **kwargs):
        self.target = target
        self.message = message
        self.deleteIn = deleteIn
        self.priorMessage = priorMessage
        self.kwargs = kwargs