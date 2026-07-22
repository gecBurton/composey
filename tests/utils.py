import os


def get_examples():
    """Utility to find all example directories."""
    root_dir = os.path.dirname(os.path.dirname(__file__))
    examples_dir = os.path.join(root_dir, "examples")
    return sorted(
        d
        for d in os.listdir(examples_dir)
        if os.path.isdir(os.path.join(examples_dir, d))
    )
