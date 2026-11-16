# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

from azulero.tools.messaging import colorize, header_color_codes, logger, clear_term
from azulero.tools.secret import Auth
from azulero.tools.retry import retry


def choice_str(choices: list[str]):
    return ", ".join("'" + c + "'" for c in choices[:-1]) + " or '" + choices[-1] + "'"


@retry(2, logger=logger)
def prompt_choice(prompt, choices: list[str] = ["no", "yes"]):
    logger.info("")
    answer = logger.prompt_clear(
        colorize(header_color_codes[3], prompt) + " [" + "/".join(choices) + "]"
    )
    logger.info("")
    try:
        return choices.index(answer)
    except ValueError:
        raise ValueError(f"Invalid answer. Please enter {choice_str(choices)}")


def next_step(title, validation=False):
    if validation:
        logger.info("")
        logger.prompt_obfuscated("Press Enter to continue.", echo_char=None)
    clear_term()
    logger.info("")
    logger.header(1, title)


def setup_wizard(workspace: Path, prefix: str):

    clear_term()
    logger.header(1, "Welcome to the setup wizard!")
    logger.info(
        "This tool will help you configure data retrieval "
        "according to the type of environment you're in."
    )

    if prompt_choice("Are you in ESA Datalabs?"):
        next_step("ESA Datalabs setup")
        setup_datalabs(workspace, prefix)
    elif prompt_choice(
        "Are you in another shared environment such as a computing center?"
    ):
        next_step("Shared environment setup")
        setup_shared(workspace, prefix)
    else:
        next_step("Authentication setup")
        setup_secrets(workspace, prefix)

    next_step("Setup complete!", True)
    logger.info(f"You can now use Azulero commands, e.g.:")
    logger.command("azul retrieve UGC11169 -r 30s | azul process")
    logger.info(
        f"Don't forget to read the docs: "
        + colorize(
            header_color_codes[2],
            "https://kabasset.github.io/azulero/develop/quickstart.html",
        )
    )


def setup_datalabs(workspace: Path, prefix: str):
    ev = prefix + "RETRIEVE_DATA=labs"
    logger.info(
        f"We can enforce direct data retrieval from the Datalabs (no downloads) in this workspace. "
        f"This is configured by storing the dedicated environment variable ({ev}) in: {workspace.absolute()}/.env"
    )
    if prompt_choice(f"Do you want me to edit this file?"):
        with open(workspace / ".env", "a") as f:
            f.write(ev + "\n")
    else:
        logger.info("Feel free to set the following variable yourself:")
        logger.command(ev)

    next_step("Shared environment setup", True)
    setup_shared(workspace, prefix)


def setup_shared(workspace: Path, prefix: str):
    unix_command = "export $(azul env print-user)"
    windows_command = "for /f %%x in ('azul env print-user') do set " + '"%%x"'
    command = windows_command if os.name == "nt" else unix_command
    logger.info(
        "In shared environments, we do not store secrets. "
        "To avoid leaving traces, you will have to authenticate at the beginning of each terminal session. "
        "Your credentials are forgotten when the session closes. "
        "To this end, please run the following command each time you start a new session:"
    )
    logger.command(command)
    pass


def setup_secrets(workspace: Path, prefix: str):
    logger.warning(
        "The wizard will ask for your credentials. "
        "If you don't want to store your user name or password, just press Enter."
    )
    logger.header(2, "ESA Cosmos authentication")
    cosmos_auth = setup_cosmos()
    write_to_netrc(cosmos_auth, "easidr.esac.esa.int")

    logger.header(2, "SGS authentication")
    if prompt_choice("Are you an SGS member?"):
        eas_auth = setup_eas(cosmos_auth)
        write_to_netrc(eas_auth, "eas-dps-rest-ops.esac.esa.int")
        write_to_netrc(eas_auth, "euclidsoc.esac.esa.int")


def setup_cosmos():
    return Auth("cosmos.esa.int", None)


def setup_eas(cosmos_auth):
    if prompt_choice("Do you want to use your Cosmos account to access the DPS/DSS?"):
        return cosmos_auth
    return Auth("EAS DPS/DSS", None)


def write_to_netrc(auth: Auth, host: str = ""):
    machine = host or auth.host
    netrc = Path.home() / ".netrc"

    # FIXME check if machine already exists

    os.umask(0)
    descriptor = os.open(
        path=netrc,
        flags=(os.O_WRONLY | os.O_CREAT),
        mode=0o600,
    )

    with open(descriptor, "a+") as f:
        user = auth.user
        if user:
            logger.info(f"Store user name for {machine}.")
            f.write(f"machine {machine}\n")
            f.write(f"  login {user}\n")
            password = auth.password.value
            if password:
                logger.info(f"Store password for {machine}.")
                f.write(f"  password {password}\n")
        else:
            logger.warning(f"No user name given for {machine}. Skip.")
