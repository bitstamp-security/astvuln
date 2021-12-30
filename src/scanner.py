# -*- coding: utf-8 -*-

# Copyright (c) 2021 Bitstamp Ltd
# This code is licensed under the MIT license. See LICENSE.md for license terms.

import ast
import os


# Recursive AST parser
class Scanner:
    def __init__(self, log, visitor_configs, extensions=["py"], skip=[], grepable=False, print_source=True):
        self.data = {}
        self.extensions = extensions
        self.grepable = grepable
        self.log = log
        self.n_files = 0
        self.n_findings = 0
        self.print_source = print_source
        self.skip = skip
        self.visitors = []
        self.visitor_configs = visitor_configs

        previsitors = set()

        for visitor_config in visitor_configs:
            visitor = visitor_config["visitor"](self, *visitor_config["args"], **visitor_config["kwargs"])
            self.visitors.append(visitor)
            previsitors = set.union(previsitors, visitor.PREVISITORS)

        self.previsitors = [previsitor(self) for previsitor in previsitors]

    def print_result(self, state, msg, print_source=True, print_state=True):
        self.n_findings += 1
        clr = self.log.clr
        parts = [f'{clr.FILE}{self.state["filename"]}{clr.NONE}:' if self.grepable else "    "]
        parts.append(f'{clr.LINE}{state["line_start"]}{clr.NONE}')

        if print_state:
            fn = " " + ".".join([f"{clr.FUNC}{x[0]}{clr.NONE}" for x in state["fn"]]) if state["fn"] else ""
            cf = " " + "->".join([f"{clr.FLOW}{x[0]}{clr.NONE}" for x in state["cf"]]) if state["cf"] else ""
            parts.append(f"{fn}{cf}")

        parts.append(f": {clr.MSGS}{msg}{clr.NONE}")

        if not self.grepable and not self.state["printed"]:
            print(clr.FILE + self.state["filename"] + clr.NONE)
            self.state["printed"] = True

        print("".join(parts))

        if print_source and self.print_source:
            if self.state["lines"] is None:
                self.state["lines"] = self.state["src"].split(b"\n")

            print(
                "\n".join(
                    [
                        f'{clr.LINE}{n:4}{clr.NONE}:{self.state["lines"][n-1].decode()}'
                        for n in range(state["line_start"], state["line_end"] + 1)
                    ]
                )
            )

    def scan(self, path):
        if self.previsitors:
            self.scan_with_visitors(path, self.previsitors)

        self.scan_with_visitors(path, self.visitors)

    def scan_with_visitors(self, path, visitors):
        if os.path.exists(path):
            if os.path.isfile(path):
                self.scan_file(path, visitors)
            else:
                for root, dirs, files in os.walk(path):
                    dirs[:] = [x for x in dirs if x not in self.skip]
                    for filename in files:
                        if filename.rsplit(".", 1)[-1] in self.extensions:
                            self.scan_file(os.path.join(root, filename), visitors)
        else:
            self.log.error(f"Path does not exist: {path}")

    def scan_file(self, path, visitors):
        self.n_files += 1

        with open(path, "rb") as f:
            src = f.read()

        self.state = {
            "ast": None,  # Set when needed
            "filename": path,
            "lines": None,  # Set when needed
            "printed": False,
            "src": src,
        }

        for visitor in visitors:
            if not visitor.skip(src):
                if self.state["ast"] is None:
                    self.state["ast"] = ast.parse(src)

                visitor.visit(self.state["ast"])
