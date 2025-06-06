# Simplified Command Structure

This directory contains a simplified, elegant command structure inspired by typer/click but using argparse. The new structure eliminates complex class hierarchies, factories, and operations in favor of a clean decorator-based approach.

## Key Benefits

1. **Simplicity**: Functions instead of complex class hierarchies
2. **Decorator-based**: Easy-to-use decorators for command and argument registration
3. **Less boilerplate**: Minimal code required to create new commands
4. **Easy to understand**: Clear, linear code flow
5. **Maintainable**: Reduced complexity makes the code easier to maintain and extend

## Architecture Overview

### Core Components

- **`registry.py`**: Simple command registration system with decorators
- **`utils.py`**: Common utilities and helpers for commands
- **Individual command files**: `feedback.py`, `chat.py`, `history.py`, `shell.py`

### Command Structure

Each command is now implemented as a simple function with decorators:

```python
from command_line_assistant.utils.cli import argument, command
from command_line_assistant.commands.utils import create_utils

@command("mycommand", help="Description of my command")
@argument("positional_arg", help="A positional argument")
@argument("-f", "--flag", action="store_true", help="An optional flag")
@argument("-v", "--value", type=str, help="An optional value")
def my_command(args: Namespace, context: CommandContext) -> int:
    """Command implementation."""
    utils = create_utils(context, args)  # Pass args for plain support

    try:
        # Command logic here
        utils.render_success("Command executed successfully!")
        return 0
    except Exception as e:
        utils.render_error(str(e))
        return 1
```

## Creating a New Command

### Step 1: Create the command function

```python
@command("newcmd", help="My new command")
@argument("message", help="Message to display")
@argument("-u", "--uppercase", action="store_true", help="Uppercase the message")
def new_command(args: Namespace, context: CommandContext) -> int:
    utils = create_utils(context, args)  # Pass args for plain support

    message = args.message.upper() if args.uppercase else args.message
    utils.render_success(message)
    return 0
```

### Step 2: Import in `__init__.py`

Add your command module to the imports in `__init__.py`:

```python
from command_line_assistant.commands import feedback, chat_simple, newcmd
```

That's it! No factories, no complex registration, no multiple inheritance.

## Available Utilities

The `CommandUtils` class provides common functionality:

### Renderers
- `utils.render_success(message)` - Success messages
- `utils.render_warning(message)` - Warning messages
- `utils.render_error(message)` - Error messages
- `utils.text_renderer` - Direct access to text renderer
- `utils.warning_renderer` - Direct access to warning renderer
- `utils.error_renderer` - Direct access to error renderer

**Note**: All renderers automatically respect the `--plain` flag if present in args.

### D-Bus Proxies
- `utils.chat_proxy` - Chat interface proxy
- `utils.history_proxy` - History interface proxy
- `utils.user_proxy` - User interface proxy

### Helper Methods
- `utils.get_user_id()` - Get current user ID
- `utils.context` - Access to command context

## Migration from Old Structure

### Old Structure (Complex)
```python
class MyOperationType(CommandOperationType):
    OPERATION = auto()

class MyOperationFactory(CommandOperationFactory):
    _arg_to_operation = {"arg": MyOperationType.OPERATION}

@MyOperationFactory.register(MyOperationType.OPERATION)
class MyOperation(BaseOperation):
    def execute(self) -> None:
        self.text_renderer.render("Hello")

class MyCommand(BaseCLICommand):
    def run(self) -> int:
        factory = MyOperationFactory()
        operation = factory.create_operation(self._args, self._context)
        operation.execute()
        return 0

def register_subcommand(parser):
    # Complex argument setup...
    pass
```

### New Structure (Simple)
```python
@command("mycommand", help="My command")
@argument("--arg", action="store_true", help="An argument")
def my_command(args: Namespace, context: CommandContext) -> int:
    utils = create_utils(context, args)  # Pass args for plain support
    utils.render_success("Hello")
    return 0
```

## Decorator Details

### @command(name, help=None, description=None)
Registers a function as a CLI command.

- `name`: Command name (required)
- `help`: Short help text (optional)
- `description`: Long description (optional)

### @argument(*args, **kwargs)
Adds an argument to the command. Uses the same signature as `argparse.add_argument()`.

**Note**: Arguments are applied in reverse order (decorators are applied bottom-up), so the last `@argument` decorator will be the first argument added to the parser.

## Examples

See `example.py` for a complete example showing:
- Positional and optional arguments
- Different argument types
- Error handling
- Using various utilities

## Error Handling

Commands should:
1. Use try/except blocks for error handling
2. Use appropriate exception types (e.g., `ChatCommandException`)
3. Render errors using `utils.render_error()`
4. Return appropriate exit codes (0 for success, non-zero for failure)

## Best Practices

1. **Keep commands simple**: Each command function should focus on one main task
2. **Use utilities**: Leverage `CommandUtils` for common operations - always pass `args` to `create_utils(context, args)` for proper plain text support
3. **Handle errors gracefully**: Always catch and handle exceptions properly
4. **Return appropriate exit codes**: 0 for success, non-zero for errors
5. **Use descriptive help text**: Make commands self-documenting
6. **Validate arguments**: Check argument validity early in the function
7. **Support plain mode**: Always pass args to create_utils() so the `--plain` flag is respected

## Handling Branching Logic

If your command has multiple operations (like the chat command with --list, --delete, etc.), you can handle this in a few ways:

### Option 1: Simple if/else in main function
```python
@command("mycommand", help="My command")
@argument("--list", action="store_true", help="List items")
@argument("--delete", help="Delete an item")
def my_command(args: Namespace, context: CommandContext) -> int:
    utils = create_utils(context, args)  # Pass args for plain support

    if args.list:
        return list_items(utils)
    elif args.delete:
        return delete_item(utils, args.delete)
    else:
        return default_behavior(utils, args)
```

### Option 2: Helper functions
```python
def _list_items(utils) -> int:
    """List items operation."""
    # Implementation here
    return 0

def _delete_item(utils, item_name: str) -> int:
    """Delete item operation."""
    # Implementation here
    return 0

@command("mycommand", help="My command")
@argument("--list", action="store_true", help="List items")
@argument("--delete", help="Delete an item")
def my_command(args: Namespace, context: CommandContext) -> int:
    utils = create_utils(context, args)  # Pass args for plain support

    if args.list:
        return _list_items(utils)
    elif args.delete:
        return _delete_item(utils, args.delete)
    else:
        # Default behavior
        return 0
```

## Legacy Support

The old base classes and factory pattern are still available in `base.py` but should be considered deprecated. New commands should use the simplified structure. The old system will be removed in a future version.
