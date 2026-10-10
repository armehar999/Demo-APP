# ===== ENGINE =====
import ast
import math
import re

OWNER = "Abdul Rahman"


class CalcError(Exception):
    """User ko dikhane wala friendly error."""


FUNC_NAMES = [
    "asin", "acos", "atan", "sinh", "cosh", "tanh", "sin", "cos", "tan",
    "log", "ln", "sqrt", "cbrt", "abs", "exp", "fact",
]
FUNC_RE = "|".join(sorted(FUNC_NAMES, key=len, reverse=True))
NUM = r"(?:\d+\.?\d*|\.\d+)"


def normalize(text: str) -> str:
    """Display wali expression ko Python-safe expression bana deta hai."""
    s = text.strip().lower()
    s = (s.replace("×", "*").replace("÷", "/").replace("−", "-").replace("–", "-")
          .replace("π", "pi").replace("√", "sqrt").replace("^", "**").replace("%", "/100"))
    s = s.replace(" ", "")
    # 1e+20 jaisi scientific notation (result se aati hai)
    s = re.sub(rf"(?<![\w.])({NUM})e([+-]\d+)", r"\1*10**(\2)", s)
    # factorial: 5!
    s = re.sub(r"(\d+)!", r"fact(\1)", s)
    # implicit multiplication: 2pi, 3(4), )(, 2sin30, (2)3
    s = re.sub(r"(\d|\))(?=[a-z(])", r"\1*", s)
    s = re.sub(r"\)(?=\d|\.\d)", ")*", s)
    s = re.sub(r"\b(pi|e)\b(?=[\d.(a-z])", r"\1*", s)
    # bracket ke baghair function: sin30 -> sin(30), sqrt16 -> sqrt(16)
    s = re.sub(rf"\b({FUNC_RE})(-?{NUM}|pi|e)(?![\w.(])", r"\1(\2)", s)
    # adhoore brackets khud band kar do
    opens = s.count("(") - s.count(")")
    if opens > 0:
        s += ")" * opens
    return s


def _clean(v: float) -> float:
    return 0.0 if abs(v) < 1e-12 else v


def make_funcs(degrees: bool):
    to_rad = math.radians if degrees else (lambda x: x)
    from_rad = math.degrees if degrees else (lambda x: x)

    def tan(x):
        if abs(math.cos(to_rad(x))) < 1e-12:
            raise CalcError("tan is angle par define nahi hai")
        return _clean(math.tan(to_rad(x)))

    def fact(x):
        if x != int(x) or x < 0:
            raise CalcError("Factorial sirf 0 ya positive poore number ka hota hai")
        if x > 170:
            raise CalcError("Number bohat bara hai")
        return math.factorial(int(x))

    def log(x):
        if x <= 0:
            raise CalcError("log sirf positive number ka hota hai")
        return math.log10(x)

    def ln(x):
        if x <= 0:
            raise CalcError("ln sirf positive number ka hota hai")
        return math.log(x)

    def sqrt(x):
        if x < 0:
            raise CalcError("Negative number ka square root nahi hota")
        return math.sqrt(x)

    def cbrt(x):
        return math.copysign(abs(x) ** (1 / 3), x)

    return {
        "sin": lambda x: _clean(math.sin(to_rad(x))),
        "cos": lambda x: _clean(math.cos(to_rad(x))),
        "tan": tan,
        "asin": lambda x: from_rad(math.asin(x)),
        "acos": lambda x: from_rad(math.acos(x)),
        "atan": lambda x: from_rad(math.atan(x)),
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "log": log, "ln": ln, "sqrt": sqrt, "cbrt": cbrt,
        "abs": abs, "exp": math.exp, "fact": fact,
    }


BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Mod: lambda a, b: a % b,
    ast.FloorDiv: lambda a, b: a // b,
}
CONSTS = {"pi": math.pi, "e": math.e}


