Documentation How-To
====================

The documentation has two inputs: docstrings in Python files of the
``./command_line_assistant/`` module and plain ReST markup in ``.rst`` files in
``./docs/sources/*.rst``. Formatting rules for docstrings and rst files may be
slightly different.

Generally try to put information into docstrings including those at
the module-level.

Create additional rst files to describe generic concepts or anything
which doesn't fit into the scope of a specific module.

Layout
------

Rst files layout is currently very simple::

  index.rst
  -- meta.rst         // Documentation about documentation
  -- initialize.rst   // Dedicated page for a topic, can reference the API docs.
  -- commands/*.rst   // Dedicated folder for a topic, can reference the API docs.

How to build
------------

With a standard Fedora environment you need to install dependencies::

  $ sudo dnf install python3-sphinx python3-sphinx-autodoc-typehints.noarchpython3-sphinx

And then got to `./docs/` and run make::

  $ make html

The output is going to appear in `./docs/build/html`.

Tips & Tricks
--------------

References to modules, methods and classes
..........................................

To refer to a Python object use backticks.

It can be a little tricky due to use the correct name for the object. See the following examples::

   1. :mod:`handlers`,       // works in docstrings, doesn't work in rst
   2. :class:`LocalHistory`, // works in docstrings, doesn't work in rst
   3. :mod:`.handlers`,      // looks fo all objects which end with the suffix `.handlers`.
                             // As it finds two: command_line_assistant.handlers and command_line_assistant.tests.handlers
                             // it takes the shortest of them
   4. :mod:`command_line_assistant.handlers`,  // fully-qualified name
   5. :mod:`~command_line_assistant.tests.handlers`, // cuts the title to the last part
   6. :attr:`.ColorDecorator.FOREGROUND_COLORS`,
   7. :attr:`.ColorDecorator.FOREGROUND_COLORS.`\ s, // see the note
   8. `.handlers`. // text in backticks recognized as inline code by default.

Output:

1. :mod:`handlers`,
2. :class:`LocalHistory`,
3. :mod:`.handlers`,
4. :mod:`command_line_assistant.handlers`,
5. :mod:`~command_line_assistant.tests.handlers`,
6. :attr:`.ColorDecorator.FOREGROUND_COLORS`,
7. :attr:`.ColorDecorator.FOREGROUND_COLORS`\ s,
8. `~command_line_assistant.handlers`.


.. note:: ReST recognizes a closing backtick only if it is followed by
   a space to punctuation mark. If the backtick is followed by a
   letter, insert the escaped space "`\\ \ `" after it.
