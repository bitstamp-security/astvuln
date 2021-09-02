# -*- coding: utf-8 -*-

import ast
import os


# Recursive AST parser
class Scanner:
    def __init__(self, log, visitor_configs, extensions=['py'], skip=[], grepable=False, print_source=True):
        self.grepable = grepable
        self.print_source = print_source
        self.data = {}
        self.log = log
        self.visitor_configs = visitor_configs
        self.extensions = extensions
        self.skip = skip
        self.visitors = []

        previsitors = set()

        for visitor_config in visitor_configs:
            visitor = visitor_config['visitor'](self, *visitor_config['args'], **visitor_config['kwargs'])
            self.visitors.append(visitor)
            previsitors = set.union(previsitors, visitor.PREVISITORS)

        self.previsitors = [previsitor(self) for previsitor in previsitors]

    def _scan_with_worker(self, path, visitors):
        worker = ScannerWorker(self.log, self.grepable, self.print_source, visitors)

        # Overwrite print method to get additional information added by scanner
        for visitor in worker.visitors:
            visitor.print_method = worker.print_result

        if os.path.exists(path):
            if os.path.isfile(path):
                worker.scan(path)
            else:
                for root, dirs, files in os.walk(path):
                    dirs[:] = [x for x in dirs if x not in self.skip]
                    for filename in files:
                        if filename.rsplit('.', 1)[-1] in self.extensions:
                            worker.scan(os.path.join(root, filename))
        else:
            self.log.error(f'Path does not exist: {path}')

    def scan(self, path):
        if self.previsitors:
            self._scan_with_worker(path, self.previsitors)

        self._scan_with_worker(path, self.visitors)


class ScannerWorker():
    def __init__(self, log, grepable, print_source, visitors):
        self.log = log
        self.grepable = grepable
        self.print_source = print_source
        self.state = {}
        self.visitors = visitors

    def print_result(self, state, msg, print_source=True, print_state=True):
        clr = self.log.clr
        parts = [f'{clr.FILE}{self.state["filename"]}{clr.NONE}:' if self.grepable else '    ']
        parts.append(f'{clr.LINE}{state["line_start"]}{clr.NONE}')

        if print_state:
            fn = ' ' + '.'.join([f'{clr.FUNC}{x[0]}{clr.NONE}' for x in state['fn']]) if state['fn'] else ''
            cf = ' ' + '->'.join([f'{clr.FLOW}{x[0]}{clr.NONE}' for x in state['cf']]) if state['cf'] else ''
            parts.append(f'{fn}{cf}')

        parts.append(f': {clr.MSGS}{msg}{clr.NONE}')

        if not self.grepable and not self.state['printed']:
            print(clr.FILE + self.state['filename'] + clr.NONE)
            self.state['printed'] = True

        print(''.join(parts))

        if print_source and self.print_source:
            if self.state['lines'] is None:
                self.state['lines'] = self.state['src'].split(b'\n')

            print('\n'.join([
                f'{clr.LINE}{n:4}{clr.NONE}:{self.state["lines"][n-1].decode()}'
                for n in range(state['line_start'], state['line_end'] + 1)
            ]))

    def scan(self, path):
        with open(path, 'rb') as f:
            src = f.read()

        self.state = {
            'ast': ast.parse(src),
            'filename': path,
            'lines': None,  # Set when needed
            'printed': False,
            'src': src,
        }

        for visitor in self.visitors:
            visitor.visit(self.state['ast'])
