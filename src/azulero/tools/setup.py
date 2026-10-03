# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

from azulero.tools.messaging import logger
from azulero.tools.secret import prompt_clear, Auth
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
    logger.header(1, "Welcome to the setup wizard!")
    logger.info("We are going to configure your access to the data providers.")

    if prompt_choice("Are you a Euclid Consortium member?"):
        setup_euclid()
    else:
        setup_public(workspace, prefix)


def setup_public(workspace: Path, prefix: str):
    if prompt_choice(
        f"Currently configured workspace is '{str(workspace.absolute())}'. "
        f"Do you want to change it?"
    ):
        workspace = Path(prompt_clear("Please enter a new workspace:"))
    workspace.mkdir(parents=True, exist_ok=True)
    logger.info(
        "The following command should be run in your workspace "
        "before working with Azulero:"
    )
    dotenv = workspace / ".env"
    cmd = "azul env pdr >> " + str(dotenv)
    logger.info(cmd)
    if prompt_choice("Do you want me to run it?"):
        with open(dotenv, "a+") as f:
            f.write(prefix + "RETRIEVE_FROM=PDR\n")
    logger.header(1, "Setup complete!", linebreaks=[1, 0])


def setup_euclid():
    logger.warning(
        "The wizard will ask for your credentials. "
        "If you don't want to store your username or password, just press Enter."
    )
    logger.header(2, "ESA Cosmos authentication")
    cosmos_auth = setup_cosmos()
    write_to_netrc(cosmos_auth, "easidr.esac.esa.int")

    logger.header(2, "SGS authentication")
    if prompt_choice("Are you an SGS member?"):
        logger.info("Let us configure the EAS/DPS authentication...")
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
    netrc = Path("~/.netrc").expanduser()  # FIXME support Windows

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
