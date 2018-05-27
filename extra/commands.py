class Command:
    NAME = None
    RANK = 0
    DELETE_PRIOR_MESSAGE = False

    @classmethod
    async def _execute(cls, client, module, message, *args):
        if cls.DELETE_PRIOR_MESSAGE:
            message.nonce = 'silent'
            await message.delete()
        await cls.execute(client, module, message, *args)

    @staticmethod
    async def execute(client, module, message, *args):
        pass

class CommandResponse:
    def __init__(self, target, message, deleteIn=0, priorMessage=None, **kwargs):
        self.target = target
        self.message = message
        self.deleteIn = deleteIn
        self.priorMessage = priorMessage
        self.kwargs = kwargs