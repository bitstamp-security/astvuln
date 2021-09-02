# -*- coding: utf-8 -*-

# Copyright (c) 2021 Bitstamp Ltd
# This code is licensed under the MIT license. See LICENSE.md for license terms.

import ast

from .base import Visitor


# Base class for visitors used to gather information before "main" visitor runs
class Previsitor(Visitor):
    def init_visitor(self):
        if 'names' not in self.data:
            self.data['names'] = set()

    def visit(self, node):
        # Visit node
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        visitor(node)

        # Recursively visit children
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)


class PrevisitorNames(Previsitor):
    def visit_Name(self, node):
        self.data['names'].add(node.id)

    def visit_Attribute(self, node):
        self.data['names'].add(node.attr)
