class Command:
    NAME = None
    RANK = 0

    @staticmethod
    def execute(client, module, message, *args):
        pass

class CommandResponse:
    def __init__(self, target, message, delete_in=0, prior_message=None, **kwargs):
        self.target = target
        self.message = message
        self.delete_in = delete_in
        self.prior_message = prior_message
        self.kwargs = kwargs