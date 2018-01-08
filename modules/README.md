# Modules

ToonTracker's functionality is sorted up into "modules" which can be configured to load on an individual basis in the config.

## module.py

This is the base class for all modules, and is technically a module but not really. Any modules added should be inherited from this class and documented here, if you feel like writing.

All modules come with the capability of starting up their own thread for doing various background tasks and loops while the main Discord client chugs along asynchronously, which is of course very safe and very efficient and could not be improved upon in any way.

For modules that collect and handle data, such as modules that track statistics like invasions or game server information, there are two convenience methods: `collectData()` and `handleData()`. The results from `collectData()` are passed into `handleData()` automatically, so it just cleans up the flow in the background slightly. If that format doesn't fit your need for something that needs to be loop, you can simply use `loopIteration()` instead. All of these will loop on a cooldown interval specified by `cooldown_interval` in the config, in this order:
  > collectData()
  
  > handleData()
  
  > loopIteration()
  
Modules also have the ability to make announcements or "permanent messages" on their own accord. In another class within the same module file, you can inherit the `Announcer` class and reimplement a single method: `announce(module, data)`. You will get passed the instance of the module currently running and any data passed to the announcer. The method should return text or an embed that can be sent to a channel. To trigger this announcement, you should call `Module.announce(announcerSubclass, *data)`. This will simply notify the client it's ready to send an announcement and will do so on its next loop.

As for "permanent messages", they're similar but different. In another class within the same module file, you can inherit the `PermaMsg` class and reimplement a single method: `update(module)`. You will get passed the instance of the module, and any information needed can be pulled from there. The method must return an embed with a distinct title, and the same title as the embed it wants updating, as it is used to differntiate other "permanent messages". You should not have more than 10 permanent messages on a channel at a time, and you shouldn't use permanent channels in publicly available channels. Doing either may cause some permanent messages to stop updating. To update the permanent message, you should call `Module.updatePermaMsg(permaMsgSubclass)`. 

Modules also get commands, located at `extra.commands.Command`. They're stored as an inner class to the module implementing `Command`, and have two attributes: `NAME` and `RANK`. Name is the command name, naturally, and Rank is the lowest possible integer ranking required to use the command. Inside the class, one only has to reimplement a single **static coroutine** `execute(client, module, message, *args)`. `client` is an instance of ToonTracker, the client, `module` is the instance of the module its residing in, `message` is a copy of the `discord.Message` object, and `*args` contains a string split into a list by spaces. Rank verification happens outside of the class.

For announcements and permanent messages, as long as they are called within the module by the module's own functions, they need not be referenced elsewhere. For commands, they're automatically added for a module upon loading of a module.

Convenience functions and classes are available, such as in `extra.toontown` which contains many classes for Cog types, in-game locations, etc., and `utils`, which allow you to access Config, Users, time-string conversions, type assertions, etc.

Finally, ToonTracker will only load a module if the Python module *(the .py file)* has an attribute named `module` referencing the module class.

## Maybe we'll add some documentation for each module later 👀
