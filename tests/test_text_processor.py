"""
Unit tests for text_processor script.

Tests the text processing functionality.
"""

import unittest
from scripts.text_processor import process_text


class TestTextProcessor(unittest.TestCase):
    """Test cases for text processor script."""
    
    def test_process_text_simple(self):
        """Test processing a simple text."""
        result = process_text("hello world")
        
        self.assertEqual(result['original'], "hello world")
        self.assertEqual(result['reversed'], "dlrow olleh")
        self.assertEqual(result['capitalized'], "Hello World")
        self.assertEqual(result['uppercase'], "HELLO WORLD")
        self.assertEqual(result['lowercase'], "hello world")
        self.assertEqual(result['word_count'], 2)
    
    def test_process_text_single_word(self):
        """Test processing a single word."""
        result = process_text("python")
        
        self.assertEqual(result['original'], "python")
        self.assertEqual(result['reversed'], "nohtyp")
        self.assertEqual(result['capitalized'], "Python")
        self.assertEqual(result['uppercase'], "PYTHON")
        self.assertEqual(result['lowercase'], "python")
        self.assertEqual(result['word_count'], 1)
    
    def test_process_text_multiple_words(self):
        """Test processing multiple words."""
        result = process_text("the quick brown fox")
        
        self.assertEqual(result['original'], "the quick brown fox")
        self.assertEqual(result['reversed'], "xof nworb kciuq eht")
        self.assertEqual(result['capitalized'], "The Quick Brown Fox")
        self.assertEqual(result['word_count'], 4)
    
    def test_process_text_with_mixed_case(self):
        """Test processing text with mixed case."""
        result = process_text("PyThOn RoCkS")
        
        self.assertEqual(result['original'], "PyThOn RoCkS")
        self.assertEqual(result['uppercase'], "PYTHON ROCKS")
        self.assertEqual(result['lowercase'], "python rocks")
        self.assertEqual(result['word_count'], 2)


if __name__ == "__main__":
    unittest.main()
