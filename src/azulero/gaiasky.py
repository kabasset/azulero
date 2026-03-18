# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from py4j.clientserver import ClientServer, JavaParameters


class CameraRunnable:

    def __init__(self, gs, params):
        self.gs = gs
        self.frame = 0
        self.params = params
        self.gs.setFrameOutput(True)
        self.gs.parkRunnable("azul", self)

    def run(self):
        print(f"{self.frame=}")
        p = self.params[self.frame]
        pointing = self.gs.equatorialToInternalCartesian(*p.center_in_radec(), 1.0)
        pointing = np.array(pointing)
        pointing /= np.linalg.norm(pointing)
        self.gs.setCameraDirection(pointing.tolist(), immediate=True)
        up = self._up(pointing, p.orientation_in_degrees())
        self.gs.setCameraUp(up.tolist(), immediate=True)
        self.frame += 1
        if self.frame == len(self.params):
            print("Stop runnable")
            self.gs.setFrameOutput(False)
            self.gs.unparkRunnable("azul")

    def _up(self, pointing, angle):
        up = np.array([-np.sin(angle), np.cos(angle), 0])
        up_xyz = up - np.dot(up, pointing) * pointing
        return up_xyz / np.linalg.norm(up_xyz)

    class Java:
        implements = ["java.lang.Runnable"]


class GaiaskyConnection:

    def __enter__(self, video_format, fps):
        self.gateway = ClientServer(java_parameters=JavaParameters(auto_convert=True))
        self.gs = self.gateway.entry_point
        self.output_dir = self.gs.getDefaultFramesDir()  # FIXME tmp
        self.gs.configureFrameOutput(*video_format, fps, self.output_dir, "frame")
        self.gs.setLimitFps(self.fps)
        return self

    def __exit__(self, *args):
        self.gateway.close()


def roam_gaiasky(params, video_format, fps, output):
    with GaiaskyConnection(video_format, fps) as gateway:
        CameraRunnable(gateway.gs, params)
        output_dir = gateway.output_dir
    print(output_dir)
    # FIXME combine frames as output
    print(output)
