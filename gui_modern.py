# coding: utf-8
"""Compatibility wrapper for previous entrypoint.

This file used to contain the full GUI. It now forwards to `gui.run()` so
existing invocation patterns continue to work (e.g. `python gui_modern.py`).
"""

import os
import sys

# Preserve prior behavior of setting CUDA devices when run as script
if __name__ == "__main__":
    gpu_use = "0"
    print("GPU use: {}".format(gpu_use))
    os.environ["CUDA_VISIBLE_DEVICES"] = "{}".format(gpu_use)

from inference import __VERSION__

# Import the new GUI package entrypoint
try:
    from gui import run
except Exception:
    run = None


def main(argv=None):
    if run is None:
        print("GUI package not available. Did the refactor complete?")
        return 1

    return run(argv)


if __name__ == "__main__":
    print("Version: {}".format(__VERSION__))
    sys.exit(main())
