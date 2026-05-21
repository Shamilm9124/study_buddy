import math
import re
import sys
from pathlib import Path

import streamlit as st

from studdybuddy.chat import answer_user
from studdybuddy.flashcards import (
    CHECK_MARK,
    generate_flashcards,
    save_flashcards,
)


st.set_page_config(page_title="Study Buddy", page_icon="SB", layout="wide")

ALLOWED_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log10,
    "ln": math.log,
    "abs": abs,
    "factorial": math.factorial,
}


def trig_value(function_name: str, value: float) -> float:
    if st.session_state.angle_mode == "DEG":
        value = math.radians(value)
    return ALLOWED_FUNCTIONS[function_name](value)


def add_implicit_multiplication(expression: str) -> str:
    expression = re.sub(
        r"(\d|\)|pi|e)(?=(sin|cos|tan|sqrt|log|ln|abs|factorial|\(|pi|e))",
        r"\1*",
        expression,
    )
    return re.sub(r"(\)|pi|e)(?=\d)", r"\1*", expression)


def apply_factorials(expression: str) -> str:
    pattern = re.compile(r"(\d+(?:\.\d+)?|\([^()]*\))!")
    while pattern.search(expression):
        expression = pattern.sub(r"factorial(\1)", expression)
    return expression


def calculate(expression: str) -> float:
    cleaned = expression.replace(" ", "").replace("^", "**").replace("%", "/100")
    cleaned = apply_factorials(cleaned)
    cleaned = add_implicit_multiplication(cleaned)

    if not re.fullmatch(r"[0-9+\-*/().,a-zA-Z_*]+", cleaned):
        raise ValueError("Unsupported characters")

    unknown_names = re.sub(
        r"sin|cos|tan|sqrt|log|ln|abs|factorial|pi|e",
        "",
        cleaned,
    )
    if re.search(r"[a-zA-Z]", unknown_names):
        raise ValueError("Unsupported function")

    scope = {
        "sin": lambda value: trig_value("sin", value),
        "cos": lambda value: trig_value("cos", value),
        "tan": lambda value: trig_value("tan", value),
        "sqrt": math.sqrt,
        "log": math.log10,
        "ln": math.log,
        "abs": abs,
        "factorial": factorial_value,
        "pi": math.pi,
        "e": math.e,
    }
    result = eval(cleaned, {"__builtins__": {}}, scope)
    if not isinstance(result, (int, float)) or not math.isfinite(result):
        raise ValueError("Invalid result")
    return float(result)


def format_number(value: float) -> str:
    if abs(value) >= 1e12 or (0 < abs(value) < 1e-9):
        return f"{value:.8e}".replace(".00000000e", "e")
    return f"{value:.12g}"


def factorial_value(value: float) -> int:
    if not float(value).is_integer() or value < 0 or value > 170:
        raise ValueError("Invalid factorial")
    return math.factorial(int(value))


def append_calc(value: str) -> None:
    st.session_state.calc_expression += value


def clear_calc() -> None:
    st.session_state.calc_expression = ""
    st.session_state.calc_result = "0"


def backspace_calc() -> None:
    st.session_state.calc_expression = st.session_state.calc_expression[:-1]


def solve_calc() -> None:
    try:
        result = calculate(st.session_state.calc_expression)
        st.session_state.last_answer = result
        st.session_state.calc_expression = format_number(result)
        st.session_state.calc_result = format_number(result)
    except Exception:
        st.session_state.calc_result = "Error"


