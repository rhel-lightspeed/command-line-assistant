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

        Arguments:
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

        Arguments:
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

        Arguments:
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

        Arguments:
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

        Arguments:
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

        Arguments:
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

        Arguments:
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

        Arguments:
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

        Arguments:
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

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._stdin = value


class TerminalInput(BaseDataMixin, DBusData):
    """Represents an terminal input"""

    def __init__(self, output: Str = "") -> None:
        """Constructor of the class

        Arguments:
            output (Str): Output from terminal, if any
        """
        self._output: Str = output

    @property
    def output(self) -> Str:
        """Property for internal stdin attribute.

        Returns:
            Str: Value of stdin
        """
        return self._output

    @output.setter
    def output(self, value: Str) -> None:
        """Set a new output

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._output = value


class SystemInfo(BaseDataMixin, DBusData):
    """Represents system information"""

    def __init__(
        self, os: Str = "", version: Str = "", arch: Str = "", id: Str = ""
    ) -> None:
        """Constructor of the class

        Arguments:
            os (Str): The operating system
            version (Str): The version of the operating system
            arch (Str): The architecture of the operating system
            id (Str): The unique identifier of the operating system
        """
        self._os = os
        self._version = version
        self._arch = arch
        self._id = id

    @property
    def os(self) -> Str:
        """Property for internal os attribute.

        Returns:
            Str: Value of os
        """
        return self._os

    @os.setter
    def os(self, value: Str) -> None:
        """Set a new os

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._os = value

    @property
    def version(self) -> Str:
        """Property for internal version attribute.

        Returns:
            Str: Value of version
        """
        return self._version

    @version.setter
    def version(self, value: Str) -> None:
        """Set a new version

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._version = value

    @property
    def arch(self) -> Str:
        """Property for internal arch attribute.

        Returns:
            Str: Value of arch
        """
        return self._arch

    @arch.setter
    def arch(self, value: Str) -> None:
        """Set a new arch

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._arch = value

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

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._id = value


class Question(BaseDataMixin, DBusData):
    """Represents the input message to be sent to the backend"""

    def __init__(
        self,
        message: Str = "",
        stdin: Optional[StdinInput] = None,
        attachment: Optional[AttachmentInput] = None,
        terminal: Optional[TerminalInput] = None,
        systeminfo: Optional[SystemInfo] = None,
    ) -> None:
        """Constructor of the class.

        Arguments:
            message (Str): The user message
            stdin (Optional[StdinInput], optional): The stdin object if any
            attachment (Optional[AttachmentInput], optional): The attachment input if any
            terminal (Optional[TerminalInput], optional): The terminal input if any
            systeminfo (Optional[SystemInfo], optional): The system info if any
        """
        self._message: Str = message
        self._stdin: StdinInput = stdin or StdinInput()
        self._attachment: AttachmentInput = attachment or AttachmentInput()
        self._terminal: TerminalInput = terminal or TerminalInput()
        self._systeminfo: SystemInfo = systeminfo or SystemInfo()

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

        Arguments:
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

        Arguments:
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

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._attachment = value

    @property
    def terminal(self) -> TerminalInput:
        """Property for internal terminal_contents attribute.

        Returns:
            Str: Value of terminal
        """
        return self._terminal

    @terminal.setter
    def terminal(self, value: TerminalInput) -> None:
        """Set a new terminal_contents

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._terminal = value

    @property
    def systeminfo(self) -> SystemInfo:
        """Property for internal systeminfo attribute.

        Returns:
            Str: Value of systeminfo
        """
        return self._systeminfo

    @systeminfo.setter
    def systeminfo(self, value: SystemInfo) -> None:
        """Set a new systeminfo

        Arguments:
            value (Str): Value to be set to the internal property
        """
        self._systeminfo = value


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

        Arguments:
            value (Str): Message to be set to the internal property
        """
        self._message = value