def evaluate(expr: str, degrees: bool = True):
    s = normalize(expr)
    if not s:
        raise CalcError("Pehle koi expression likhein")
    try:
        tree = ast.parse(s, mode="eval")
    except SyntaxError:
        raise CalcError("Expression adhoora ya ghalat hai")
    funcs = make_funcs(degrees)

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name) and node.id in CONSTS:
            return CONSTS[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = ev(node.operand)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp):
            a, b = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Pow):
                if a == 0 and b < 0:
                    raise CalcError("Zero se divide nahi ho sakta")
                if abs(b) > 100000:
                    raise CalcError("Number bohat bara hai")
                r = a ** b
                if isinstance(r, complex):
                    raise CalcError("Negative number ka fractional power nahi hota")
                return r
            if type(node.op) in BIN_OPS:
                return BIN_OPS[type(node.op)](a, b)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in funcs and len(node.args) == 1 and not node.keywords):
            return funcs[node.func.id](ev(node.args[0]))
        raise CalcError("Expression ghalat hai")

    try:
        val = ev(tree)
        if isinstance(val, int) and abs(val) >= 10 ** 15:
            val = float(val)
    except ZeroDivisionError:
        raise CalcError("Zero se divide nahi ho sakta")
    except OverflowError:
        raise CalcError("Number bohat bara hai")
    except ValueError:
        raise CalcError("Is value par function define nahi hai")
    if isinstance(val, float) and not math.isfinite(val):
        raise CalcError("Number bohat bara hai")
    return val


def fmt(v) -> str:
    if isinstance(v, int) and abs(v) < 10 ** 15:
        return str(v)
    v = float(v)
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return f"{v:.12g}"


# ===== UI =====
from html import escape

import streamlit as st

st.set_page_config(page_title=f"Scientific Calculator | {OWNER}", page_icon="🧮", layout="centered")

