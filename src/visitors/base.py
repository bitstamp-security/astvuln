# -*- coding: utf-8 -*-

# Copyright (c) 2021 Bitstamp Ltd
# This code is licensed under the MIT license. See LICENSE.md for license terms.

import ast


# AST visitor base class
class Visitor(ast.NodeVisitor):
    ARGS = []
    COMMON = True
    DEFAULTS = {}
    HELP = ''
    NAME = ''
    TYPES_CF = [
        ast.ExceptHandler,
        ast.For,
        ast.If,
        ast.Try,
        ast.While,
        ast.With,
    ]
    TYPES_FN = [
        ast.ClassDef,
        ast.FunctionDef
    ]
    PREVISITORS = set()

    def __init__(self, scanner, *args, **kwargs):
        self.state = {
            'global': {},
            'fn': [],
            'cf': [],
            'line_start': 0,
            'line_end': 0,
        }

        self.data = scanner.data
        self.log = scanner.log

        # Set arguments
        for arg in self.ARGS:
            setattr(self, arg, self.DEFAULTS.get(arg, None))

        for ii, arg in enumerate(args):
            if ii < len(self.ARGS):
                setattr(self, self.ARGS[ii], self.parse_value(arg))

        for key, value in kwargs.items():
            if key in self.ARGS:
                setattr(self, key, self.parse_value(value))

        self.init_visitor()

    def init_visitor(self):
        pass

    def del_tracked(self, *args):
        for key in args:
            if key in self.state['global']:
                del self.state['global'][key]

            for scope in ['fn', 'cf']:
                for item in self.state[scope]:
                    if key in item[1]:
                        del item[1][key]

    def generic_visit(self, node):
        pass

    def get_tracked(self, key):
        for scope in ['cf', 'fn']:
            for item in self.state[scope]:
                if key in item[1]:
                    return item[1][key]

        return self.state['global'].get(key, None)

    def get_tracked_all(self):
        tracked = {
            'global': self.state['global'],
            'fn': self.state['fn'][-1][1] if self.state['fn'] else {},
            'cf': self.state['cf'][-1][1] if self.state['cf'] else {},
        }

        for scope in ['fn', 'cf']:
            for item in self.state[scope]:
                for key, value in item[1].items():
                    tracked[scope][key] = value

        return tracked

    @staticmethod
    def has_class(node, search):
        for attr, cls in search:
            node = getattr(node, attr, None) if attr else node
            if not isinstance(node, cls):
                return False

        return True

    @staticmethod
    def parse_value(value):
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        elif value.isnumeric():
            return int(value)

        return value

    @staticmethod
    def print_method(state, msg, print_source):
        # This method is meant to be replaced by scanner print which has the needed context
        pass

    def print_result(self, msg='', print_source=True):
        self.print_method(self.state, msg, print_source)

    @classmethod
    def recursive_attribute_name(cls, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Attribute):
            return '{}.{}'.format(cls.recursive_attribute_name(node.value), node.attr)

    def set_tracked(self, key, value):
        self.state['global'][key] = value

        if self.state['fn']:
            self.state['fn'][-1][1][key] = value
        if self.state['cf']:
            self.state['cf'][-1][1][key] = value

    def visit(self, node):
        # Update state
        if type(node) in self.TYPES_FN:
            self.state['fn'].append((node.name, {}))
        elif type(node) in self.TYPES_CF:
            self.state['cf'].append((node.__class__.__name__, {}))

        self.state['line_start'] = getattr(node, 'lineno', self.state['line_start'])
        self.state['line_end'] = getattr(node, 'end_lineno', self.state['line_end'])

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

        # Update state again
        if type(node) in self.TYPES_FN:
            self.state['fn'].pop()
        elif type(node) in self.TYPES_CF:
            self.state['cf'].pop()
