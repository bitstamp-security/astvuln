# Astvuln

Astvuln is a simple AST scanner which recursively scans a directory, parses each
file as AST and runs specified method. Some search methods are provided with the
tool and can be found under `./src/visitors/` in `common.py` and `custom.py` but
most methods are not included in the repository. To add a new search method edit
one of existing files and add a new class. The simplest way is to extend it from
`AstVisitor` class. Implement query logic using `generic_visit`/`visit_{class}`.

This tool was developed for research purposes with the idea to explore potential
vulnerable patterns when a new type of bug is discovered in our code. We can use
such patterns to potentially find new similar bugs. AST code patterns which have
sufficiently low false positive rate should then be included in SAST automation.

## Usage

```
Astvuln: Search Python code for AST patterns.
Usage: <method> [-a <value>][-h][-e <value>][-g][-c][-n][-p <value>][-s <value>]

Options:
    -a|--args <value>         Arguments for method
    -h|--help                 Show help and exit
    -e|--extensions <value>   Extensions to process
    -g|--grepable             Make results easier to grep
    -c|--no-colors            Don't print colors
    -n|--no-source            Don't print source code
    -p|--path <value>         Starting directory
    -s|--skip <value>         Paths to skip

Common methods:
    assign                    Find assignements with matching names (name)
    call                      Find all function calls with matching name (name, path)
    class                     Find all classes with matching name (name)
    constant                  Find all constants with matching value (name)
    dict                      Find all dicts with matching item constant value (name)
    dump                      Dump AST
    function                  Find all functions and methods with matching name (name)
    list                      Find all lists with matching constant value (name)
    name                      Find all matching names (name)
    print                     Print node names
    test                      Do nothing

Custom methods:
    forelse                   Search for `for` loops with `else` clause which seems to always trigger
    replace_with_substring    Search for replace of a string with a substring or an empty string
    unused_classes            Find classes which are never directly referenced by name (ignore)

Reading methods from file:
   Run method "file" and pass filename in method arguments to run multiple methods in a single run.
   Each method needs to be specified in a single line and colon-seperated from arguments.
   E. g. "./astvuln foo -a bar,baz" would be translated to:
       foo:bar,baz

Examples:
    ./astvuln -h                   # Print help
    ./astvuln print -c             # Run method `print` without color output
    ./astvuln dump -p dir          # Run method `dump` on directory `dir`
    ./astvuln call -a bytes        # Run method `call` with argument `bytes`
    ./astvuln foo -a a=1,b=2       # Run method `foo` with arguments a = 1 and b = 2
    ./astvuln file -a methods.txt  # Run multiple methods specified in a file
```

## License

Astvuln is released under the MIT License.
