# Carrier-board design references

- [Teensy / encoder carrier board](teensy-encoder-board.html)
- [Perma-Proto solder map](perma-proto-solder-map.html)
- [Solder-map generator](gen_solder_map.py)

These are historical component designs, not verified as-built drawings for
both robots. In particular, a drawing describing a data-only USB connection
and external Teensy power does **not** describe the personal TX2's USB-only
Teensy supply. Check each robot's specs and wiring records before interpreting
these drawings as installation details.

Regenerate the solder map from the repository root:

```bash
python3 docs/shared/hardware/gen_solder_map.py
```

The output is written beside the generator. The old `docs/gen_solder_map.py`
path is retained as a compatibility link.
