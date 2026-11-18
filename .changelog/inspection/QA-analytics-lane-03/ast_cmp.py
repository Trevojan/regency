"""Compare every top-level node except selftest() between two copies of a script. Usage: ast_cmp.py <a.py> <b.py>"""
import ast, sys
def nodes(p):
    t = ast.parse(open(p, encoding="utf-8").read())
    return [(getattr(n, "name", type(n).__name__), ast.dump(n)) for n in t.body if getattr(n, "name", None) != "selftest"]
a, b = nodes(sys.argv[1]), nodes(sys.argv[2])
print(sys.argv[1].split("/")[-1], "top-level nodes", len(a), "vs", len(b), "| identical outside selftest():", a == b)
