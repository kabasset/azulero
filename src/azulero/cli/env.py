# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
from typing import Annotated

from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
)


def preset_q1():
    """
    Retrieval parameters and default processing parameters for Q1 data.
    """
    return {
        "RETRIEVE_FROM": "PDR",
        "RETRIEVE_DSR": "Q1",
        "PROCESS_WHITE": 22.5,
        "PROCESS_STRETCH": 28.25,
        "PROCESS_BLACK": 29.0,
    }


def preset_dr1():
    """
    Retrieval parameters for DR1 data.
    """
    return {
        "RETRIEVE_FROM": "IDR",
        "RETRIEVE_DSR": "DR1_R1,DR1_R2",
    }


def preset_otf():
    """
    Retrieval parameters for on-the-fly data.
    """
    return {
        "RETRIEVE_FROM": "OTF",
        "RETRIEVE_DSR": "F-006",
    }


def preset_datalabs():
    """
    Retrieval parameters for ESA Datalabs.
    """
    return {
        "RETRIEVE_DATA": "labs",
    }


presets = {
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
        default=os.environ.get("AZULERO_PREFIX", "AZUL"),
        metavar="PREFIX",
        help="Environment variables prefix.",
    )

    parser.set_defaults(**parse_envargs("env"), func=run)


def run(args):
    if not args.variables:
        return list_presets(args.prefix)
    variables = {}
    for arg in args.variables:
        if "=" in arg:
            k, v = arg.split("=")
            k = args.prefix + k.removeprefix(args.prefix)
            variables[k] = v
        else:
            preset = presets[arg.lower()]()
            for k in preset:
                variables[args.prefix + k] = preset[k]
    lines = [f"{v}={variables[v]}" for v in variables]
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
        for k in preset():
            logger.bullet(f"{prefix+k}={preset()[k]}")