def render_calculator() -> None:
    with st.sidebar:
        top_left, top_right = st.columns([1, 0.2])
        top_left.subheader("Scientific Calculator")
        if top_right.button("X", help="Close calculator"):
            st.session_state.show_calculator = False
            st.rerun()

        st.radio(
            "Angle mode",
            ["DEG", "RAD"],
            key="angle_mode",
            horizontal=True,
            label_visibility="collapsed",
        )

        st.text_input("Expression", key="calc_expression")
        try:
            if st.session_state.calc_expression:
                st.session_state.calc_result = format_number(
                    calculate(st.session_state.calc_expression)
                )
        except Exception:
            st.session_state.calc_result = ""

        st.metric("Result", st.session_state.calc_result or " ")

        rows = [
            [
                ("AC", clear_calc),
                ("DEL", backspace_calc),
                ("(", lambda: append_calc("(")),
                (")", lambda: append_calc(")")),
                ("/", lambda: append_calc("/")),
            ],
            [
                ("sin", lambda: append_calc("sin(")),
                ("cos", lambda: append_calc("cos(")),
                ("tan", lambda: append_calc("tan(")),
                ("sqrt", lambda: append_calc("sqrt(")),
                ("x^y", lambda: append_calc("^")),
            ],
            [
                ("log", lambda: append_calc("log(")),
                ("ln", lambda: append_calc("ln(")),
                ("pi", lambda: append_calc("pi")),
                ("e", lambda: append_calc("e")),
                ("n!", lambda: append_calc("!")),
            ],
            [
                ("7", lambda: append_calc("7")),
                ("8", lambda: append_calc("8")),
                ("9", lambda: append_calc("9")),
                ("*", lambda: append_calc("*")),
                ("abs", lambda: append_calc("abs(")),
            ],
            [
                ("4", lambda: append_calc("4")),
                ("5", lambda: append_calc("5")),
                ("6", lambda: append_calc("6")),
                ("-", lambda: append_calc("-")),
                ("%", lambda: append_calc("%")),
            ],
            [
                ("1", lambda: append_calc("1")),
                ("2", lambda: append_calc("2")),
                ("3", lambda: append_calc("3")),
                ("+", lambda: append_calc("+")),
                ("+/-", lambda: append_calc("-(")),
            ],
            [
                ("0", lambda: append_calc("0")),
                (".", lambda: append_calc(".")),
                ("=", solve_calc),
                ("ANS", lambda: append_calc(format_number(st.session_state.last_answer))),
            ],
        ]

        for row_index, row in enumerate(rows):
            columns = st.columns(len(row))
            for column, (label, action) in zip(columns, row):
                column.button(
                    label,
                    key=f"calc_{row_index}_{label}",
                    on_click=action,
                    use_container_width=True,
                )

        st.caption(
            "Use DEG for school trig problems. Switch to RAD for calculus and unit-circle work."
        )


def render_flashcards(payload: dict) -> None:
    st.subheader("Today's Learning Summary")
    for concept in payload.get("summary", []):
        st.markdown(f"{CHECK_MARK} {concept}")

    st.subheader("Flashcards")
    for index, card in enumerate(payload.get("cards", []), start=1):
        title = card.get("title") or f"Flashcard {index}"
        with st.expander(title, expanded=index == 1):
            st.markdown("**Question:**")
            st.markdown(card.get("question", ""))
            st.markdown("**Answer:**")
            st.markdown(card.get("answer", ""))


def handle_flashcard_click() -> None:
    flashcards = generate_flashcards(st.session_state.messages)
    save_flashcards(flashcards)
    st.session_state.flashcards = flashcards


if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_calculator" not in st.session_state:
    st.session_state.show_calculator = False
if "calc_expression" not in st.session_state:
    st.session_state.calc_expression = ""
if "calc_result" not in st.session_state:
    st.session_state.calc_result = "0"
if "last_answer" not in st.session_state:
    st.session_state.last_answer = 0.0
if "angle_mode" not in st.session_state:
    st.session_state.angle_mode = "DEG"
if "flashcards" not in st.session_state:
    st.session_state.flashcards = None

if st.session_state.show_calculator:
    render_calculator()

header_left, header_right = st.columns([1, 0.16])
with header_left:
    st.title(":blue[Study Buddy]")
    st.caption("AI Learning Assistant")
with header_right:
    if st.button("Calculator", use_container_width=True):
        st.session_state.show_calculator = not st.session_state.show_calculator
        st.rerun()

personality = st.selectbox(
    "Explain Like",
    ["Teacher", "Friend", "Exam Coach", "Socratic Mentor"],
    key="learning_personality",
)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = answer_user(prompt, personality)
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

if st.session_state.messages:
    if st.button("Generate Flashcards", key="generate_session_flashcards"):
        with st.spinner("Creating flashcards..."):
            try:
                handle_flashcard_click()
            except Exception as exc:
                st.error(f"Could not generate flashcards: {exc}")
    if st.session_state.flashcards:
        render_flashcards(st.session_state.flashcards)


def run():
    from streamlit.web import cli

    sys.argv = ["streamlit", "run", str(Path(__file__).resolve())]
    cli.main()
