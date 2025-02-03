"""Define the base classes and mixins for handling structures"""

from dasbus.typing import Structure


class BaseDataMixin:
    """Base mixin for data classes to handle structure conversion."""

    def structure(self) -> Structure:
        """Handle the structure conversion for dbus data class.

        Note:
            This method only exists due to the bad API from dasbus to handle
            such scenario of converting the data class to a dbus structure.

            It tries to use the underlying `to_structure` method to
            convert the parent class to a structure, but with a sane operation
            to just use `structure()` after we initialize the class.

        Returns:
            Structure: The structure representation of the data.
        """
        # We are ignoring the attribute access here because the subclass that
        # inherits this BaseDataMixin will have access to the `to_structure`
        # when initialized.
        #
        # It's weird for static analysis cases, but good for API usage in our
        # own codebase.
        return self.to_structure(data=self)  # type: ignore[reportAttributeAccessIssue]
