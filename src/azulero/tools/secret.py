from dataclasses import dataclass
import getpass
import netrc


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
    def prompt(cls, text: str, echo_char: str = "*"):
        """
        Prompt the user for a secret without echoing.

        Args:
            text:
                The prompt text.
            echo_char:
                The obfuscated character to display instead of input characters.
        """
        # TODO log prompt as warning?
        return cls(getpass.getpass(prompt=text, echo_char=echo_char))


class Auth:

    def __init__(self, host: str | dict, user: str | None):
        self.host = host
        if user is None:
            auth = netrc.netrc().authenticators(self.host)
            # FIXME raise if None
            self.user = auth[0]
            self.password = Secret(auth[2])
        else:
            self.user = user
            self.password = Secret.prompt(f"Password for user {user}: ")
