"""Rule-based information extraction from job descriptions.

Extracts structured information using regex patterns:
- Dates and durations
- Contact information (emails, phones, URLs)
- Salary information
- Work arrangements (remote, hybrid, onsite)
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RuleBasedExtractor:
    """Extract structured information using regex patterns."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.extract_dates = self.config.get('extract_dates', True)
        self.extract_emails = self.config.get('extract_emails', True)
        self.extract_urls = self.config.get('extract_urls', True)
        self.extract_phone = self.config.get('extract_phone', True)
        self.extract_salary = self.config.get('extract_salary', True)
        self.extract_work_arrangement = self.config.get('extract_work_arrangement', True)

        self._compile_patterns()

    def _compile_patterns(self):
        """Compile all regex patterns for efficiency."""

        # Date patterns
        self.date_patterns = [
            # Standard formats: 01/01/2024, 1-1-2024, 01.01.2024
            re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b'),
            re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b'),

            # Month year: January 2024, Jan 2024
            re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b', re.IGNORECASE),

            # Relative dates: immediately, ASAP, within 2 weeks
            re.compile(r'\b(?:immediately|asap|urgent|within\s+\d+\s+(?:days?|weeks?|months?))\b', re.IGNORECASE),
        ]

        # Duration patterns
        self.duration_patterns = [
            # X years experience, 2-5 years, 3+ years
            re.compile(r'\b\d+[-+]?\s*(?:to\s+\d+\s*)?years?\s*(?:of\s*)?(?:experience|exp)\b', re.IGNORECASE),
            re.compile(r'\b\d+\s*[-–]\s*\d+\s*years?\b', re.IGNORECASE),
            re.compile(r'\b\d+\+?\s*years?\b', re.IGNORECASE),

            # Months experience
            re.compile(r'\b\d+[-+]?\s*(?:to\s+\d+\s*)?months?\s*(?:of\s*)?(?:experience|exp)\b', re.IGNORECASE),

            # Contract duration
            re.compile(r'\b(?:\d+\s*(?:month|year)s?\s*contract|contract\s*(?:for\s*)?\d+\s*(?:month|year)s?)\b', re.IGNORECASE),
        ]

        # Email pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        )

        # URL patterns
        self.url_patterns = [
            re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE),
            re.compile(r'www\.[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE),
        ]

        # Phone number patterns (multiple formats)
        self.phone_patterns = [
            # (XXX) XXX-XXXX, XXX-XXX-XXXX
            re.compile(r'\b\(\d{3}\)\s*\d{3}[-\s]?\d{4}\b'),
            re.compile(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b'),

            # International: +1-XXX-XXX-XXXX, +84-XXX-XXX-XXXX
            re.compile(r'\+\d{1,3}[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,9}'),

            # Vietnamese phone: 0901234567, (+84) 901234567
            re.compile(r'(?:\+84|0)\d{9,10}\b'),
        ]

        # Salary patterns
        self.salary_patterns = [
            # $50,000 - $70,000, $50K-70K, 50-70k USD
            re.compile(r'\$\d{1,3}(?:,\d{3})*(?:\s*[-–]\s*\$?\d{1,3}(?:,\d{3})*)?(?:\s*(?:USD|usd|per\s*year|annually|pa))?', re.IGNORECASE),
            re.compile(r'\$\d{1,3}[kK](?:\s*[-–]\s*\$?\d{1,3}[kK])?', re.IGNORECASE),
            re.compile(r'\b\d{1,3}[kK]?\s*[-–]\s*\d{1,3}[kK]?\s*(?:USD|usd|dollars?|per\s*year|annually)\b', re.IGNORECASE),

            # Vietnamese currency: 10-15 triệu VND, 10tr-15tr
            re.compile(r'\b\d{1,3}(?:\s*[-–]\s*\d{1,3})?\s*(?:triệu|tr|million)\s*(?:VND|vnd|đồng)?\b', re.IGNORECASE),

            # Hourly rates: $25/hour, $15-25 per hour
            re.compile(r'\$\d{1,3}(?:\s*[-–]\s*\$?\d{1,3})?\s*(?:per\s*hour|/hour|/hr|hourly)', re.IGNORECASE),
        ]

        # Work arrangement patterns
        self.work_arrangement_patterns = [
            re.compile(r'\b(?:remote|work\s*from\s*home|wfh|telecommute|telework)\b', re.IGNORECASE),
            re.compile(r'\b(?:hybrid|flexible|mixed)\b', re.IGNORECASE),
            re.compile(r'\b(?:on-site|onsite|office|in-person)\b', re.IGNORECASE),
            re.compile(r'\b(?:full-time|fulltime|full\s*time|ft)\b', re.IGNORECASE),
            re.compile(r'\b(?:part-time|parttime|part\s*time|pt)\b', re.IGNORECASE),
            re.compile(r'\b(?:contract|contractor|freelance|temporary|temp)\b', re.IGNORECASE),
        ]

        # Education level patterns
        self.education_patterns = [
            re.compile(r'\b(?:bachelor\'?s?|ba|bs|undergraduate)\s*(?:degree)?\b', re.IGNORECASE),
            re.compile(r'\b(?:master\'?s?|ma|ms|mba|graduate)\s*(?:degree)?\b', re.IGNORECASE),
            re.compile(r'\b(?:phd|ph\.d|doctorate|doctoral)\s*(?:degree)?\b', re.IGNORECASE),
            re.compile(r'\b(?:associate\'?s?|aa|as)\s*(?:degree)?\b', re.IGNORECASE),
            re.compile(r'\b(?:high\s*school|diploma|ged)\b', re.IGNORECASE),
        ]

    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract all information from text."""
        results = {}

        if self.extract_dates:
            results['dates'] = self.extract_dates_info(text)

        if self.extract_emails:
            results['emails'] = self.extract_emails_info(text)

        if self.extract_urls:
            results['urls'] = self.extract_urls_info(text)

        if self.extract_phone:
            results['phone_numbers'] = self.extract_phone_numbers(text)

        if self.extract_salary:
            results['salaries'] = self.extract_salary_info(text)

        if self.extract_work_arrangement:
            results['work_arrangements'] = self.extract_work_arrangements(text)

        # Additional extractions
        results['durations'] = self.extract_durations(text)
        results['education_levels'] = self.extract_education_levels(text)

        return results

    def extract_dates_info(self, text: str) -> List[str]:
        """Extract date information."""
        dates = []
        for pattern in self.date_patterns:
            matches = pattern.findall(text)
            dates.extend(matches)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(dates))

    def extract_durations(self, text: str) -> List[str]:
        """Extract duration/experience requirements."""
        durations = []
        for pattern in self.duration_patterns:
            matches = pattern.findall(text)
            durations.extend(matches)

        return list(dict.fromkeys(durations))

    def extract_emails_info(self, text: str) -> List[str]:
        """Extract email addresses."""
        emails = self.email_pattern.findall(text)
        return list(dict.fromkeys(emails))

    def extract_urls_info(self, text: str) -> List[str]:
        """Extract URLs."""
        urls = []
        for pattern in self.url_patterns:
            matches = pattern.findall(text)
            urls.extend(matches)

        return list(dict.fromkeys(urls))

    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers."""
        phones = []
        for pattern in self.phone_patterns:
            matches = pattern.findall(text)
            phones.extend(matches)

        # Clean up phone numbers
        cleaned_phones = []
        for phone in phones:
            # Remove extra spaces and standardize format
            cleaned = re.sub(r'\s+', '-', phone.strip())
            cleaned_phones.append(cleaned)

        return list(dict.fromkeys(cleaned_phones))

    def extract_salary_info(self, text: str) -> List[str]:
        """Extract salary information."""
        salaries = []
        for pattern in self.salary_patterns:
            matches = pattern.findall(text)
            salaries.extend(matches)

        return list(dict.fromkeys(salaries))

    def extract_work_arrangements(self, text: str) -> List[str]:
        """Extract work arrangement information."""
        arrangements = []
        for pattern in self.work_arrangement_patterns:
            matches = pattern.findall(text)
            arrangements.extend(matches)

        return list(dict.fromkeys([arr.lower() for arr in arrangements]))

    def extract_education_levels(self, text: str) -> List[str]:
        """Extract education level requirements."""
        education = []
        for pattern in self.education_patterns:
            matches = pattern.findall(text)
            education.extend(matches)

        return list(dict.fromkeys([edu.lower() for edu in education]))

    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """Extract all contact information."""
        return {
            'emails': self.extract_emails_info(text),
            'phone_numbers': self.extract_phone_numbers(text),
            'urls': self.extract_urls_info(text)
        }

    def extract_requirements_section(self, text: str) -> Dict[str, Any]:
        """Extract structured requirements information."""
        # Look for requirements/qualifications section
        req_pattern = re.compile(
            r'(?:requirements?|qualifications?|skills?|must\s*have)\s*:?\s*\n(.*?)(?=\n(?:[A-Z][^:]*:|$))',
            re.IGNORECASE | re.DOTALL
        )

        match = req_pattern.search(text)
        if not match:
            return {}

        req_text = match.group(1)

        return {
            'raw_requirements': req_text.strip(),
            'durations': self.extract_durations(req_text),
            'education_levels': self.extract_education_levels(req_text),
            'work_arrangements': self.extract_work_arrangements(req_text)
        }

    def get_extraction_summary(self, results: Dict[str, List[str]]) -> Dict[str, int]:
        """Get summary statistics of extraction results."""
        summary = {}
        for key, value in results.items():
            if isinstance(value, list):
                summary[f"{key}_count"] = len(value)
            else:
                summary[key] = str(value)

        return summary
