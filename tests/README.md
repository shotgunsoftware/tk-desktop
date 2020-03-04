tk-desktop tests
----------------

This folder contains the tests for tk-desktop. You can run those tests using pytest, as usual.

There's also a test script that will allow you to use the CommandsView widget without having to launch the Shotgun Desktop. It requires that you also have tk-nuke, tk-maya and tk-core alonside this repository on disk. Simply run `run_project_commands.py` with the Python interpreter of your choosing. The only parameter is --async. When set, the commands will be added in the panel asynchronously, mimicking the behaviour in Shotgun Desktop, where commands appear one after the other in the GUI.
