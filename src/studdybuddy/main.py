#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from studdybuddy.chat import answer_user
from studdybuddy.crew import Studdybuddy

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Answer a user's question from the command line.
    """
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("Ask Study Buddy: ").strip()

    try:
        print(answer_user(query))
    except Exception as e:
        raise Exception(f"An error occurred while answering the question: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'query': 'Solve this calculus problem: find the derivative of f(x) = x^2 * sin(x)'
    }
    try:
        Studdybuddy().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Studdybuddy().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'query': 'Solve this calculus problem: find the derivative of f(x) = x^2 * sin(x)'
    }

    try:
        Studdybuddy().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "query": trigger_payload.get("query", "")
    }

    try:
        result = Studdybuddy().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
