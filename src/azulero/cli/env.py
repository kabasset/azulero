# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from functools import lru_cache
import os

from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
)


@lru_cache
def azulero_prefix():
    return os.environ.get("AZULERO_PREFIX", "AZUL")


def reprefix(key, prefix):
    if key.startswith(azulero_prefix()):
        return prefix + key.removeprefix(azulero_prefix())
    return key


def current_env(prefix):
    """
    All Azulero environment variables currently defined.
    """
    return {
        reprefix(k, prefix): v
        for (k, v) in os.environ.items()
        if k.startswith(azulero_prefix())
    }


def preset_q1(prefix):
    """
    Retrieval parameters and default processing parameters for Q1 data.
    """
    return {
        prefix + "RETRIEVE_FROM": "PDR",
        prefix + "RETRIEVE_DSR": "Q1_R1",
        prefix + "PROCESS_WHITE": 22.5,
        prefix + "PROCESS_STRETCH": 28.25,
        prefix + "PROCESS_BLACK": 29.0,
    }


def preset_dr1(prefix):
    """
    Retrieval parameters for DR1 data.
    """
    return {
        prefix + "RETRIEVE_FROM": "IDR",
        prefix + "RETRIEVE_DSR": "DR1_R1,DR1_R2",
    }


def preset_otf(prefix):
    """
    Retrieval parameters for on-the-fly data.
    """
    return {
        prefix + "RETRIEVE_FROM": "OTF",
        prefix + "RETRIEVE_DSR": "F-006",
    }


def preset_datalabs(prefix):
    """
    Retrieval parameters for ESA Datalabs.
    """
    return {
        prefix + "RETRIEVE_DATA": "labs",
    }


presets = {
    "current": current_env,
    "q1": preset_q1,
    "dr1": preset_dr1,
    "otf": preset_otf,
    "datalabs": preset_datalabs,
}


def add_parser(subparsers, help):

    parser = subparsers.add_parser(
        "env",
        help=help,
        description=(
            "Set predefined and custom environment variables. "
            "The command outputs a list of variables which can be written to a .env file, e.g.: "
            "``azul env dr1 datalabs AZULPROCESS_WHITE=0 > .env``"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "variables",
        type=str,
        nargs="*",
        default=read_pipe_args(),
        help=(
            "Ordered list of preset names and/or variables: "
            "arguments which contain ``=`` are considered variables. "
            "If empty, print the list of available presets."
        ),
    )
    parser.add_argument(
        "--prefix",
        default=azulero_prefix(),
        metavar="PREFIX",
        help="Environment variables prefix. Defaults to the Azulero prefix.",
    )

    parser.set_defaults(**parse_envargs("env"), func=run)


def run(args):
    if not args.variables:
        return list_presets(args.prefix)
    environment = {}
    for arg in args.variables:
        if "=" in arg:
            k, v = arg.split("=")
            environment[reprefix(k, args.prefix)] = v
        else:
            environment.update(presets[arg.lower()](args.prefix))
    lines = [f"{e}={environment[e]}" for e in environment]
    write_pipe_args(lines)


def list_presets(prefix):
    logger.header(
        1, "Available presets (name, description, variables)", linebreaks=[1, 0]
    )
    for p in presets:
        preset = presets[p]
        logger.header(2, '"' + p + '"')
        desc = (
            preset.__doc__.removeprefix("\n").removesuffix("\n")
            or "No description available."
        )
        logger.header(3, desc, linebreaks=[0, 1])
        preset = preset(prefix)
        if not preset:
            logger.info("No variable defined.")
        for k in preset:
            logger.bullet(f"{k}={preset[k]}")
