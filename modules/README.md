# Modules

ToonTracker's functionality is sorted up into "modules" which can be configured to load on an individual basis in the config.

## module.py

This is the base class for all modules, and is technically a module but not really. Any modules added should be inherited from this class and documented here, if you feel like writing.

All modules come with the capability of starting up their own asynchronous activities via asyncio for doing various background tasks and loops while the main Discord client loop chugs along.

For modules that collect and handle data, such as modules that track statistics like invasions or game server information, there are two convenience asynchronous methods: `collect_data()` and `handle_data()`. The results from `collect_data()` are passed into `handle_data()` automatically, so it just cleans up the flow in the background slightly. If that format doesn't fit your need for something that needs to be loop, you can simply use `loop_iteration()` instead. All of these will loop on a cooldown interval specified by `cooldown_interval` in the config, in this order:
  > collect_data()
  
  > handle_data()
  
  > loop_iteration()
  
Modules also have the ability to make announcements or "permanent messages" on their own accord. In another class within the same module file, you can inherit the `Announcer` class and reimplement a single method: `announce(self, ...)`. The announcer has a `module` attribute which contains the instance of the module currently running, with `...` representing any arguments you'd like to send to the announcer. The method should return text or an embed that can be sent to a channel. To trigger this announcement, you should call `Module.announcer_attr.announce(...)`. This will simply notify the client it's ready to send an announcement and will do so on its next loop.

As for "permanent messages", they're similar but different. In another class within the same module file, you can inherit the `PermaMessage` class and reimplement a single method: `update(...)`. You will get passed the same values as listed above. The method must return an embed with a distinct title, and the same title as the embed it wants updating, as it is used to differntiate other "permanent messages". You should not have more than 10 permanent messages on a channel at a time, and you shouldn't use permanent channels in publicly available channels. Doing either may cause some permanent messages to stop updating. To update the permanent message, you should call `Module.perma_message_attr.update(...)`. 

Modules also get commands, located at `extra.commands.Command`. They're stored as an inner class to the module implementing `Command`, and have two attributes: `NAME` and `RANK`. Name is the command name, naturally, and Rank is the lowest possible integer ranking required to use the command. Inside the class, one only has to reimplement a single **static coroutine** `execute(client, module, message, *args)`. `client` is an instance of ToonTracker, the client, `module` is the instance of the module its residing in, `message` is a copy of the `discord.Message` object, and `*args` contains a string split into a list by spaces. Rank verification happens outside of the class.

For announcements and permanent messages, as long as they are called within the module by the module's own functions, they need not be referenced elsewhere. For commands, they're automatically added for a module upon loading of a module.

Convenience functions and classes are available, such as in `extra.toontown` which contains many classes for Cog types, in-game locations, etc., and `utils`, which allow you to access Config, Users, time-string conversions, type assertions, etc.

Finally, ToonTracker will only load a module if the Python module *(the .py file)* has an attribute named `module` referencing the module class.

## Maybe we'll add some documentation for each module later 👀
