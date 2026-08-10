from dataclasses import dataclass
import getpass


@dataclass
class Secret:
    """
    A foolproof secret (e.g. password) wrapper, string representation of which returns an obfuscated text.

    This class does not bring any kind of security.
    It only ensures that printing or logging the secret will obfuscate it.
    Getting the secret in clear form requires explicit call to member ``value``.
    """

    value: object  #: The secret in clear form
    obfuscated: str = "X" * 8  #: The obfuscated secret text

    def __repr__(self):
        return self.obfuscated

    @classmethod
    def prompt(cls, text, char="*"):
        """
        Prompt the user for a secret without echoing.
        """
        return cls(getpass.getpass(prompt=text + ": ", echo_char=char))
