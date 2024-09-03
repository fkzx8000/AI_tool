import ast

with open('app.py', 'r') as file:
    code = file.read()

lines = code.split('\n')
num_lines = len(lines)
long_lines = [line for line in lines if len(line) > 79]

parsed_code = ast.parse(code)
functions = [node for node in parsed_code.body if isinstance(node, ast.FunctionDef)]

functions_missing_docstrings = [
    func for func in functions
    if not (func.body and isinstance(func.body[0], ast.Expr) and isinstance(func.body[0].value, ast.Constant))
]

print("Total lines:", num_lines)
print("Lines longer than 79 characters:", len(long_lines))
print("Functions missing docstrings:", len(functions_missing_docstrings))
