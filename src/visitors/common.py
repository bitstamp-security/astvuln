# -*- coding: utf-8 -*-

import ast
import re

from .base import Visitor


# Import astor for pretty dump or fallback to ast (less pretty) dump
try:
    import astor
    dump = astor.dump_tree
except Exception:
    dump = ast.dump


# Visitors for individual AST types
class VisitorType(Visitor):
    ARGS = ['name']
    TYPE = None
    PATHS = {}

    def init_visitor(self):
        self.regex = []

        for arg in self.ARGS:
            value = getattr(self, arg, None)
            self.regex.append((arg, re.compile(f'^{value}$') if value else None))

        self.regex = self.regex[::-1]

    def get_name(self, node, arg):
        current_node = node
        for path in self.PATHS[arg]:
            current_node = getattr(current_node, path, None)

        return current_node

    def is_match(self, node):
        if not isinstance(node, self.TYPE):
            return '', False

        for arg, regex in self.regex:
            name = self.get_name(node, arg)

            if type(name) is None:
                return name, False
            if regex:
                if type(name) is str:
                    if not regex.match(name):
                        return name, False
                elif type(name) is list:
                    if not any([regex.match(x) for x in name]):
                        return name, False
                else:
                    return name, False

        return name, True

    def generic_visit(self, node):
        name, match = self.is_match(node)
        if match:
            self.print_result(name)


class VisitorTypeNested(VisitorType):
    def generic_visit(self, node):
        return

    def visit_elements(self, elements):
        for element in elements:
            name, match = self.is_match(element)
            if match:
                self.print_result(name)
                return True

        return False


class VisitorAssign(VisitorTypeNested):
    NAME = 'assign'
    HELP = 'Find assignements with matching names'
    TYPE = ast.Name
    PATHS = {'name': ['id']}

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Tuple):
                if self.visit_elements(target.elts):
                    return
            name, match = self.is_match(target)
            if match:
                self.print_result(name)
                return


class VisitorCall(VisitorType):
    ARGS = ['name', 'path']
    NAME = 'call'
    HELP = 'Find all function calls with matching name'
    TYPE = ast.Call

    def get_name(self, node, name):
        node = node.func
        elements = []

        while True:
            if type(node) is ast.Name:
                elements.append(node.id)
                break
            elif type(node) is ast.Attribute:
                elements.append(node.attr)
                node = node.value
            else:
                break

        if not elements:
            return

        if name == 'name':
            return elements[0]
        elif name == 'path':
            return elements[1:]


class VisitorClass(VisitorType):
    NAME = 'class'
    HELP = 'Find all classes with matching name'
    TYPE = ast.ClassDef
    PATHS = {'name': ['name']}


class VisitorConstant(VisitorType):
    NAME = 'constant'
    HELP = 'Find all constants with matching value'
    TYPE = ast.Constant
    PATHS = {'name': ['value']}


class VisitorDict(VisitorTypeNested):
    NAME = 'dict'
    HELP = 'Find all dicts with matching item constant value'
    TYPE = ast.Constant
    PATHS = {'name': ['value']}

    def visit_Dict(self, node):
        self.visit_elements(node.keys) or self.visit_elements(node.values)


class VisitorFunction(VisitorType):
    NAME = 'function'
    HELP = 'Find all functions and methods with matching name'
    TYPE = ast.FunctionDef
    PATHS = {'name': ['name']}


class VisitorName(VisitorType):
    NAME = 'name'
    HELP = 'Find all matching names'
    TYPE = ast.Name
    PATHS = {'name': ['id']}


class VisitorList(VisitorTypeNested):
    NAME = 'list'
    HELP = 'Find all lists with matching constant value'
    TYPE = ast.Constant
    PATHS = {'name': ['value']}

    def visit_List(self, node):
        self.visit_elements(node.elts)


# Debug visitors
class VisitorDump(Visitor):
    NAME = 'dump'
    HELP = 'Dump AST'

    def generic_visit(self, node):
        print(dump(node))


class VisitorPrint(Visitor):
    NAME = 'print'
    HELP = 'Print node names'

    def generic_visit(self, node):
        self.print_result(f'{node.__class__.__name__}', print_source=False)


class VisitorTest(Visitor):
    NAME = 'test'
    HELP = 'Do nothing'

    def generic_visit(self, node):
        return
