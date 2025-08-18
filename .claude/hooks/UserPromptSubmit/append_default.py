"""
Append default tokens to the user prompt.
"""

import json
import sys


def main() -> None:
    """
    Append default tokens to the user prompt.
    
    Args:
        user_prompt (str): The original user prompt.
    
    Returns:
        str: The modified user prompt with default tokens appended.
    """
    try:
        data = json.loads(sys.stdin)
        user_prompt = data.get("prompt", None)
        if user_prompt:
            print("\nThink harder to this problem, analyze it, and provide a short  and simple answer.")
            sys.exit(0)
    except Exception as e:
        print(f"Error reading user prompt: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()