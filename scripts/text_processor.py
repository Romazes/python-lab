#!/usr/bin/env python3
"""
Text Processor Script

A simple script that demonstrates text processing using utility functions.
This script reads input text and applies various transformations.

Usage:
    python text_processor.py [text]
    
Example:
    python text_processor.py "hello world"
"""

import sys
import os

# Add parent directory to path to import utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.string_utils import reverse_string, capitalize_words


def process_text(text: str) -> dict:
    """
    Process the input text with various transformations.
    
    Args:
        text: The text to process
        
    Returns:
        Dictionary containing different text transformations
    """
    return {
        'original': text,
        'reversed': reverse_string(text),
        'capitalized': capitalize_words(text),
        'uppercase': text.upper(),
        'lowercase': text.lower(),
        'word_count': len(text.split())
    }


def main():
    """Main function to run the text processor."""
    if len(sys.argv) < 2:
        print("Usage: python text_processor.py [text]")
        print("Example: python text_processor.py 'hello world'")
        sys.exit(1)
    
    input_text = ' '.join(sys.argv[1:])
    
    print("=" * 50)
    print("Text Processor Results")
    print("=" * 50)
    
    results = process_text(input_text)
    
    for key, value in results.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
