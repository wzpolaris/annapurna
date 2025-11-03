# Tools

Place the `ffmpeg` executable in this directory so the simulation runner can
convert recorded `.webm` captures into `.mp4` files automatically.

Example layout:

```
simulation/
  tools/
    ffmpeg        # executable binary
```

Alternatively, update `simulation/config.py` with the path to an existing
`ffmpeg` installation on your system.
