"""
String utility functions for text processing.

This module provides common string manipulation utilities.
"""


def reverse_string(text: str) -> str:
    """
    Reverse the given string.
    
    Args:
        text: The string to reverse
        
    Returns:
        The reversed string
        
    Examples:
        >>> reverse_string("hello")
        'olleh'
        >>> reverse_string("Python")
        'nohtyP'
    """
    return text[::-1]


def capitalize_words(text: str) -> str:
    """
    Capitalize the first letter of each word in the string.
    
    Args:
        text: The string to capitalize
        
    Returns:
        String with each word capitalized
        
    Examples:
        >>> capitalize_words("hello world")
        'Hello World'
        >>> capitalize_words("python is awesome")
        'Python Is Awesome'
    """
    return ' '.join(word.capitalize() for word in text.split())
