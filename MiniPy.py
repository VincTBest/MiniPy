import re

# Token class definition
class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

# Lexer class definition
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Invalid character')

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def variable(self):
        result = ''
        while self.current_char is not None and self.current_char.isalnum():
            result += self.current_char
            self.advance()
        return Token('VARIABLE', result)

    def number(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return Token('NUMBER', int(result))

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            if self.current_char.isalpha():
                return self.variable()
            if self.current_char.isdigit():
                return self.number()
            if self.current_char == '+':
                self.advance()
                return Token('PLUS', '+')
            if self.current_char == '-':
                self.advance()
                return Token('MINUS', '-')
            if self.current_char == '*':
                self.advance()
                return Token('MUL', '*')
            if self.current_char == '/':
                self.advance()
                return Token('DIV', '/')
            if self.current_char == '=':
                self.advance()
                return Token('EQ', '=')
            if self.current_char == ';':
                self.advance()
                return Token('SEMICOLON', ';')
            if self.current_char == '(':
                self.advance()
                return Token('LPAREN', '(')
            if self.current_char == ')':
                self.advance()
                return Token('RPAREN', ')')
            if self.current_char == 'p' and self.text[self.pos:self.pos+5] == 'print':
                self.pos += 5
                self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                return Token('PRINT', 'print')
            self.error()
        return Token('EOF', None)

# AST Node classes
class AST:
    pass

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"BinOp({self.left}, {self.op}, {self.right})"

class Num(AST):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Num({self.value})"

class Var(AST):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Var({self.name})"

class Assign(AST):
    def __init__(self, var, value):
        self.var = var
        self.value = value

    def __repr__(self):
        return f"Assign({self.var}, {self.value})"

class Print(AST):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"Print({self.expr})"

# Parser class definition
class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self):
        token = self.current_token
        if token.type == 'NUMBER':
            self.eat('NUMBER')
            return Num(token.value)
        elif token.type == 'VARIABLE':
            self.eat('VARIABLE')
            return Var(token.value)
        elif token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            return node
        self.error()

    def term(self):
        node = self.factor()
        while self.current_token.type in ('MUL', 'DIV'):
            token = self.current_token
            if token.type == 'MUL':
                self.eat('MUL')
            elif token.type == 'DIV':
                self.eat('DIV')
            node = BinOp(node, token, self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.current_token.type in ('PLUS', 'MINUS'):
            token = self.current_token
            if token.type == 'PLUS':
                self.eat('PLUS')
            elif token.type == 'MINUS':
                self.eat('MINUS')
            node = BinOp(node, token, self.term())
        return node

    def statement(self):
        if self.current_token.type == 'VARIABLE':
            var = self.current_token
            self.eat('VARIABLE')
            self.eat('EQ')
            value = self.expr()
            self.eat('SEMICOLON')
            return Assign(var.value, value)
        elif self.current_token.type == 'PRINT':
            self.eat('PRINT')
            expr = self.expr()
            self.eat('SEMICOLON')
            return Print(expr)
        self.error()

    def parse(self):
        statements = []
        while self.current_token.type != 'EOF':
            statements.append(self.statement())
        return statements

# Interpreter class definition
class Interpreter:
    def __init__(self, parser):
        self.parser = parser
        self.variables = {}

    def visit_Num(self, node):
        return node.value

    def visit_Var(self, node):
        return self.variables.get(node.name, 0)

    def visit_BinOp(self, node):
        if node.op.type == 'PLUS':
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == 'MINUS':
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == 'MUL':
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == 'DIV':
            return self.visit(node.left) / self.visit(node.right)
        self.error()

    def visit_Assign(self, node):
        self.variables[node.var] = self.visit(node.value)

    def visit_Print(self, node):
        result = self.visit(node.expr)
        print(result)

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.error)
        return method(node)

    def interpret(self):
        tree = self.parser.parse()
        for statement in tree:
            self.visit(statement)

# Help function
def print_help():
    help_text = """
MiniPy Help:

Commands:
- let <variable> = <expression>;    : Assigns the result of <expression> to <variable>.
- print(<expression>);              : Prints the result of <expression> to the console.
- help                            : Displays this help message.
- exit                            : Exits the MiniPy interpreter.

Expressions:
- Basic arithmetic: +, -, *, /
- Parentheses for grouping: ( and )
- Variables are alphanumeric names.

Examples:
- let x = 5 + 3;
- print(x * 2);
- let y = 10 / (2 + 3);
- print(y);
    """
    print(help_text)

# Main function to run the interpreter
def main():
    print("Welcome to MiniPy! Type 'help' for a list of commands.")
    while True:
        try:
            text = input('MiniPy> ')
            if text.strip() == 'exit':
                break
            elif text.strip() == 'help':
                print_help()
            else:
                lexer = Lexer(text)
                parser = Parser(lexer)
                interpreter = Interpreter(parser)
                interpreter.interpret()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
