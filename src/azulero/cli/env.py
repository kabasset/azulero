# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from functools import lru_cache
import os

from azulero.cli.process import default_transform, default_workspace
from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
)
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


def preset_q1_data(prefix):
    """
    Retrieve Q1 data.
    """
    return {
        prefix + "RETRIEVE_FROM": "pdr",
        prefix + "RETRIEVE_DSR": "Q1_R1",
    }


def preset_q1_processing(prefix):
    """
    Process with Q1 default parameters.
    """
    return {
        prefix + "PROCESS_WHITE": 22.5,
        prefix + "PROCESS_STRETCH": 28.25,
        prefix + "PROCESS_BLACK": 29.0,
    }


def preset_q1(prefix):
    """
    Retrieve Q1 data and process with Q1 default parameters.
    """
    return {**preset_q1_data(prefix), **preset_q1_processing(prefix)}


def preset_dr1_data(prefix):
    """
    Retrieve DR1 data.
    """
    return {
        prefix + "RETRIEVE_DSR": "DR1_R1,DR1_R2",
    }


def preset_pdr(prefix):
    """
    Retrieve public data.
    """
    return {prefix + "RETRIEVE_FROM": "pdr"}


def preset_otf_data(prefix):
    """
    Retrieve on-the-fly data.
    """
    return {
        prefix + "RETRIEVE_FROM": "otf",
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
    Process with NIR colors only.
    """
    return {
        prefix + "PROCESS_IB": 0,
        prefix + "PROCESS_YG": 0,
        prefix + "PROCESS_JR": 0,
        prefix + "PROCESS_HUE": 0,
    }


def preset_yhj_to_lbgr(prefix):
    """
    Process with NIR colors and lightness only.
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


def preset_process_heavy(prefix):
    """
    Process more aggressively (heavier sharpening, saturation, overflow clipping).
    """
    return {
        prefix + "PROCESS_FWHM": tuple(w * 1.5 for w in default_transform.iyjh_fwhm),
        prefix + "PROCESS_SHARPEN": 0.7,
        prefix + "PROCESS_SATURATION": 1.4,
        prefix + "PROCESS_OVERFLOW": 0.1,
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
    "q1-data": preset_q1_data,
    "q1-processing": preset_q1_processing,
    "q1": preset_q1,
    "dr1": preset_dr1_data,
    "pdr": preset_pdr,
    "otf": preset_otf_data,
    "dss": preset_dss,
    "datalabs": preset_datalabs,
    "yjh-bgr": preset_yjh_to_bgr,
    "yjh-lbgr": preset_yhj_to_lbgr,
    "adjust-not": preset_adjust_not,
    "process-heavy": preset_process_heavy,
    "process-jpg": preset_process_jpg,
    "process-png": preset_process_png,
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
    parser.add_argument("--setup", action="store_true", help="Start the setup wizard.")

    parser.set_defaults(**parse_envargs("env"), func=run)


def run(args):
    if args.setup:
        setup_wizard(args.workspace, args.prefix)
        return
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