CSS = """
<style>
.stApp{background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 55%,#312e81 100%);}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer{visibility:hidden;}
.block-container{max-width:560px;padding-top:1.5rem;padding-bottom:2rem;}

.hero{text-align:center;margin-bottom:.6rem;}
.hero h1{color:#fff;font-size:2rem;margin:0;padding:0;}
.hero .by{font-size:1.05rem;color:#cbd5e1;margin-top:.2rem;}
.hero .by b{background:linear-gradient(90deg,#fbbf24,#f472b6,#818cf8);
  -webkit-background-clip:text;background-clip:text;color:transparent;font-size:1.25rem;}

/* mobile par bhi columns ek row mein rahein */
div[data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;gap:.45rem !important;}
div[data-testid="stColumn"], div[data-testid="column"]{min-width:0 !important;flex:1 1 0 !important;}

/* display box */
.stTextInput input{background:#0b1220 !important;color:#f8fafc !important;font-size:1.6rem !important;
  text-align:right;border-radius:14px !important;height:3.4rem;border:2px solid #6366f1 !important;}
.stTextInput input:focus{border-color:#f472b6 !important;box-shadow:0 0 0 2px rgba(244,114,182,.35) !important;}
[data-testid="stForm"]{border:none !important;padding:0 !important;}
[data-testid="InputInstructions"]{display:none;}

.stRadio label, .stRadio p{color:#e2e8f0 !important;}

.res{background:rgba(15,23,42,.75);border:1px solid #4338ca;border-radius:14px;padding:.7rem 1rem;
  margin:.2rem 0 .7rem 0;text-align:right;color:#cbd5e1;}
.res b{display:block;font-size:1.9rem;color:#34d399;word-break:break-all;}
.err{background:rgba(127,29,29,.55);border:1px solid #ef4444;color:#fecaca;border-radius:14px;
  padding:.7rem 1rem;margin:.2rem 0 .7rem 0;}

/* buttons */
.stButton>button, [data-testid="stFormSubmitButton"]>button{
  height:3.2rem;border-radius:14px;border:none;font-weight:700;font-size:1.1rem;color:#fff;
  box-shadow:0 3px 8px rgba(0,0,0,.35);transition:transform .08s, filter .15s;}
.stButton>button *, [data-testid="stFormSubmitButton"]>button *{color:#fff !important;}
.stButton>button:hover, [data-testid="stFormSubmitButton"]>button:hover{filter:brightness(1.18);}
.stButton>button:active, [data-testid="stFormSubmitButton"]>button:active{transform:scale(.95);}
[class*="st-key-num_"] button{background:#334155;}
[class*="st-key-fn_"] button{background:linear-gradient(135deg,#7c3aed,#6366f1);}
[class*="st-key-const_"] button{background:linear-gradient(135deg,#0ea5e9,#06b6d4);}
[class*="st-key-op_"] button{background:linear-gradient(135deg,#f59e0b,#f97316);}
[class*="st-key-ctrl_"] button{background:linear-gradient(135deg,#ef4444,#be123c);}
[data-testid="stFormSubmitButton"]>button{background:linear-gradient(135deg,#10b981,#059669);}

.foot{text-align:center;color:#94a3b8;margin-top:1.2rem;font-size:.9rem;}
.foot b{color:#e2e8f0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---- state ----
for _k, _v in {"expr": "", "error": "", "fresh": False, "last_expr": "", "last_result": "", "history": []}.items():
    st.session_state.setdefault(_k, _v)


def calculate():
    expr = st.session_state.expr
    try:
        out = fmt(evaluate(expr, st.session_state.angle_mode == "Degree"))
    except CalcError as e:
        st.session_state.error = str(e)
        return
    st.session_state.error = ""
    st.session_state.last_expr = expr.strip()
    st.session_state.last_result = out
    st.session_state.history.insert(0, (expr.strip(), out))
    st.session_state.history = st.session_state.history[:10]
    st.session_state.expr = out
    st.session_state.fresh = True


def press(token: str, kind: str):
    expr = st.session_state.expr
    if st.session_state.fresh and kind in ("num", "fn", "const", "open"):
        expr = ""  # naya hisaab shuru
    st.session_state.fresh = False
    st.session_state.error = ""
    if kind == "ctrl":
        expr = "" if token == "CLR" else expr[:-1]
        if token == "CLR":
            st.session_state.last_expr = st.session_state.last_result = ""
    else:
        expr += token
    st.session_state.expr = expr


# ---- header ----
st.markdown(
    f'<div class="hero"><h1>🧮 Scientific Calculator</h1>'
    f'<div class="by">Created by <b>{escape(OWNER)}</b></div></div>',
    unsafe_allow_html=True,
)

st.radio("Angle mode", ["Degree", "Radian"], horizontal=True, key="angle_mode", label_visibility="collapsed")

# ---- display + Enter key ----
with st.form("calc_form", clear_on_submit=False):
    c1, c2 = st.columns([5, 1])
    with c1:
        st.text_input("Expression", key="expr", placeholder="e.g. sin30 + sqrt16 * 5  (Enter dabayen)",
                      label_visibility="collapsed")
    with c2:
        st.form_submit_button("=", on_click=calculate, use_container_width=True)

if st.session_state.error:
    st.markdown(f'<div class="err">⚠️ {escape(st.session_state.error)}</div>', unsafe_allow_html=True)
elif st.session_state.last_result:
    st.markdown(
        f'<div class="res">{escape(st.session_state.last_expr)} =<b>{escape(st.session_state.last_result)}</b></div>',
        unsafe_allow_html=True,
    )

# ---- keypad ----
KEYPAD = [
    [("sin", "fn", "sin"), ("cos", "fn", "cos"), ("tan", "fn", "tan"), ("log", "fn", "log"), ("ln", "fn", "ln")],
    [("sin⁻¹", "fn", "asin"), ("cos⁻¹", "fn", "acos"), ("tan⁻¹", "fn", "atan"), ("√", "fn", "√"), ("x²", "op", "^2")],
    [("π", "const", "pi"), ("e", "const", "e"), ("(", "open", "("), (")", "op", ")"), ("n!", "op", "!")],
    [("7", "num", "7"), ("8", "num", "8"), ("9", "num", "9"), ("÷", "op", "÷"), ("DEL", "ctrl", "DEL")],
    [("4", "num", "4"), ("5", "num", "5"), ("6", "num", "6"), ("×", "op", "×"), ("CLR", "ctrl", "CLR")],
    [("1", "num", "1"), ("2", "num", "2"), ("3", "num", "3"), ("−", "op", "−"), ("+", "op", "+")],
    [("0", "num", "0"), (".", "num", "."), ("^", "op", "^"), ("%", "op", "%"), ("abs", "fn", "abs")],
]

for r, row in enumerate(KEYPAD):
    cols = st.columns(5)
    for c, (label, kind, token) in enumerate(row):
        with cols[c]:
            st.button(label, key=f"{kind}_{r}_{c}", on_click=press, args=(token, kind), use_container_width=True)

with st.expander("🕘 History"):
    if st.session_state.history:
        for e, res in st.session_state.history:
            st.write(f"`{e}` = **{res}**")
    else:
        st.caption("Abhi koi hisaab nahi hua.")

st.markdown(f'<div class="foot">© 2026 <b>{escape(OWNER)}</b> • Made with ❤️ in Streamlit</div>', unsafe_allow_html=True)
