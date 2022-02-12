#!/usr/bin/env python3
# -*- coding: utf8 -*-
# tab-width:4
"""
Error Pretty Print: epprint()
prepend stack metadata to eprint()
"""

import inspect
import os
import sys
import time

from eprint import eprint


def epprint(*args, **kwargs) -> None:
    """prepend stack metadata to eprint()"""
    # pylint: disable=W0212  # access to protected member
    caller = sys._getframe(1).f_code.co_name
    # pylint: enable=W0212
    stack = inspect.stack()
    frm = stack[1]
    depth = len(stack)
    mod = str(inspect.getmodule(frm[0]))
    try:
        source_file = mod.split()[-1].split(">")[0].split("'")[1].split("/")[-1]
    except IndexError:
        source_file = "(none)"
    head = " ".join(
        [
            str(depth).zfill(4),
            f"{time.time():.5f}",
            str(os.getpid()),
            source_file,
            caller + "()",
        ]
    )
    eprint(f"{head}", *args, **kwargs)
