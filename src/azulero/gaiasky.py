# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import time

import numpy as np
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
                    p.center.ra.value,
                    p.center.dec.value,
                    p.hfov.value,
                    p.orientation.value,
                )
            ]
            for p in params
        ]

    def run(self):
        print(f"{self.frame=}")
        if self.frame < len(self.params):
            p = self.params[self.frame]
            print(p)
            pointing = self.refsys.equatorial_to_cartesian(p[0], p[1], 1.0)
            print(f"{pointing=}")
            pointing = np.array(pointing)
            print(f"{pointing=}")
            pointing /= np.linalg.norm(pointing)
            print(f"{pointing=}")
            self.camera.set_direction(pointing.tolist(), True)
            print("set_direction()")
            self.camera.set_fov(p[2] * 9 / 16)  # FIXME compute vfov with atan
            print("set_fov()")
            up = camera_up(pointing, p[3])
            print(f"{up=}")
            self.camera.set_up(up.tolist(), True)
            print("set_up()")
            self.frame += 1
            print(f"{self.frame=}")

    class Java:
        implements = ["java.lang.Runnable"]


def camera_up(pointing, orientation):
    rad = np.deg2rad(orientation)
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
    output_dir = api.base.get_default_frame_output_dir()  # FIXME tmp
    api.output.configure_frame_output(
        *video_format, fps, output_dir, "frame"
    )  # FIXME use max fps
    runnable = CameraRunnable(api, params)
    api.output.frame_output(True)
    api.base.park_camera_runnable("azul", runnable)
    print(params)
    while runnable.frame < len(params):
        time.sleep(0.05)
    api.output.frame_output(False)
    api.base.remove_runnable("azul")
    api.camera.stop()
    api.input.enable()
    gateway.close()
    output_dir = gateway.output_dir
    print(output_dir)
    # FIXME combine frames as output
    print(output)
