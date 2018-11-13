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
    def __init__(self, target, message, delete_in=0, prior_message=None, **kwargs):
        self.target = target
        self.message = message
        self.delete_in = delete_in
        self.prior_message = prior_message
        self.kwargs = kwargs