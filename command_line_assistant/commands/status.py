"""Module to handle status command."""

import logging
from argparse import Namespace
from dataclasses import dataclass
from enum import auto
from typing import ClassVar, Optional

from dasbus.error import DBusError

from command_line_assistant.commands.base import (
    BaseCLICommand,
    BaseOperation,
    CommandOperationFactory,
    CommandOperationType,
)
from command_line_assistant.dbus.constants import SYSTEM_BUS
from command_line_assistant.exceptions import StatusCommandException
from command_line_assistant.rendering.renders.text import TextRenderer
from command_line_assistant.utils.cli import SubParsersAction, create_subparser
from command_line_assistant.utils.renderers import create_error_renderer

logger = logging.getLogger(__name__)


class StatusOperationType(CommandOperationType):
    """Enum to control the operations for the command"""

    ALL = auto()
    DAEMON = auto()
    SUBSCRIPTION = auto()


class StatusOperationFactory(CommandOperationFactory):
    """Factory for creating status operations with decorator-based registration"""

    # Mapping of CLI arguments to operation types
    _arg_to_operation: ClassVar[dict[str, CommandOperationType]] = {
        "all": StatusOperationType.ALL,
        "daemon": StatusOperationType.DAEMON,
        "subscription": StatusOperationType.SUBSCRIPTION,
    }


@dataclass
class OperationResult:
    """Dataclass to hold the results of a status operation."""

    success: bool = False
    recommendation: Optional[str] = None
    message: str = ""


@dataclass
class Statuses:
    """Dataclass to hold the results of status operations."""

    results: list[OperationResult]


# Base class for status operations with common functionality
class BaseStatusOperation(BaseOperation):
    """Base status operation common to all operations."""

    def __init__(
        self,
        text_renderer,
        warning_renderer,
        error_renderer,
        args,
        context,
        chat_proxy,
        history_proxy,
        user_proxy,
    ):
        """Initialize the base status operation.
        Arguments:
            text_renderer (TextRenderer): Renderer for text output
            warning_renderer (TextRenderer): Renderer for warning output
            error_renderer (TextRenderer): Renderer for error output
            args (Namespace): Parsed command line arguments
            context: Context object for the operation
            chat_proxy: Proxy for chat operations
            history_proxy: Proxy for history operations
            user_proxy: Proxy for user operations
        """
        super().__init__(
            text_renderer,
            warning_renderer,
            error_renderer,
            args,
            context,
            chat_proxy,
            history_proxy,
            user_proxy,
        )
        self.statuses = Statuses(results=[])

    def _check_systemd_unit_present(self, unit_name: str) -> None:
        """Check if the systemd unit is available.

        Arguments:
            unit_name (str): The name of the systemd unit to check

        Returns:
            tuple[bool, str]: Success status and message
        """
        try:
            systemd_manager = SYSTEM_BUS.get_proxy(
                service_name="org.freedesktop.systemd1",
                object_path="/org/freedesktop/systemd1",
            )

            unit = systemd_manager.GetUnit(unit_name)  # type: ignore[reportOptionalCall]
            if not unit:
                logger.debug("Systemd unit '%s' does not exist.", unit_name)
                recommendation = f"""
Try the following commands to check the status of the unit:
- `systemctl status {unit_name}`
- `journalctl -u {unit_name}`
"""
                self.statuses.results.append(
                    OperationResult(
                        success=False,
                        message=f"Daemon {unit_name} is not available",
                        recommendation=recommendation,
                    )
                )
                return

            self.statuses.results.append(
                OperationResult(
                    success=True, message=f"Daemon {unit_name} is available"
                )
            )
        except DBusError as e:
            logger.debug(
                "Error while checking systemd unit '%s': %s", unit_name, str(e)
            )
            if "not loaded" in str(e):
                self.statuses.results.append(
                    OperationResult(
                        success=False,
                        message=f"Daemon {unit_name} is not loaded",
                        recommendation="Try to start the daemon with `systemctl start {unit_name}`",
                    )
                )
                return

            self.statuses.results.append(
                OperationResult(
                    success=False,
                    message=f"Could not check systemd unit {unit_name}",
                    recommendation="Ask your system administrator to check if the package is installed correctly.",
                )
            )

    def _check_user_channel_permission(self) -> None:
        """Check if the user has permission to access the channels.

        Returns:
            tuple[bool, str]: Success status and message
        """
        proxies = [
            ("Chat", self.chat_proxy),
            ("History", self.history_proxy),
            ("User", self.user_proxy),
        ]
        not_accessible_proxies = []
        for name, proxy in proxies:
            try:
                proxy.IsAllowed()
                self.statuses.results.append(
                    OperationResult(
                        success=True,
                        message=f"User has permission to access channel {name}",
                    )
                )
            except DBusError as e:
                logger.debug(
                    "User does not have permission to access channel %s: %s",
                    name,
                    str(e),
                )
                not_accessible_proxies.append(name)

        self.statuses.results.append(
            OperationResult(
                success=False,
                message=f"User does not have permission to access channel(s) {', '.join(not_accessible_proxies)}",
                recommendation="Ask your system administrator to grant you access to the channels.",
            )
        )

    def _check_subscription_status(self) -> None:
        """Check if the system is registered with subscription manager.

        Returns:
            tuple[bool, str]: Success status and message
        """
        try:
            rhsm_manager = SYSTEM_BUS.get_proxy(
                service_name="com.redhat.RHSM1",
                object_path="/com/redhat/RHSM1/Consumer",
            )

            # Call the GetUuid method to retrieve subscription status
            uuid = rhsm_manager.GetUuid("")  # type: ignore[reportOptionalCall]
            if not uuid:
                self.statuses.results.append(
                    OperationResult(
                        success=False,
                        message="System is not registered with subscription manager",
                        recommendation="Ask your system administrator to register your machine with either subscription-manager or rhc.",
                    )
                )
                return

            logger.debug("Subscription UUID: %s. System is registered.", uuid)
            self.statuses.results.append(
                OperationResult(
                    success=True,
                    message="System is registered with subscription manager",
                )
            )
        except Exception as e:
            logger.debug("Error checking subscription status: %s", str(e))
            self.statuses.results.append(
                OperationResult(
                    success=False,
                    message="Could not check subscription status",
                    recommendation="",
                )
            )

    def _display_results(self) -> None:
        """Display the results of the status checks."""
        title = "Command Line Assistant Status Check"
        self.text_renderer.render(title)
        self.text_renderer.render(len(title) * "=")

        for result in self.statuses.results:
            if result.success:
                self.text_renderer.render(f"✅ {result.message}")
            else:
                self.error_renderer.render(f"{result.message}")

                if result.recommendation:
                    self.warning_renderer.render(
                        f"Recommendation: {result.recommendation}"
                    )


