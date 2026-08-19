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
                The obfuscated character to display instead of input characters (if supported).
        """
        # TODO log prompt as warning?
        try:
            return cls(getpass.getpass(prompt=text, echo_char=echo_char))
        except TypeError:
            return cls(getpass.getpass(prompt=text))


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

    def _prompt_clear_text(self, text):
        return input(text)

    def _prompt_user(self):
        self.user = self._prompt_clear_text(f"Enter user name for host {self.host}: ")

    def _prompt_password(self):
        self.password = Secret.prompt(f"Enter password for {self.user}@{self.host}: ")
