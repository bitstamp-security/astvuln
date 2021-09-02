# -*- coding: utf-8 -*-

# Copyright (c) 2021 Bitstamp Ltd
# This code is licensed under the MIT license. See LICENSE.md for license terms.

import datetime
import sys


# Colors
class Colors:
    COLORS = {
        'ERRS': '\033[31m',  # Red
        'FILE': '\033[35m',  # Magenta
        'FLOW': '\033[33m',  # Yellow
        'FUNC': '\033[91m',  # Light red
        'INFO': '\033[93m',  # Light yellow
        'LINE': '\033[32m',  # Green
        'MSGS': '\033[96m',  # Light cyan
        'NONE': '\033[39m',  # Default
        'H_SHOW': '\033[41m',  # Red
        'H_NONE': '\033[49m',  # Default
    }

    def __init__(self, no_colors=False):
        self.no_colors = no_colors

    def __getattr__(self, name):
        if name in self.COLORS:
            return '' if self.no_colors else self.COLORS[name]
        else:
            object.__getattr__(self, name)


# Helper functions for logging
class Log:
    def __init__(self, clr):
        self.clr = clr

    def _print(self, prefix, color, msg):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{color}[{prefix}][{now}] {msg}{self.clr.NONE}', file=sys.stderr)

    def error(self, msg):
        print(f'{self.clr.ERRS}{msg}{self.clr.NONE}', file=sys.stderr)
        sys.exit(-1)

    def info(self, msg):
        self._print('?', self.clr.INFO, msg)

    def plain(self, msg, clr=None):
        print(f'{clr}{msg}{self.clr.NONE}' if clr else msg, file=sys.stderr)
