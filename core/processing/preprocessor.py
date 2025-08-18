"""Text preprocessing module for job descriptions.

Handles:
- HTML tag removal
- Text normalization
- Special character handling
- Whitespace normalization
"""

import re
import html
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Text preprocessing pipeline for job descriptions."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.remove_html = self.config.get('remove_html', True)
        self.normalize_whitespace = self.config.get('normalize_whitespace', True)
        self.remove_special_chars = self.config.get('remove_special_chars', False)
        self.min_length = self.config.get('min_length', 10)

        # Compile regex patterns for efficiency
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile frequently used regex patterns."""
        # HTML tags
        self.html_pattern = re.compile(r'<[^>]+>')

        # Multiple whitespace (spaces, tabs, newlines)
        self.whitespace_pattern = re.compile(r'\s+')

        # Special characters (keep only alphanumeric, spaces, and basic punctuation)
        self.special_chars_pattern = re.compile(r'[^\w\s\.\,\!\?\-\:\;\(\)\[\]\"\'\/\+\=\@\#\$\%\&\*]')

        # Email pattern (for preservation during cleaning)
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

        # URL pattern (for preservation during cleaning)
        self.url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+')

        # Bullet points and list markers
        self.bullet_pattern = re.compile(r'^[\s]*[•·▪▫◦‣⁃]\s*', re.MULTILINE)

        # Number bullets (1., 2., a), b), etc.)
        self.number_bullet_pattern = re.compile(r'^[\s]*(?:\d+\.|\w+\)|\w+\.)\s*', re.MULTILINE)

    def clean(self, text: str) -> str:
        """Main cleaning pipeline."""
        if not text or len(text.strip()) < self.min_length:
            return ""

        # Step 1: Decode HTML entities
        cleaned = html.unescape(text)

        # Step 2: Remove HTML tags
        if self.remove_html:
            cleaned = self._remove_html(cleaned)

        # Step 3: Normalize bullet points and lists
        cleaned = self._normalize_lists(cleaned)

        # Step 4: Remove special characters (but preserve important info)
        if self.remove_special_chars:
            cleaned = self._remove_special_chars(cleaned)

        # Step 5: Normalize whitespace
        if self.normalize_whitespace:
            cleaned = self._normalize_whitespace(cleaned)

        # Step 6: Final cleanup
        cleaned = self._final_cleanup(cleaned)

        return cleaned.strip()

    def _remove_html(self, text: str) -> str:
        """Remove HTML tags while preserving text content."""
        # Replace common HTML tags with appropriate spacing
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</?p[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</?div[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</?li[^>]*>', '\n• ', text, flags=re.IGNORECASE)
        text = re.sub(r'</?ul[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</?ol[^>]*>', '\n', text, flags=re.IGNORECASE)

        # Remove all remaining HTML tags
        text = self.html_pattern.sub(' ', text)

        return text

    def _normalize_lists(self, text: str) -> str:
        """Normalize bullet points and list formatting."""
        # Convert various bullet symbols to standard bullet
        text = self.bullet_pattern.sub('• ', text)

        # Normalize numbered lists
        text = self.number_bullet_pattern.sub('• ', text)

        return text

    def _remove_special_chars(self, text: str) -> str:
        """Remove special characters while preserving important information."""
        # Temporarily replace emails and URLs with placeholders
        emails = self.email_pattern.findall(text)
        urls = self.url_pattern.findall(text)

        email_placeholders = {}
        url_placeholders = {}

        for i, email in enumerate(emails):
            placeholder = f"__EMAIL_{i}__"
            email_placeholders[placeholder] = email
            text = text.replace(email, placeholder)

        for i, url in enumerate(urls):
            placeholder = f"__URL_{i}__"
            url_placeholders[placeholder] = url
            text = text.replace(url, placeholder)

        # Remove special characters
        text = self.special_chars_pattern.sub(' ', text)

        # Restore emails and URLs
        for placeholder, email in email_placeholders.items():
            text = text.replace(placeholder, email)

        for placeholder, url in url_placeholders.items():
            text = text.replace(placeholder, url)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace (multiple spaces, tabs, newlines)."""
        # Replace multiple whitespace with single space
        text = self.whitespace_pattern.sub(' ', text)

        # But preserve paragraph breaks (double newlines become single newlines)
        text = re.sub(r'\n\s*\n', '\n', text)

        return text

    def _final_cleanup(self, text: str) -> str:
        """Final cleanup and formatting."""
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]

        # Remove empty lines
        lines = [line for line in lines if line]

        # Join with single newlines
        text = '\n'.join(lines)

        # Fix common formatting issues
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)  # Ensure space after sentence end

        return text

    def extract_sections(self, text: str) -> Dict[str, str]:
        """Extract common job description sections."""
        sections = {}

        # Common section headers patterns
        section_patterns = {
            'requirements': r'(?:requirements?|qualifications?|skills?)\s*:?\s*\n(.*?)(?=\n(?:[A-Z][^:]*:|$))',
            'responsibilities': r'(?:responsibilities?|duties|role)\s*:?\s*\n(.*?)(?=\n(?:[A-Z][^:]*:|$))',
            'benefits': r'(?:benefits?|perks?|we offer)\s*:?\s*\n(.*?)(?=\n(?:[A-Z][^:]*:|$))',
            'about': r'(?:about us|company|who we are)\s*:?\s*\n(.*?)(?=\n(?:[A-Z][^:]*:|$))',
            'description': r'(?:job description|role description|overview)\s*:?\s*\n(.*?)(?=\n(?:[A-Z][^:]*:|$))'
        }

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section_name] = match.group(1).strip()

        return sections

    def get_statistics(self, original: str, cleaned: str) -> Dict[str, Any]:
        """Get preprocessing statistics."""
        return {
            'original_length': len(original),
            'cleaned_length': len(cleaned),
            'reduction_ratio': 1 - (len(cleaned) / len(original)) if original else 0,
            'original_words': len(original.split()) if original else 0,
            'cleaned_words': len(cleaned.split()) if cleaned else 0
        }
