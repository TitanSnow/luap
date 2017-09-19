from os.path import expanduser
from functools import partial
from ffilupa import *
from ffilupa.py_from_lua import *
from pygments.lexers import LuaLexer
from pygments.styles.default import DefaultStyle
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments
from prompt_toolkit.token import Token
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys


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
        def get_token(firstline, cli, width=4):
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

        manager = KeyBindingManager.for_prompt()
        @manager.registry.add_binding(Keys.Enter)
        def _(event):
            code = event.current_buffer.text
            if self.incomplete(code):
                event.current_buffer.newline(copy_margin=not event.cli.in_paste_mode)
            else:
                buff = event.current_buffer
                buff.accept_action.validate_and_handle(event.cli, buff)

        return prompt(
            get_prompt_tokens=partial(get_token, True),
            lexer=PygmentsLexer(LuaLexer),
            style=self.PROMPT_STYLE,
            history=self._history,
            key_bindings_registry=manager.registry,
            multiline=True,
            get_continuation_tokens=partial(get_token, False)
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
