"""
Unit tests for string_utils module.

Tests the string manipulation utility functions.
"""

import unittest
from utilities.string_utils import reverse_string, capitalize_words


class TestStringUtils(unittest.TestCase):
    """Test cases for string utility functions."""
    
    def test_reverse_string_simple(self):
        """Test reversing a simple string."""
        self.assertEqual(reverse_string("hello"), "olleh")
    
    def test_reverse_string_with_spaces(self):
        """Test reversing a string with spaces."""
        self.assertEqual(reverse_string("hello world"), "dlrow olleh")
    
    def test_reverse_string_empty(self):
        """Test reversing an empty string."""
        self.assertEqual(reverse_string(""), "")
    
    def test_reverse_string_single_char(self):
        """Test reversing a single character."""
        self.assertEqual(reverse_string("a"), "a")
    
    def test_capitalize_words_simple(self):
        """Test capitalizing a simple phrase."""
        self.assertEqual(capitalize_words("hello world"), "Hello World")
    
    def test_capitalize_words_already_capitalized(self):
        """Test capitalizing already capitalized words."""
        self.assertEqual(capitalize_words("Hello World"), "Hello World")
    
    def test_capitalize_words_mixed_case(self):
        """Test capitalizing mixed case words."""
        self.assertEqual(capitalize_words("hELLo WoRLd"), "Hello World")
    
    def test_capitalize_words_single_word(self):
        """Test capitalizing a single word."""
        self.assertEqual(capitalize_words("python"), "Python")
    
    def test_capitalize_words_empty(self):
        """Test capitalizing an empty string."""
        self.assertEqual(capitalize_words(""), "")


if __name__ == "__main__":
    unittest.main()
