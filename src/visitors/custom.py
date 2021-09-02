# -*- coding: utf-8 -*-

# Source file for custom AST search patterns. Patterns we use internally are not
# included here to avoid revealing internal code structure and coding practices.
# A few visitors are provided as an example.

import ast
import re

from .base import Visitor
from . import previsitors


class VisitorCustom(Visitor):
    # Base visitor for custom methods
    COMMON = False


class VisitorForElse(VisitorCustom):
    NAME = 'forelse'
    HELP = 'Search for `for` loops with `else` clause which seems to always trigger'

    def generic_visit(self, node):
        if type(node) in [ast.For, ast.While] and node.orelse:
            for x in ast.walk(node):
                if type(x) in [ast.Break, ast.Return]:
                    return
            self.print_result(f'{node.__class__.__name__} with else')


class VisitorReplaceWithSubstring(VisitorCustom):
    NAME = 'replace_with_substring'
    HELP = 'Search for replace of a string with a substring or an empty string'

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ['replace', 'sub']:
                if len(node.args) > 1 \
                        and isinstance(node.args[0], ast.Constant) \
                        and isinstance(node.args[1], ast.Constant) \
                        and len(node.args[0].value) > 0 \
                        and node.args[0].value.find(node.args[1].value) != -1:
                    self.print_result('Replace with substring')


class VisitorUnusuedClasses(VisitorCustom):
    NAME = 'unused_classes'
    HELP = 'Find classes which are never directly referenced by name'
    PREVISITORS = {previsitors.PrevisitorNames}
    ARGS = ['ignore']

    def init_visitor(self):
        self.ignore = re.compile(f'^({self.ignore})$') if self.ignore else None

    def visit_ClassDef(self, node):
        if 'names' not in self.data:
            self.log.error('Missing data in scanner, did previsitor run?')

        if node.name not in self.data['names']:
            if not self.ignore or not self.ignore.match(node.name):
                self.print_result('Potentially unused class', print_source=False)
