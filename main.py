import ast
import html
import math
import operator

import streamlit as st


def _trig_functions(angle_mode):
	angle_in = math.radians if angle_mode == "Degrees" else float
	angle_out = math.degrees if angle_mode == "Degrees" else float
	return {
		"sin": lambda value: math.sin(angle_in(value)),
		"cos": lambda value: math.cos(angle_in(value)),
		"tan": lambda value: math.tan(angle_in(value)),
		"asin": lambda value: angle_out(math.asin(value)),
		"acos": lambda value: angle_out(math.acos(value)),
		"atan": lambda value: angle_out(math.atan(value)),
		"atan2": lambda y, x: angle_out(math.atan2(y, x)),
	}


def evaluate(expression, angle_mode, answer=0):
	functions = {
		**_trig_functions(angle_mode),
		"sinh": math.sinh,
		"cosh": math.cosh,
		"tanh": math.tanh,
		"asinh": math.asinh,
		"acosh": math.acosh,
		"atanh": math.atanh,
		"sqrt": math.sqrt,
		"cbrt": math.cbrt,
		"exp": math.exp,
		"expm1": math.expm1,
		"ln": math.log,
		"log": math.log,
		"log10": math.log10,
		"log2": math.log2,
		"log1p": math.log1p,
		"abs": abs,
		"fabs": math.fabs,
		"round": round,
		"ceil": math.ceil,
		"floor": math.floor,
		"trunc": math.trunc,
		"factorial": math.factorial,
		"comb": math.comb,
		"perm": math.perm,
		"gcd": math.gcd,
		"lcm": math.lcm,
		"min": min,
		"max": max,
		"sum": sum,
		"prod": math.prod,
		"hypot": math.hypot,
		"fmod": math.fmod,
		"remainder": math.remainder,
		"copysign": math.copysign,
		"degrees": math.degrees,
		"radians": math.radians,
		"pow": pow,
	}
	constants = {"pi": math.pi, "e": math.e, "tau": math.tau, "ans": answer}
	binary_operators = {
		ast.Add: operator.add,
		ast.Sub: operator.sub,
		ast.Mult: operator.mul,
		ast.Div: operator.truediv,
		ast.FloorDiv: operator.floordiv,
		ast.Mod: operator.mod,
		ast.Pow: operator.pow,
		ast.BitXor: operator.pow,
	}
	unary_operators = {ast.UAdd: operator.pos, ast.USub: operator.neg}

	if not expression.strip() or len(expression) > 200:
		raise ValueError("Enter an expression up to 200 characters long.")

	tree = ast.parse(expression.replace("^", "**"), mode="eval")

	def checked(value):
		if isinstance(value, complex):
			raise ValueError("Complex results are not supported.")
		if isinstance(value, (int, float)) and abs(value) > 1e308:
			raise ValueError("The result is outside the real number range.")
		if isinstance(value, float) and not math.isfinite(value):
			raise ValueError("The result is outside the real number range.")
		return value

	def calculate(node):
		if isinstance(node, ast.Expression):
			return calculate(node.body)
		if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
			return node.value
		if isinstance(node, (ast.List, ast.Tuple)):
			return [calculate(element) for element in node.elts]
		if isinstance(node, ast.Name):
			if node.id in constants:
				return constants[node.id]
			raise ValueError(f"Unknown name: {node.id}")
		if isinstance(node, ast.BinOp) and type(node.op) in binary_operators:
			left, right = calculate(node.left), calculate(node.right)
			if isinstance(node.op, ast.Pow) and abs(right) > 1000:
				raise ValueError("Exponent magnitude must be 1,000 or less.")
			return checked(binary_operators[type(node.op)](left, right))
		if isinstance(node, ast.UnaryOp) and type(node.op) in unary_operators:
			return checked(unary_operators[type(node.op)](calculate(node.operand)))
		if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
			function = functions.get(node.func.id)
			if function is None or node.keywords:
				raise ValueError("That function is not available.")
			return checked(function(*(calculate(argument) for argument in node.args)))
		raise ValueError("Use numbers, operators, constants, and supported functions only.")

	result = calculate(tree)
	if isinstance(result, complex) or not math.isfinite(result):
		raise ValueError("The result is outside the real number range.")
	return result


def insert_text(text):
	st.session_state.expression += text


def clear_expression():
	st.session_state.expression = ""


def delete_character():
	st.session_state.expression = st.session_state.expression[:-1]


def calculate_result():
	expression = st.session_state.expression.strip()
	try:
		result = evaluate(
			expression,
			st.session_state.angle_mode,
			st.session_state.get("answer", 0),
		)
		st.session_state.answer = result
		st.session_state.result = result
		st.session_state.history.insert(0, (expression, result))
		st.session_state.history = st.session_state.history[:10]
		st.session_state.error = ""
	except (ArithmeticError, SyntaxError, TypeError, ValueError) as error:
		st.session_state.error = str(error) or "Unable to calculate this expression."


