from os.path import expanduser
from ffilupa import *
from ffilupa.py_from_lua import *
from pygments.lexers import LuaLexer
from pygments.styles.default import DefaultStyle
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments
from prompt_toolkit.token import Token
from prompt_toolkit.history import FileHistory


class LuaRepl:
    PROMPT1 = '>>> '
    PROMPT2 = '... '
    PROMPT_STYLE = style_from_pygments(DefaultStyle, {
        Token.Succ: '#ansigreen',
        Token.Fail: '#ansired',
        Token.Dot: '#ansiblue',
    })

    def __init__(self, runtime=None):
        if runtime is None:
            runtime = LuaRuntime()
        self._lua = runtime
        self._laststate = True
        self._history = FileHistory(expanduser('~/.luap_history'))

    def run(self):
        try:
            while True:
                try:
                    self._laststate = self.run_single()
                except KeyboardInterrupt:
                    self._laststate = False
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
        def get_token(cli):
            if firstline:
                return [
                    (
                        (Token.Succ if self._laststate else Token.Fail),
                        self.PROMPT1,
                    )
                ]
            else:
                return [
                    (
                        Token.Dot,
                        self.PROMPT2,
                    )
                ]
        return prompt(
            get_prompt_tokens=get_token,
            lexer=PygmentsLexer(LuaLexer),
            style=self.PROMPT_STYLE,
            history=self._history,
            enable_system_bindings=True
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
