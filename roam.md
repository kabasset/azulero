# Roam

## Basics

Command `azul roam` consists in moving a so-called viewport,
that is a rectangle from which video frames are extracted.
The image and viewport can be seen as analogous to a scene and camera, respectively.

The viewport has a variable center, scale and rotation angle.
The parameters evolve smoothly between key frames specified by the user.
Between them, the viewport geometry is sine-interpolated to ensure smooth transitions.
The path of the center can also be spline-interpolated to depart from zigzag patterns.

Command line synopsis is:

```
azul roam <image> <sequence> [options]
```

with:

- `<image>` - The path to the input image file.
- `<sequence>` - The path to the sequence configuration file (see next section).
- `[options]` - Additional parameters (see below).

## Sequence file

The sequence of key frames is provided to `azul roam` as a configuration file in YAML.
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

The viewport center is given with keys `x` and `y`.
Suffix `px` indicates absolute coordinates, while suffix `%` indicates percentage relative to the image width or height.
Negative values are interpreted as backward coordinates, i.e. from the right for `x` or from the bottom for `y`.
Typically, the viewport is centered with `x: 50%` and `y: 50%`.

**Zoom**

Zoom is specified with key `z`.
When suffixed with `%`, the parameter is interpretted as relative to the pixel size,
such that `z: 100%` (resp. `z: 50%`) means that one pixel in the output frame
corresponds to one pixel (resp. two pixels) in the input image,
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
Several successive key frames can be eluded, as demonstrated in the example below.

**Spline-interpolated center**

It is possible to make the path followed by the center a spline, by defining intermediate "knots",
which are positions the center must pass through.
They are specified by providing `x` and `y` only (no time or any other parameter).
The following example is a ten-second circular trajectory with three intermediate knots:

```yaml
- t: 0s
  x: 70%
  y: 50%
  z: 100%
  a: 0°

- x: 50%
  y: 70%

- x: 30%
  y: 50%

- x: 50%
  y: 30%

- t: 10s
  x: 70%
  y: 50%
```

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

## Command line options

In addition to the input image file and sequence configuration file,
static parameters can be adjusted with command line options.

The frame format is specified with `--format` and the frame rate with `--fps`.
For example, a 720p60 video is configured with `--format 1280 720 --fps 60`.

The output file name is given to parameter `-o`.

Check `azul roam -h` for more details.
