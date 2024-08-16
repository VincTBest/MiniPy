# --- Token Definition ---

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

# --- Lexer ---

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

    def skip_comment(self):
        while self.current_char is not None and self.current_char != '\n':
            self.advance()
        self.advance()  # Skip the newline character

    def variable(self):
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
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
            if self.current_char == '#':
                self.skip_comment()
                continue
            if self.current_char.isalpha() or self.current_char == '_':
                if self.text[self.pos:self.pos+3] == 'let':
                    self.pos += 3
                    self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                    return Token('LET', 'let')
                if self.text[self.pos:self.pos+5] == 'print':
                    self.pos += 5
                    self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                    return Token('PRINT', 'print')
                return self.variable()
            if self.current_char.isdigit():
                return self.number()
            if self.current_char in '+-*/=();':
                token_type = {
                    '+': 'PLUS',
                    '-': 'MINUS',
                    '*': 'MUL',
                    '/': 'DIV',
                    '=': 'EQ',
                    ';': 'SEMICOLON',
                    '(': 'LPAREN',
                    ')': 'RPAREN'
                }[self.current_char]
                self.advance()
                return Token(token_type, token_type)
            self.error()
        return Token('EOF', None)

# --- AST Node Classes ---

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

# --- Parser ---

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
        if self.current_token.type == 'LET':
            self.eat('LET')
            var = self.current_token
            self.eat('VARIABLE')
            self.eat('EQ')
            value = self.expr()
            if self.current_token.type == 'SEMICOLON':
                self.eat('SEMICOLON')
            return Assign(var.value, value)
        elif self.current_token.type == 'PRINT':
            self.eat('PRINT')
            expr = self.expr()
            if self.current_token.type == 'SEMICOLON':
                self.eat('SEMICOLON')
            return Print(expr)
        self.error()

    def parse(self):
        return self.statement()

# --- Interpreter ---

class Interpreter:
    def __init__(self, parser):
        self.parser = parser
        self.variables = {}

    def error(self):
        raise Exception('Invalid syntax')

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    def visit_Num(self, node):
        return node.value

    def visit_Var(self, node):
        if node.name in self.variables:
            return self.variables[node.name]
        self.error()

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.op.type == 'PLUS':
            return left + right
        elif node.op.type == 'MINUS':
            return left - right
        elif node.op.type == 'MUL':
            return left * right
        elif node.op.type == 'DIV':
            return left / right
        self.error()

    def visit_Assign(self, node):
        self.variables[node.var] = self.visit(node.value)

    def visit_Print(self, node):
        result = self.visit(node.expr)
        print(result)

# --- Main Execution ---

def main():
    while True:
        try:
            text = input("MiniPy> ")
            if not text.strip():
                continue
            lexer = Lexer(text)
            parser = Parser(lexer)
            interpreter = Interpreter(parser)
            ast = parser.parse()
            if ast is not None:
                interpreter.visit(ast)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
