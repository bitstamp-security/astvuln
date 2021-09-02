# -*- coding: utf-8 -*-

import datetime
import os

from . import visitors
from .common import Colors, Log
from .scanner import Scanner


# CLI interface
class Interface:
    PARAMS = {
        'arg_string': {'args': ['-a', '--args'], 'value': True, 'default': '', 'help': 'Arguments for method'},
        'help': {'args': ['-h', '--help'], 'value': False, 'help': 'Show help and exit'},
        'extensions': {'args': ['-e', '--extensions'], 'value': True, 'default': 'py', 'help': 'Extensions to process'},
        'grepable': {'args': ['-g', '--grepable'], 'value': False, 'help': 'Make results easier to grep'},
        'no_colors': {'args': ['-c', '--no-colors'], 'value': False, 'help': 'Don\'t print colors'},
        'no_source': {'args': ['-n', '--no-source'], 'value': False, 'help': 'Don\'t print source code'},
        'path': {'args': ['-p', '--path'], 'value': True, 'default': '.', 'help': 'Starting directory'},
        'skip': {'args': ['-s', '--skip'], 'value': True, 'default': 'tests', 'help': 'Paths to skip'},
    }

    def __init__(self, args):
        self.args = []
        self.name = args[0]
        self.method = None
        self.visitors = {}

        # Load visitors
        for name in dir(visitors):
            if name.startswith('Visitor'):
                visitor = getattr(visitors, name)
                if visitor.NAME:
                    self.visitors[visitor.NAME] = visitor

        # Allow multiple short arguments in same argument
        for arg in args[1:]:
            if len(arg) > 1 and arg[0] == '-' and arg[1] != '-':
                self.args += [f'-{x}' for x in arg[1:]]
            else:
                self.args.append(arg)

        self.configure()

        self.clr = Colors(self.no_colors or os.environ.get('NO_COLOR', False))
        self.log = Log(self.clr)

        if self.help or self.method is None:
            self.print_help()

        self.scanner_config = {
            'extensions': self.extensions.split(','),
            'skip': self.skip.split(','),
            'grepable': self.grepable,
            'print_source': not self.no_source,
            'visitor_configs': self.get_visitor_configs(),
        }

    def get_visitor_config(self, method, arg_string):
        if method in self.visitors:
            visitor = self.visitors[method]
        else:
            self.log.error(f'Unknown method "{method}"')

        visitor_args, visitor_kwargs = self.parse_visitor_args(arg_string)
        return {
            'visitor': visitor,
            'args': visitor_args,
            'kwargs': visitor_kwargs,
        }

    def get_visitor_configs(self):
        visitor_configs = []

        if self.method == 'file':
            # Configure visitors from file
            try:
                with open(self.arg_string, 'r') as f:
                    lines = [line.strip() for line in f.readlines()]
            except Exception as e:
                self.log.error(f'Error reading "{self.arg_string}": {e}')

            for line in lines:
                if not line or line.startswith('#'):
                    continue

                if ':' in line:
                    method, arg_string = line.strip().split(':', 1)
                else:
                    method, arg_string = line, ''

                visitor_configs.append(self.get_visitor_config(method.strip(), arg_string.strip()))
        else:
            # Configure visitors from CLI arguments
            visitor_configs.append(self.get_visitor_config(self.method, self.arg_string))

        return visitor_configs

    def configure(self):
        param = None

        for key, value in self.PARAMS.items():
            setattr(self, key, value.get('default', False))

        for arg in self.args:
            if param is not None:
                setattr(self, param, arg)
                param = None
                continue

            found = False

            for key, value in self.PARAMS.items():
                if arg in value['args']:
                    if value['value']:
                        param = key  # Parameter takes value
                        found = True
                    else:
                        setattr(self, key, True)  # Parameter is a flag
                        found = True

            if not found:
                if self.method is None:
                    self.method = arg
                else:
                    self.help = True

    def f(self, string, length):
        if len(string) > length:
            return string[:length - 3] + '...'
        else:
            return string + ' ' * (length - len(string))

    def parse_visitor_args(self, arg_string):
        args, kwargs = [], {}

        for arg in arg_string.split(','):
            arg = arg.strip()
            if not arg:
                continue

            parts = arg.split('=', 1)

            if len(parts) == 1:
                args.append(parts[0])
            else:
                kwargs[parts[0]] = parts[1]

        return args, kwargs

    def print_help(self):
        methods, params, usage = ([], []), [], []

        for method in sorted(self.visitors.keys()):
            visitor = self.visitors[method]
            args = ' ({})'.format(', '.join(visitor.ARGS)) if visitor.ARGS else ''
            group = 0 if visitor.COMMON else 1
            methods[group].append(f'    {method:25} {visitor.HELP}{args}')

        for x in self.PARAMS.values():
            param = ' <value>' if x['value'] else ''
            usage.append(f'[{x["args"][0]}{param}]')
            params.append('    {:25} {}'.format(f'{x["args"][0]}|{x["args"][1]}{param}', x['help']))

        print('\n'.join([
            'Astvuln: Search Python code for AST patterns.',
            'Usage: <method> {}'.format(''.join(usage)),
            '\nOptions:\n{}'.format('\n'.join(params)),
            '\nCommon methods:\n{}'.format('\n'.join(methods[0])),
            '\nCustom methods:\n{}'.format('\n'.join(methods[1])),
            '\nReading methods from file:',
            '   Run method "file" and pass filename in method arguments to run multiple methods in a single run.',
            '   Each method needs to be specified in a single line and colon-seperated from arguments.',
            '   E. g. "./astvuln foo -a bar,baz" would be translated to:',
            '       foo:bar,baz',
            '\nExamples:',
            '    ./astvuln -h                   # Print help',
            '    ./astvuln print -c             # Run method `print` without color output',
            '    ./astvuln dump -p dir          # Run method `dump` on directory `dir`',
            '    ./astvuln call -a bytes        # Run method `called` with argument `bytes`',
            '    ./astvuln foo -a a=1,b=2       # Run method `foo` with arguments a = 1 and b = 2',
            '    ./astvuln file -a methods.txt  # Run multiple methods specified in a file',
        ]))

        exit()

    def print_greeting(self):
        conf = self.scanner_config
        flags = []

        if self.log.clr.no_colors:
            flags.append('no colors')
        if conf['grepable']:
            flags.append('grepable')

        greeting = [
            '+---------------------------------[ astvuln ]---------------------------------+',
            '| Date:       {} |'.format(self.f(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 63)),
            '| Path:       {} |'.format(self.f(self.path, 63)),
            '| Extensions: {} |'.format(self.f(', '.join(conf['extensions']), 63)),
            '| Skip:       {} |'.format(self.f(', '.join(conf['skip']), 63)),
            '| Flags:      {} |'.format(self.f(', '.join(flags), 63)),
            '+-----------------------------------------------------------------------------+',
        ]

        for visitor_config in conf['visitor_configs']:
            greeting += [
                '| Method:     {} |'.format(self.f(visitor_config['visitor'].NAME, 63)),
                '|             {} |'.format(self.f(visitor_config['visitor'].HELP, 63)),
                '| Params:     {} |'.format(self.f(', '.join(visitor_config['visitor'].ARGS), 63)),
                '| Args:       {} |'.format(self.f(', '.join(visitor_config['args']), 63)),
                '| Kwargs:     {} |'.format(
                    self.f(', '.join([f'{k}={v}' for k, v in visitor_config['kwargs'].items()]), 63)),
                '+-----------------------------------------------------------------------------+',
            ]

        self.log.plain('\n'.join(greeting), self.log.clr.INFO)

    def run(self):
        self.print_greeting()

        start = datetime.datetime.now()
        scanner = Scanner(self.log, **self.scanner_config)

        try:
            scanner.scan(self.path)
        except KeyboardInterrupt:
            self.log.info('Interrupted, exiting')

        duration = datetime.datetime.now() - start
        self.log.info(f'Finished run in {duration}')