@StatusOperationFactory.register(StatusOperationType.DAEMON)
class CheckDaemonStatus(BaseStatusOperation):
    """Class to check daemon status"""

    UNIT_NAME: str = "clad.service"

    def execute(self) -> None:
        """Execute the daemon status check"""
        self._check_user_channel_permission()
        self._check_systemd_unit_present(self.UNIT_NAME)

        self._display_results()


@StatusOperationFactory.register(StatusOperationType.SUBSCRIPTION)
class CheckSubscriptionStatus(BaseStatusOperation):
    """Class to check subscription status"""

    def execute(self) -> None:
        """Execute the subscription status check"""
        self._check_subscription_status()
        self._display_results()


@StatusOperationFactory.register(StatusOperationType.ALL)
class CheckAllStatus(BaseStatusOperation):
    """Class to check all statuses at once"""

    def execute(self) -> None:
        """Execute all status checks and report them together at the end"""
        self._check_user_channel_permission()
        self._check_systemd_unit_present("clad.service")

        self._check_subscription_status()

        self._display_results()


class StatusCommand(BaseCLICommand):
    """Class that represents the history command."""

    def run(self) -> int:
        """Main entrypoint for the command to run.

        Returns:
            int: Return the status code for the operation
        """
        error_renderer: TextRenderer = create_error_renderer()
        operation_factory = StatusOperationFactory()
        try:
            # Get and execute the appropriate operation
            operation = operation_factory.create_operation(
                self._args, self._context, error_renderer=error_renderer
            )
            if operation:
                operation.execute()

            return 0
        except StatusCommandException as e:
            logger.info("Failed to execute status command: %s", str(e))
            error_renderer.render(str(e))
            return 1


def register_subcommand(parser: SubParsersAction):
    """
    Register this command to argparse so it's available for the root parser.

    Arguments:
        parser (SubParsersAction): Root parser to register command-specific arguments
    """
    status_parser = create_subparser(parser, "status", "Check for system status ")

    status_parser.add_argument(
        "--all",
        action="store_true",
        help="Run all system status checks.",
    )

    status_parser.add_argument(
        "--daemon",
        action="store_true",
        help="Check if the daemon statuses are operational.",
    )
    status_parser.add_argument(
        "--subscription",
        action="store_true",
        help="Check if subscription manager is operational.",
    )

    status_parser.set_defaults(func=_command_factory)


def _command_factory(args: Namespace) -> StatusCommand:
    """Internal command factory to create the command class

    Arguments:
        args (Namespace): The arguments processed with argparse.

    Returns:
        statusCommand: Return an instance of class
    """

    args.all = True if not args.daemon and not args.subscription else args.all
    return StatusCommand(args)
