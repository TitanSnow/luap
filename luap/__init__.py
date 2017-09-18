from ffilupa import *
from ffilupa.py_from_lua import *
from pygments.lexers import LuaLexer
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.layout.lexers import PygmentsLexer


class LuaRepl:
    PROMPT1 = '>>> '
    PROMPT2 = '... '

    def __init__(self, runtime=None):
        if runtime is None:
            runtime = LuaRuntime()
        self._lua = runtime

    def run(self):
        try:
            while True:
                self.run_single()
        except EOFError:
            pass

    def run_single(self):
        code = self.read_code()
        try:
            func = self._lua.compile('return ' + code, b'=stdin')
        except LuaErrSyntax:
            try:
                func = self._lua.compile(code, b'=stdin')
            except LuaErrSyntax as e:
                print(e.err_msg)
                return False
        try:
            results = func(keep=True)
        except LuaErr as e:
            print(e.err_msg)
            return False
        if results is not None:
            self.print_results(*(results if isinstance(results, tuple) else (results,)))
        return True

    def read_code(self):
        lns = [self.read_line(True)]
        while self.incomplete('\n'.join(lns)):
            lns.append(self.read_line(False))
        return '\n'.join(lns)

    def read_line(self, firstline):
        return prompt(
            self.PROMPT1 if firstline else self.PROMPT2,
            lexer=PygmentsLexer(LuaLexer)
        )

    def incomplete(self, code):
        try:
            self._lua.compile(code)
        except LuaErrSyntax as e:
            if e.err_msg.endswith('<eof>'):
                try:
                    self._lua.compile('return ' + code)
                except LuaErrSyntax:
                    return True
        return False

    def print_results(self, *results):
        self._lua._G.print(*results)


def embed(runtime=None):
    LuaRepl(runtime).run()
