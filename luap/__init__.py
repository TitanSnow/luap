from os.path import expanduser
from functools import partial
import re
import platform
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
from prompt_toolkit.buffer import indent, unindent


class LuaRepl:
    PROMPT1 = '>>> '
    PROMPT2 = '... '
    PROMPT_STYLE = style_from_pygments(DefaultStyle, {
        Token.Succ: '#ansigreen',
        Token.Fail: '#ansired',
        Token.Dot: '#ansiblue',
        Token.Alter: 'bg:#ffff88 #444444'
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
        def get_prompt(firstline, cli, width=4):
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
            buff = event.current_buffer
            doc = buff.document
            code = doc.text
            if not doc.is_cursor_at_the_end or self.incomplete(code):
                buff.newline(copy_margin=not event.cli.in_paste_mode)
                if not event.cli.in_paste_mode:
                    if self.get_lua_indent('\n'.join(doc.lines[:doc.cursor_position_row + 1])):
                        self.indent_curline(buff)
            else:
                buff.accept_action.validate_and_handle(event.cli, buff)

        @manager.registry.add_binding(Keys.Tab)
        def _(event):
            event.current_buffer.insert_text(' ' * 4)

        @manager.registry.add_binding(Keys.Backspace)
        def _(event):
            buff = event.current_buffer
            doc = buff.document
            col = doc.cursor_position_col
            if col >= 4 and col % 4 == 0 and doc.current_line[:col].isspace():
                self.indent_curline(buff, -1)
            else:
                buff.delete_before_cursor()

        def get_rprompt(cli):
            return [
                (Token.Alter, ' '),
                (Token.Alter, self._lua._G._VERSION),
                (Token.Alter, ', '),
                (Token.Alter, platform.python_implementation() + ' ' + '.'.join(platform.python_version_tuple()[:2])),
                (Token.Alter, ' '),
            ]

        def get_toolbar(cli):
            if cli.current_buffer.document.is_cursor_at_the_end:
                return []
            else:
                return [
                    (Token.Alter, ' [Meta+Enter] Execute ')
                ]

        return prompt(
            get_prompt_tokens=partial(get_prompt, True),
            lexer=PygmentsLexer(LuaLexer),
            style=self.PROMPT_STYLE,
            history=self._history,
            key_bindings_registry=manager.registry,
            multiline=True,
            get_continuation_tokens=partial(get_prompt, False),
            get_rprompt_tokens=get_rprompt,
            get_bottom_toolbar_tokens=get_toolbar,
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

    def get_lua_indent(self, text):
        prevline = text.rstrip().split('\n')[-1]
        tripped = prevline.lstrip()
        if (
            re.search(r'^(?:if|for|while|repeat|else|elseif|do|then)(?:\W|$)', tripped) or
            re.search(r'\{\s*$', tripped) or
            re.search(r'(?:\W|^)function\W\s*(?:\w|\.|:)*\s*\(', tripped)
        ) and not re.search(r'\W(?:end|until)\W*$', tripped):
            return True
        else:
            return False

    @staticmethod
    def indent_curline(buffer, count=1):
        lineno = buffer.document.cursor_position_row
        if count > 0:
            indent(buffer, lineno, lineno + 1, count)
        elif count < 0:
            unindent(buffer, lineno, lineno + 1, -count)


def embed(runtime=None):
    LuaRepl(runtime).run()
