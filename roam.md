# Roam

## Basics

Command `azul roam` consists in moving a so-called viewport,
a rectangle from which video frames are extracted.
The image and viewport can be seen as analogous to a scene and camera, respectively.

The viewport has a variable center, scale and rotation angle.
The parameters evolve smoothly between key frames specified by the user.
Between them, the viewport geometry is sine-interpolated.

## Sequence file

The sequence of key frames is provided to `azul roam` as a configuration file in YAML format.
For each key frame:

- The time is specified either in seconds or in number of frames.
- The center is specified either in pixels or percentage of the image extents.
- The viewport size is computeded either from a percentage relative to the image pixel size, or relatively to the image extents.
- The viewport angle is specified clockwise.

For each key frame but the first one, omitted parameters are copied from the previous key frame.

**Time**

The name of the key frame time parameter in the sequence file is `t`.
It is specified in seconds with suffix `s` or number of frames with suffix `f`.
Prefix `+` indicates a duration instead of a time point, e.g.:
`t: 1s` means key frame at 1 second, `t: +24f` means 24 frames after the previous key frame.
The time of the first frame must be `0s` or `0f`.

**Center**

Viewport center is given with keys `x` and `y`.
Suffix `px` indicates absolute coordinates, while suffix `%` indicates percentage relative to the image width or height.
Negative values are interpreted as backward coordinates, i.e. from the right for `x` or from the bottom for `y`.
Typically, the viewport can be centered with `x: 50%` and `y: 50%`.

**Zoom**

Zoom is specified with key `z`.
When suffixed with `%`, the parameter is interpretted as relative to the pixel size,
such that `z: 100%` means that one pixel in the input image corresponds to one pixel in the output frame.
When suffixed with `w` (resp. `h`), the parameter value is a factor wrt. the image width (resp. height).
Typically, a full-width viewport is specified as `z: 1w` and a full-height viewport is specified as `z: 1h`.

For now, zoom levels higher than 100% are not supported.

**Angle**

The angle parameter has key `a` and is given either in degrees with suffix `°` or in radians with suffix `pi`.
Its value is arbitrary to allow for multi-turns videos.
Typically, with `a: 0pi` in a key frame and `a: 4pi` in the next one, the viewport would perform two full turns.
Positive values mean clockwise rotation of the viewport, i.e. counterclockwise rotation of the image.

**Zoom and/or angle elision**

While all parameters can be omitted to denote no change from the previous frame,
zoom and angle parameters support key frame elision, with the ellipsis syntax: `...`.
In this case, for the zoom and/or angle parameters, it is like the key frame did not exist.
This means the interpolation runs from the frame immediately before elipsis until that immediately after ellipsis.
Several successive key frames can be eluded, as demonstrated in the following example.

**Example**

Consider the following sequence:

```yaml
- t: 0s
  x: 50%
  y: 50%
  z: 1h
  a: 0°

- t: +1s
  a: ...

- t: +10s
  x: 87%
  y: 57%
  z: 0.2w
  a: ...

- t: +5s
  a: ...

- t: +10s
  x: 60%
  y: 72%
  z: 100%
  a: ...

- t: +5s
  a: -90°

- t: +5s
  x: 50%
  y: 50%
  z: 1h

- t: +1s
```

It consists in eight key frames.
The video starts with a full-height, centered and horizontal viewport.

For one second, there is only a viewport rotation
-- which will run continuously until the sixth key frame to reach 90° clockwise rotation of the image.

Then, in ten seconds, the viewport moves to position (87%, 57%) relative to the image extents,
and we zoom until we the viewport width reaches 20% of the image width.

For the next five seconds, only the angle parameter continues to evolve.

For ten seconds, we pan to position (60%, 72%) and zoom to 100% pixel size.

Five seconds later, rotation stops.

In the next five seconds, we go back to the center of the image and zoom out to reach full image height again.
The viewport finally stays still for one second.
