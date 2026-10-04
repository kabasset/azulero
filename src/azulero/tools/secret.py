from dataclasses import dataclass
import netrc

from azulero.tools.messaging import logger


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
                The obfuscated character to display instead of input characters (if supported).
        """
        return cls(logger.prompt_obfuscated(text, echo_char))


class Auth:

    def __init__(self, host: str, user: str | None, file: str | None = None):
        self.host = host
        if user is None:
            try:
                auth = netrc.netrc(file).authenticators(self.host)
            except FileNotFoundError:
                auth = None
            if auth is None or not auth[0]:
                self._prompt_user()
            else:
                self.user = auth[0]
            if auth is None or not auth[2]:
                self._prompt_password()
            else:
                self.password = Secret(auth[2])
        else:
            self.user = user
            self._prompt_password()

    def _prompt_user(self):
        self.user = logger.prompt_clear(f"Enter user name for host {self.host}:")

    def _prompt_password(self):
        self.password = Secret.prompt(f"Enter password for {self.user}@{self.host}:")
