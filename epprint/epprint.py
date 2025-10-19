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
    """Prepend stack metadata to eprint()"""
    caller = sys._getframe(1).f_code.co_name  # pylint: disable=protected-access
    stack = inspect.stack()
    frm = stack[1]
    depth = len(stack)

    # More robust file extraction
    source_file = os.path.basename(frm.filename) if frm.filename else "(none)"

    head = " ".join(
        [
            str(depth).zfill(4),
            f"{time.time():.5f}",
            str(os.getpid()),
            source_file,
            f"{caller}()",
        ]
    )
    eprint(head, *args, **kwargs)
