import re
from .module import *

class GroupMsgHandler(MessageHandler):
    def handle(module, message):
        if module.gcmReq.match(message.content.lower()):
            return 'The group module has been temporarily disabled while ToonTracker v4.0 gets out of beta -- thanks for your patience!'

class GroupModule(Module):
    gcmReq = re.compile('(create|add|make|edit|change|delete|remove|cancel|disband|destroy|clear|kill|rip|find|list|get|join|leave)+.*group+\s*')
    HANDLERS = [GroupMsgHandler]

module = GroupModule