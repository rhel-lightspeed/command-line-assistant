import logging
from argparse import Namespace
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import ClassVar, Optional, Protocol, Type

from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import CommandContext
from command_line_assistant.utils.renderers import (
    create_error_renderer,
    create_text_renderer,
    create_warning_renderer,
)

logger = logging.getLogger(__name__)


class CommandOperation(Protocol):
    """Protocol that all shell operations must implement"""

    def execute(self) -> None:
        """Execute the shell operation"""
        pass


class CommandOperationType(Enum):
    pass


@dataclass
class BaseOperation:
    text_renderer: TextRenderer
    error_renderer: TextRenderer
    warning_renderer: TextRenderer

    args: Namespace
    context: CommandContext

    def __post__init__(self, args: Namespace, context: CommandContext, **kwargs):
        super().__init__(**kwargs)
        self.context = context
        self.args = args


class CommandOperationFactory:
    """Factory for creating shell operations with decorator-based registration"""

    # Class-level storage for registered operations
    _operations: ClassVar[dict[CommandOperationType, Type[CommandOperation]]] = {}

    # Mapping of CLI arguments to operation types
    _arg_to_operation: ClassVar[dict[str, CommandOperationType]] = {}

    def __init__(
        self,
        text_renderer: Optional[TextRenderer] = None,
        warning_renderer: Optional[TextRenderer] = None,
        error_renderer: Optional[TextRenderer] = None,
    ):
        self.text_renderer = text_renderer or create_text_renderer()
        self.warning_renderer = warning_renderer or create_warning_renderer()
        self.error_renderer = error_renderer or create_error_renderer()

    @classmethod
    def register(cls, operation_type: CommandOperationType):
        """Decorator to register a shell operation class"""

        def decorator(operation_class: Type[CommandOperation]):
            # Validate that the operation implements the required interface
            if not hasattr(operation_class, "execute"):
                raise ValueError(
                    f"Operation class {operation_class.__name__} must implement 'execute' method"
                )

            # Prevent duplicate registrations
            if operation_type in cls._operations:
                raise ValueError(
                    f"Operation type {operation_type} is already registered to {cls._operations[operation_type].__name__}"
                )

            cls._operations[operation_type] = operation_class

            @wraps(operation_class)
            def wrapped_class(*args, **kwargs):
                return operation_class(*args, **kwargs)

            logger.debug(
                "Registered operation %s for type %s",
                operation_class.__name__,
                operation_type,
            )
            return wrapped_class

        return decorator

    def create_operation(
        self, args: Namespace, context: CommandContext
    ) -> Optional[CommandOperation]:
        """Create an operation instance based on command line arguments"""
        # Find the first matching argument that is True
        operation_type = next(
            (
                op_type
                for arg_name, op_type in self._arg_to_operation.items()
                if getattr(args, arg_name, False)
            ),
            None,
        )

        if operation_type is None:
            return None

        operation_class = self._operations.get(operation_type)
        if operation_class is None:
            logger.warning("No operation registered for type %s", operation_type)
            return None

        return operation_class(
            text_renderer=self.text_renderer,  # type: ignore
            warning_renderer=self.warning_renderer,  # type: ignore
            error_renderer=self.error_renderer,  # type: ignore
            args=args,  # type: ignore
            context=context,  # type: ignore
        )