st.set_page_config(page_title="Scientific Calculator", page_icon="∑", layout="wide")
st.markdown(
	"""
	<style>
	@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
	:root { --ink: #172b2b; --muted: #637373; --paper: #f4f6f2; --line: #dce3dc; --accent: #d35232; --key: #ffffff; }
	.stApp { background: var(--paper); color: var(--ink); font-family: 'Manrope', sans-serif; }
	[data-testid="stHeader"] { background: transparent; }
	.block-container { max-width: 1100px; padding-top: 2.5rem; padding-bottom: 3rem; }
	h1 { font-family: 'Manrope', sans-serif; font-size: 2rem !important; font-weight: 800 !important; letter-spacing: 0 !important; color: var(--ink); }
	.eyebrow { color: var(--accent); font-size: .75rem; font-weight: 800; text-transform: uppercase; letter-spacing: .12em; }
	[data-testid="stTextInput"] input { font-family: 'DM Mono', monospace; font-size: 1.55rem; min-height: 3.8rem; background: #fff; border: 1px solid var(--line); border-radius: 6px; color: var(--ink); }
	[data-testid="stButton"] button { width: 100%; min-height: 3.1rem; border-radius: 5px; border: 1px solid var(--line); background: var(--key); color: var(--ink); font: 600 1rem 'DM Mono', monospace; transition: border-color .15s, transform .15s, background .15s; }
	[data-testid="stButton"] button:hover { border-color: var(--accent); background: #fff8f4; color: var(--accent); transform: translateY(-1px); }
	[data-testid="stButton"] button[kind="primary"] { background: var(--accent); border-color: var(--accent); color: #fff; }
	[data-testid="stButton"] button[kind="primary"]:hover { background: #b94227; color: #fff; }
	.result { font: 500 1.55rem 'DM Mono', monospace; color: var(--ink); padding: .5rem 0 1rem; overflow-wrap: anywhere; }
	.history-expression { font: 500 .9rem 'DM Mono', monospace; color: var(--muted); }
	.history-result { font: 600 1.05rem 'DM Mono', monospace; color: var(--ink); margin: .2rem 0 .9rem; }
	@media (max-width: 640px) { .block-container { padding: 1.2rem 1rem 2rem; } h1 { font-size: 1.65rem !important; } [data-testid="stButton"] button { min-height: 2.8rem; font-size: .86rem; } }
	</style>
	""",
	unsafe_allow_html=True,
)

for key, default in {
	"expression": "",
	"angle_mode": "Radians",
	"answer": 0,
	"result": None,
	"error": "",
	"history": [],
}.items():
	st.session_state.setdefault(key, default)

st.markdown('<div class="eyebrow">Precision instruments / 01</div>', unsafe_allow_html=True)
st.title("Scientific calculator")
calculator, history_column = st.columns([1.65, 1], gap="large")

with calculator:
	st.radio("Angle unit", ["Radians", "Degrees"], horizontal=True, key="angle_mode")
	st.text_input("Expression", key="expression", placeholder="Try sin(pi / 4) or log(100, 10)", label_visibility="collapsed")
	if st.session_state.result is not None:
		st.markdown(f'<div class="result">= {html.escape(format(st.session_state.result, ".12g"))}</div>', unsafe_allow_html=True)
	if st.session_state.error:
		st.error(st.session_state.error)

	key_rows = [
		[("sin(", "sin("), ("cos(", "cos("), ("tan(", "tan("), ("asin(", "asin("), ("acos(", "acos(")],
		[("atan(", "atan("), ("sinh(", "sinh("), ("cosh(", "cosh("), ("tanh(", "tanh("), ("sqrt(", "sqrt(")],
		[("ln(", "ln("), ("log₁₀(", "log10("), ("eˣ", "exp("), ("x²", "^2"), ("xʸ", "^")],
		[("π", "pi"), ("e", "e"), ("Ans", "ans"), ("(", "("), (")", ")")],
		[("7", "7"), ("8", "8"), ("9", "9"), ("÷", "/"), ("⌫", "delete")],
		[("4", "4"), ("5", "5"), ("6", "6"), ("×", "*"), ("−", "-")],
		[("1", "1"), ("2", "2"), ("3", "3"), ("+", "+"), ("%", "%")],
		[("0", "0"), (".", "."), ("!", "factorial("), ("C", "clear"), ("=", "equals")],
	]
	for row_index, row in enumerate(key_rows):
		columns = st.columns(5, gap="small")
		for column, (label, value) in zip(columns, row):
			with column:
				if value == "delete":
					st.button(label, key=f"key-{row_index}-{label}", on_click=delete_character)
				elif value == "clear":
					st.button(label, key=f"key-{row_index}-{label}", on_click=clear_expression)
				elif value == "equals":
					st.button(label, key=f"key-{row_index}-{label}", type="primary", on_click=calculate_result)
				else:
					st.button(label, key=f"key-{row_index}-{label}", on_click=insert_text, args=(value,))

with history_column:
	st.subheader("Recent calculations")
	if st.session_state.history:
		for expression, result in st.session_state.history:
			st.markdown(
				f'<div class="history-expression">{html.escape(expression)}</div>'
				f'<div class="history-result">= {html.escape(format(result, ".12g"))}</div>',
				unsafe_allow_html=True,
			)
		st.button("Clear history", on_click=lambda: st.session_state.update(history=[]))
	else:
		st.caption("Your last ten results will appear here.")

with st.expander("Functions"):
	st.write(
		"**Trigonometry:** sin, cos, tan, asin, acos, atan, atan2, sinh, cosh, tanh, asinh, acosh, atanh. "
		"**Numerical:** sqrt, cbrt, exp, ln, log, log10, log2, abs, round, ceil, floor, factorial, comb, perm, gcd, lcm, min, max, sum, prod, hypot, degrees, radians. "
		"Constants: pi, e, tau, ans. Use ^ for powers."
	)
