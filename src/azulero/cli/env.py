# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from functools import lru_cache
import os
import sys

from azulero.cli.process import default_workspace
from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
)
from azulero.tools.secret import Auth
from azulero.tools.setup import setup_wizard


@lru_cache
def azulero_prefix():
    return os.environ.get("AZULERO_PREFIX", "AZUL")


def reprefix(key, prefix):
    if key.startswith(azulero_prefix()):
        return prefix + key.removeprefix(azulero_prefix())
    return key


def current_env(prefix):
    """
    Collect all current environment variables which start with the Azulero prefix.
    """
    return {
        reprefix(k, prefix): v
        for (k, v) in os.environ.items()
        if k.startswith(azulero_prefix())
    }
    # FIXME rm password from AZULRETRIEVE_USER?


def preset_logfile(prefix):
    """
    Write logs (``stderr``) and manifest (``stdout``) to files.
    """
    stem = "{workspace}/azul_{cmd}_{utcnow:%Y-%m-%dT%H:%M:%S.%f}Z_{rand}"
    return {
        prefix + "_LOGFILE": stem + ".log",
        prefix + "_MANIFEST": stem + ".out",
    }


def preset_q1_processing(prefix):
    """
    Process with Q1 default parameters.
    """
    return {
        prefix + "PROCESS_WHITE": 22.5,
        prefix + "PROCESS_STRETCH": 28.25,
        prefix + "PROCESS_OFFSET": 29.0,
    }


def preset_otf_data(prefix):
    """
    Retrieve on-the-fly data.
    """
    return {
        prefix + "RETRIEVE_FROM": "dss",  # SAS' otf is generally outdated
        prefix + "RETRIEVE_DSR": "F-006",
    }


def preset_dss(prefix):
    """
    Retrieve on-the-fly or DR1 data from the DSS.
    """
    return {
        prefix + "RETRIEVE_FROM": "dss",
        prefix + "RETRIEVE_DSR": "F-006,DR1_R2,DR1_R1",
    }


def preset_datalabs(prefix):
    """
    Retrieve from ESA Datalabs.
    """
    return {prefix + "RETRIEVE_DATA": "labs"}


def preset_yjh_to_bgr(prefix):
    """
    Process with NIR colors only, use VIS for lightness, don't adjust hue.
    """
    return {
        prefix + "PROCESS_IB": 0,
        prefix + "PROCESS_YG": 0,
        prefix + "PROCESS_JR": 0,
        prefix + "PROCESS_HUE": 0,
    }


def preset_yjh_to_lbgr(prefix):
    """
    Process with NIR colors and lightness, don't adjust hue.
    """
    return {**preset_yjh_to_bgr(prefix), prefix + "PROCESS_NIRL": 1}


def preset_adjust_not(prefix):
    """
    Process without adjustment (hue shift, saturation gain, curves).
    """
    return {
        prefix + "PROCESS_HUE": 0,
        prefix + "PROCESS_SATURATION": 1,
        prefix + "PROCESS_CURVES": [],
    }


def preset_adjust_heavy(prefix):
    """
    Process more aggressively (heavier sharpening and saturation).
    """
    return {
        prefix + "PROCESS_SHARPEN": 0.7,
        prefix + "PROCESS_SATURATION": 1.4,
    }


def preset_process_jpg(prefix):
    """
    Process as JPG.
    """
    return {
        prefix
        + "PROCESS_OUTPUT": default_workspace.output_template.replace(".tiff", ".jpg")
    }


def preset_process_png(prefix):
    """
    Process as PNG.
    """
    return {
        prefix
        + "PROCESS_OUTPUT": default_workspace.output_template.replace(".tiff", ".png")
    }


presets = {
    "current": current_env,
    "logfile": preset_logfile,
    "otf": preset_otf_data,
    "dss": preset_dss,
    "datalabs": preset_datalabs,
    "yjh-bgr": preset_yjh_to_bgr,
    "yjh-lbgr": preset_yjh_to_lbgr,
    "adjust-not": preset_adjust_not,
    "process-q1": preset_q1_processing,
    "process-heavy": preset_adjust_heavy,
    "process-jpg": preset_process_jpg,
    "process-png": preset_process_png,
}


def print_user(prefix):
    """
    Print the user name and password.

    This command should ONLY be used to export the user credential for pipelines.
    See :ref:`printuser`.
    """
    if sys.stdout.isatty():
        raise RuntimeError(
            "This command will print your credentials to stdout. "
            "It can only be used within a pipeline or as an expression, e.g.: "
            "``export $(azul env print-user)``."
        )
    auth = Auth("", None)
    line = f"{prefix}RETRIEVE_USER='{auth.user}:{auth.password.value}'"
    print(line)


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
    parser.add_argument("--setup", action="store_true", help="Start the setup wizard.")

    parser.set_defaults(**parse_envargs("env"), func=run)


def run(args):

    if args.setup:
        setup_wizard(args.workspace, args.prefix)
        return

    if not args.variables:
        return list_presets(args.prefix)

    if "print-user" in args.variables:
        if len(args.variables) != 1:
            raise ValueError(
                "Special value ``set-user`` cannot be used in combination with other presets."
            )
        print_user(args.prefix)
        return

    environment = {}
    for arg in args.variables:
        if "=" in arg:
            k, v = arg.split("=")
            environment[reprefix(k, args.prefix)] = v
        else:
            environment.update(presets[arg.lower()](args.prefix))
    lines = [f"{e}={environment[e]}" for e in environment]
    write_pipe_args(lines, sh=False)


def list_presets(prefix):
    logger.header(1, "Available presets (name, description, variables)")
    for p in presets:
        preset = presets[p]
        logger.header(2, '"' + p + '"')
        desc = preset.__doc__ or "No description available."
        desc = desc.removeprefix("\n").removesuffix("\n")
        logger.header(3, desc)
        preset = preset(prefix)
        if not preset:
            logger.info("No variable defined.")
        for k in preset:
            logger.bullet(f"{k}={preset[k]}")
