from pathlib import Path


def load_prompt_template(template_name: str) -> str:
    """
    Load prompt template from prompts/ directory

    Args:
        template_name: Name of the template file (without .txt extension)

    Returns:
        Template content as string
    """
    template_path = Path("prompts") / f"{template_name}.txt"

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def clean_incomplete_sentences(text: str) -> str:
    """
    Remove incomplete sentences from the end of generated text
    
    Args:
        text: Generated text that may end with incomplete sentence
    
    Returns:
        Cleaned text with only complete sentences
    """
    if not text or not text.strip():
        return text

    # Split into lines
    lines = text.strip().split('\n')

    # Check last non-empty line
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()

        if not line:  # Skip empty lines
            continue

        # Check if line ends with proper sentence termination
        # Valid endings: . ! ? " (quote after punctuation) ) (parenthesis)
        valid_endings = ('.', '!', '?', '."', '!"', '?"', '.)', '!)', '?)')

        if line.endswith(valid_endings):
            # Line is complete, keep everything up to here
            return '\n'.join(lines[:i+1])

        # Check for common incomplete patterns
        incomplete_patterns = [
            line.endswith(','),           # Ends with comma
            line.endswith('and'),         # Ends with conjunction
            line.endswith('or'),
            line.endswith('the'),         # Ends with article
            line.endswith('a'),
            line.endswith('an'),
            line.endswith('of'),          # Ends with preposition
            line.endswith('in'),
            line.endswith('to'),
            line.endswith('for'),
            line.endswith('with'),
            line.endswith('#'),           # Hashtag cutoff
            line[-1].isalpha() and not line.endswith(valid_endings),  # Letter without punctuation
        ]

        if any(incomplete_patterns):
            # Remove this incomplete line, check previous
            continue
        else:
            # Ambiguous case - keep it if it looks reasonable
            return '\n'.join(lines[:i+1])

    # If we get here, return original (safety fallback)
    return text


def fix_incomplete_json(json_str: str) -> str:
    """
    Attempt to fix incomplete JSON by adding missing closing brackets
    
    Args:
        json_str: Potentially incomplete JSON string
    
    Returns:
        Fixed JSON string
    """
    # Count opening and closing brackets
    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    
    # Add missing closing characters
    result = json_str
    
    # Close any unterminated strings (basic attempt)
    if result.count('"') % 2 != 0:
        result += '"'
    
    # Add missing closing braces
    for _ in range(open_braces - close_braces):
        result += '\n  }'
    
    # Add missing closing brackets
    for _ in range(open_brackets - close_brackets):
        result += '\n]'
    
    return result
