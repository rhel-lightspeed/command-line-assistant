"""D-Bus structures that defines and powers our chat."""

from typing import Optional

from dasbus.structure import DBusData
from dasbus.typing import List, Str

from command_line_assistant.dbus.structures.base import BaseDataMixin


class ChatEntry(BaseDataMixin, DBusData):
    """Represents a single chat item."""

    def __init__(
        self,
        id: Str = "",
        name: Str = "",
        description: Str = "",
        created_at: Str = "",
        updated_at: Str = "",
        deleted_at: Str = "",
    ) -> None:
        """Construct of the class

        Arguments:
            id (Str): The unique identifier for the chat
            name (Str): The name of the chat
            description (Str): The description of the chat
            created_at (Str): Timestamp to identify when it was created
            updated_at (Str): Timestamp to identify when it was updated
            deleted_at (Str): Timestamp to identify when it was deleted
        """
        self._id: Str = id
        self._name: Str = name
        self._description: Str = description
        self._created_at: Str = created_at
        self._updated_at: Str = updated_at
        self._deleted_at: Str = deleted_at

        super().__init__()

    @property
    def id(self) -> Str:
        """Property for internal id attribute.

        Returns:
            Str: Value of id
        """
        return self._id

    @id.setter
    def id(self, value: Str) -> None:
        """Set a new id

        Args:
            value (Str): Value to be set to the internal property
        """
        self._id = value

    @property
    def name(self) -> Str:
        """Property for internal name attribute.

        Returns:
            Str: Value of name
        """
        return self._name

    @name.setter
    def name(self, value: Str) -> None:
        """Set a new name

        Args:
            value (Str): Value to be set to the internal property
        """
        self._name = value

    @property
    def description(self) -> Str:
        """Property for internal description attribute.

        Returns:
            Str: Value of description
        """
        return self._description

    @description.setter
    def description(self, value: Str) -> None:
        """Set a new description

        Args:
            value (Str): Value to be set to the internal property
        """
        self._description = value

    @property
    def created_at(self) -> Str:
        """Property for internal created_at attribute.

        Returns:
            Str: Value of created_at
        """
        return self._created_at

    @created_at.setter
    def created_at(self, value: Str) -> None:
        """Set a new created_at

        Args:
            value (Str): Value to be set to the internal property
        """
        self._created_at = value

    @property
    def updated_at(self) -> Str:
        """Property for internal updated_at attribute.

        Returns:
            Str: Value of updated_at
        """
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: Str) -> None:
        """Set a new updated_at

        Args:
            value (Str): Value to be set to the internal property
        """
        self._updated_at = value

    @property
    def deleted_at(self) -> Str:
        """Property for internal deleted_at attribute.

        Returns:
            Str: Value of deleted_at
        """
        return self._deleted_at

    @deleted_at.setter
    def deleted_at(self, value: Str) -> None:
        """Set a new deleted_at

        Args:
            value (Str): Value to be set to the internal property
        """
        self._deleted_at = value


class ChatList(BaseDataMixin, DBusData):
    """Represents a list of chats"""

    def __init__(self, chats: Optional[List[ChatEntry]] = None) -> None:
        """Constructor of the class

        Arguments:
            chats (Optional[List[ChatEntry]], optional): List of chat entries to hold.
        """
        self._chats: List[ChatEntry] = chats or []
        super().__init__()

    @property
    def chats(self) -> List[ChatEntry]:
        """Property for internal chats attribute.

        Returns:
            Str: Value of chats
        """
        return self._chats

    @chats.setter
    def chats(self, value: List[ChatEntry]) -> None:
        """Set a new chats

        Args:
            value (List[ChatEntry]): Value to be set to the internal property
        """
        self._chats = value


class AttachmentInput(BaseDataMixin, DBusData):
    """Represents an attachment input"""

    def __init__(self, contents: Str = "", mimetype: Str = "") -> None:
        """Constructor of the class

        Arguments:
            contents (Str): The contentsz of an attachment
            mimetype (Str): The mimetype of the attachment
        """
        self._contents: Str = contents
        self._mimetype: Str = mimetype

    @property
    def contents(self) -> Str:
        """Property for internal contents attribute.

        Returns:
            Str: Value of contents
        """
        return self._contents

    @contents.setter
    def contents(self, value: Str) -> None:
        """Set a new contents

        Args:
            value (Str): Value to be set to the internal property
        """
        self._contents = value

    @property
    def mimetype(self) -> Str:
        """Property for internal mimetype attribute.

        Returns:
            Str: Value of mimetype
        """
        return self._mimetype

    @mimetype.setter
    def mimetype(self, value: Str) -> None:
        """Set a new mimetype

        Args:
            value (Str): Value to be set to the internal property
        """
        self._mimetype = value


class StdinInput(BaseDataMixin, DBusData):
    """Represents an stdin input"""

    def __init__(self, stdin: Str = "") -> None:
        """Constructor of the class

        Arguments:
            stdin (Str): Stdin input if any
        """
        self._stdin: Str = stdin

    @property
    def stdin(self) -> Str:
        """Property for internal stdin attribute.

        Returns:
            Str: Value of stdin
        """
        return self._stdin

    @stdin.setter
    def stdin(self, value: Str) -> None:
        """Set a new stdin

        Args:
            value (Str): Value to be set to the internal property
        """
        self._stdin = value


class Question(BaseDataMixin, DBusData):
    """Represents the input message to be sent to the backend"""

    def __init__(
        self,
        message: Str = "",
        stdin: Optional[StdinInput] = None,
        attachment: Optional[AttachmentInput] = None,
    ) -> None:
        """Constructor of the class.

        Arguments:
            message (Str): The user message
            stdin (Optional[StdinInput], optional): The stdin object if any
            attachment (Optional[AttachmentInput], optional): The attachment input if any
        """
        self._message: Str = message
        self._stdin: StdinInput = stdin or StdinInput()
        self._attachment: AttachmentInput = attachment or AttachmentInput()

        super().__init__()

    @property
    def message(self) -> Str:
        """Property for internal message attribute.

        Returns:
            Str: Value of message
        """
        return self._message

    @message.setter
    def message(self, value: Str) -> None:
        """Set a new message

        Args:
            value (Str): Question to be set to the internal property
        """
        self._message = value

    @property
    def stdin(self) -> StdinInput:
        """Property for internal stdin attribute.

        Returns:
            Str: Value of stdin
        """
        return self._stdin

    @stdin.setter
    def stdin(self, value: StdinInput) -> None:
        """Set a new stdin

        Args:
            value (Str): Value to be set to the internal property
        """
        self._stdin = value

    @property
    def attachment(self) -> AttachmentInput:
        """Property for internal attachment_contents attribute.

        Returns:
            Str: Value of attachment_contents
        """
        return self._attachment

    @attachment.setter
    def attachment(self, value: AttachmentInput) -> None:
        """Set a new attachment_contents

        Args:
            value (Str): Value to be set to the internal property
        """
        self._attachment = value


class Response(BaseDataMixin, DBusData):
    """Base class for message input and output"""

    def __init__(self, message: Str = "") -> None:
        """Constructor of class.

        Arguments:
            message (Str): The message as response from llm.
        """
        self._message: Str = message
        super().__init__()

    @property
    def message(self) -> Str:
        """Property for internal message attribute.

        Returns:
            Str: Value of message
        """
        return self._message

    @message.setter
    def message(self, value: Str) -> None:
        """Set a new message

        Args:
            value (Str): Message to be set to the internal property
        """
        self._message = value
