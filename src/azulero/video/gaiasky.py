# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import time

import numpy as np
import pathlib
from py4j.clientserver import ClientServer, JavaParameters, PythonParameters


class CameraRunnable:

    def __init__(self, api, params):
        self.base = api.base
        self.camera = api.camera
        self.refsys = api.refsys
        self.output = api.output
        self.frame = 0
        self.params = [
            [
                float(v)
                for v in (
                    p.center[0].value,  # FIXME always in degrees?
                    p.center[1].value,
                    p.hfov.value,  # FIXME compute vfov early
                    p.roll.value,
                )
            ]
            for p in params
        ]

    def run(self):
        self.output.frame_output(False)
        if self.frame < len(self.params):
            p = self.params[self.frame]
            pointing = self.refsys.equatorial_to_cartesian(p[0], p[1], 1.0)
            pointing = np.array(pointing)
            pointing /= np.linalg.norm(pointing)
            self.camera.set_direction(pointing.tolist(), True)
            self.camera.set_fov(p[2] * 9 / 16)  # FIXME compute vfov with atan
            up = camera_up(pointing, p[3])
            self.camera.set_up(up.tolist(), True)
            self.output.frame_output(True)
            self.frame += 1

    class Java:
        implements = ["java.lang.Runnable"]


def camera_up(pointing, roll):
    rad = np.deg2rad(roll)
    up = np.array([-np.sin(rad), np.cos(rad), 0])
    up_xyz = up - np.dot(up, pointing) * pointing
    return up_xyz / np.linalg.norm(up_xyz)


def roam_gaiasky(params, fps, video_format, output):

    gateway = ClientServer(
        java_parameters=JavaParameters(auto_convert=True, auto_field=True),
        python_parameters=PythonParameters(),
    )
    api = gateway.entry_point.apiv2

    api.input.disable()
    api.camera.stop()
    api.camera.free_mode()
    api.time.stop_clock()
    api.camera.set_focus_lock(True)
    api.camera.set_orientation_lock(False)
    output_dir = pathlib.Path(
        api.base.get_default_frame_output_dir()
    )  # FIXME use output
    for f in output_dir.iterdir():
        f.unlink()
    api.output.configure_frame_output(
        *video_format, fps, str(output_dir), "frame"
    )  # TODO use max fps?
    runnable = CameraRunnable(api, params)
    api.base.park_camera_runnable("azul", runnable)
    # api.output.frame_output(True)
    while runnable.frame < len(params):
        time.sleep(0.01)
    print("\nPlease close Gaia Sky!\n")
    api.base.remove_runnable("azul")
    api.camera.stop()
    api.input.enable()
    gateway.close()
    return sorted(output_dir.glob("frame*"))
