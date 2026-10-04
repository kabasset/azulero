# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

from azulero.tools.messaging import colorize, header_color_codes, logger, clear_term
from azulero.tools.secret import prompt_clear, prompt_obfuscated, Auth
from azulero.tools.retry import retry


def choice_str(choices: list[str]):
    return ", ".join("'" + c + "'" for c in choices[:-1]) + " or '" + choices[-1] + "'"


@retry(2, logger=logger)
def prompt_choice(prompt, choices: list[str] = ["no", "yes"]):
    answer = prompt_clear(prompt + " [" + "/".join(choices) + "]")
    try:
        return choices.index(answer)
    except ValueError:
        raise ValueError(f"Invalid answer. Please enter {choice_str(choices)}")


def setup_wizard(workspace: Path, prefix: str):

    clear_term()
    logger.header(1, "Welcome to the setup wizard!")

    if prompt_choice("Are you a Euclid Consortium member?"):
        clear_term()
        setup_euclid(workspace, prefix)
    else:
        clear_term()
        setup_public(workspace, prefix)

    logger.info("")
    prompt_obfuscated("Press Enter to continue.", echo_char=None)  # Wait for Enter
    clear_term()
    logger.header(1, "Setup complete!")
    logger.info(f"You can now use Azulero commands, e.g.:")
    logger.command("azul retrieve UGC11169 -r 30s | azul process -w 0")
    logger.info(
        f"Don't forget to read the docs: "
        + colorize(
            header_color_codes[2],
            "https://kabasset.github.io/azulero/develop/quickstart.html",
        )
    )


def setup_public(workspace: Path, prefix: str):
    logger.header(1, "Access to public data")
    logger.header(2, "Verify the workspace")

    if prompt_choice(
        f"Currently configured workspace is '{str(workspace.absolute())}'. "
        f"Do you want to change it?"
    ):
        workspace = Path(prompt_clear("Please enter a new workspace:"))
    workspace.mkdir(parents=True, exist_ok=True)

    logger.header(2, "Set the data provider to 'pdr'")

    dotenv = workspace / ".env"
    cmd = "azul env pdr >> " + str(dotenv)

    logger.info("The following command should be run before working with Azulero:")
    logger.command(cmd)
    if prompt_choice("Do you want me to run it?"):
        with open(dotenv, "a+") as f:
            f.write(prefix + "RETRIEVE_FROM=PDR\n")
    else:
        logger.info("It's your choice!")


def setup_euclid(workspace: Path, prefix: str):
    logger.warning(
        "The wizard will ask for your credentials. "
        "If you don't want to store your username or password, just press Enter."
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
            logger.warning(f"No username given for {machine}. Skip.")
