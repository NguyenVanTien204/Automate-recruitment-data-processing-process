"""Keyword matching module for job descriptions.

Matches tokens against predefined dictionaries of:
- Technical skills
- Programming languages
- Tools and frameworks
- Soft skills
- Industry terms
"""

import json
import logging
from typing import Dict, List, Any, Set, Optional
from pathlib import Path
import re

# Try to import optional dependencies
try:
    from fuzzywuzzy import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

logger = logging.getLogger(__name__)


class KeywordMatcher:
    """Match keywords against predefined dictionaries with fuzzy matching support."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.fuzzy_matching = self.config.get('fuzzy_matching', True) and FUZZY_AVAILABLE
        self.similarity_threshold = self.config.get('similarity_threshold', 0.8)

        # Load dictionaries
        self.skills_dict = self._load_dictionary('skills')
        self.tech_dict = self._load_dictionary('technologies')
        self.soft_skills_dict = self._load_dictionary('soft_skills')
        self.industry_terms_dict = self._load_dictionary('industry_terms')

        # Compile patterns for better performance
        self._compile_patterns()

        if not FUZZY_AVAILABLE and self.config.get('fuzzy_matching', False):
            logger.warning("fuzzywuzzy not available. Install with: pip install fuzzywuzzy python-levenshtein")

    def _load_dictionary(self, dict_type: str) -> Dict[str, Any]:
        """Load dictionary from config or use defaults."""
        config_key = f"{dict_type}_dict_path"
        dict_path = self.config.get(config_key)

        if dict_path and Path(dict_path).exists():
            try:
                with open(dict_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load {dict_type} dictionary from {dict_path}: {e}")

        # Return default dictionaries
        return self._get_default_dictionary(dict_type)

    def _get_default_dictionary(self, dict_type: str) -> Dict[str, Any]:
        """Get default dictionaries for different types."""

        if dict_type == 'skills':
            return {
                'programming_languages': {
                    'python': {'category': 'programming', 'weight': 1.0, 'aliases': ['py']},
                    'java': {'category': 'programming', 'weight': 1.0, 'aliases': []},
                    'javascript': {'category': 'programming', 'weight': 1.0, 'aliases': ['js', 'node.js', 'nodejs']},
                    'typescript': {'category': 'programming', 'weight': 1.0, 'aliases': ['ts']},
                    'c++': {'category': 'programming', 'weight': 1.0, 'aliases': ['cpp', 'c plus plus']},
                    'c#': {'category': 'programming', 'weight': 1.0, 'aliases': ['csharp', 'c sharp']},
                    'php': {'category': 'programming', 'weight': 1.0, 'aliases': []},
                    'ruby': {'category': 'programming', 'weight': 1.0, 'aliases': []},
                    'go': {'category': 'programming', 'weight': 1.0, 'aliases': ['golang']},
                    'rust': {'category': 'programming', 'weight': 1.0, 'aliases': []},
                    'swift': {'category': 'programming', 'weight': 1.0, 'aliases': []},
                    'kotlin': {'category': 'programming', 'weight': 1.0, 'aliases': []},
                    'scala': {'category': 'programming', 'weight': 1.0, 'aliases': []},
                    'r': {'category': 'programming', 'weight': 1.0, 'aliases': []},
                    'matlab': {'category': 'programming', 'weight': 1.0, 'aliases': []},
                    'sql': {'category': 'database', 'weight': 1.0, 'aliases': ['structured query language']}
                },
                'data_science': {
                    'machine learning': {'category': 'ai', 'weight': 1.0, 'aliases': ['ml', 'machinelearning']},
                    'deep learning': {'category': 'ai', 'weight': 1.0, 'aliases': ['dl', 'neural networks']},
                    'artificial intelligence': {'category': 'ai', 'weight': 1.0, 'aliases': ['ai']},
                    'natural language processing': {'category': 'ai', 'weight': 1.0, 'aliases': ['nlp']},
                    'computer vision': {'category': 'ai', 'weight': 1.0, 'aliases': ['cv']},
                    'data analysis': {'category': 'analysis', 'weight': 1.0, 'aliases': ['data analytics']},
                    'statistics': {'category': 'analysis', 'weight': 1.0, 'aliases': ['statistical analysis']},
                    'big data': {'category': 'data', 'weight': 1.0, 'aliases': []},
                    'data mining': {'category': 'data', 'weight': 1.0, 'aliases': []},
                    'predictive modeling': {'category': 'modeling', 'weight': 1.0, 'aliases': []}
                }
            }

        elif dict_type == 'technologies':
            return {
                'frameworks': {
                    'react': {'category': 'frontend', 'weight': 1.0, 'aliases': ['reactjs', 'react.js']},
                    'angular': {'category': 'frontend', 'weight': 1.0, 'aliases': ['angularjs']},
                    'vue': {'category': 'frontend', 'weight': 1.0, 'aliases': ['vuejs', 'vue.js']},
                    'django': {'category': 'backend', 'weight': 1.0, 'aliases': []},
                    'flask': {'category': 'backend', 'weight': 1.0, 'aliases': []},
                    'spring': {'category': 'backend', 'weight': 1.0, 'aliases': ['spring boot']},
                    'express': {'category': 'backend', 'weight': 1.0, 'aliases': ['expressjs', 'express.js']},
                    'laravel': {'category': 'backend', 'weight': 1.0, 'aliases': []},
                    'rails': {'category': 'backend', 'weight': 1.0, 'aliases': ['ruby on rails']}
                },
                'databases': {
                    'mysql': {'category': 'database', 'weight': 1.0, 'aliases': []},
                    'postgresql': {'category': 'database', 'weight': 1.0, 'aliases': ['postgres']},
                    'mongodb': {'category': 'database', 'weight': 1.0, 'aliases': ['mongo']},
                    'redis': {'category': 'database', 'weight': 1.0, 'aliases': []},
                    'elasticsearch': {'category': 'database', 'weight': 1.0, 'aliases': ['elastic search']},
                    'cassandra': {'category': 'database', 'weight': 1.0, 'aliases': []},
                    'oracle': {'category': 'database', 'weight': 1.0, 'aliases': []},
                    'sqlite': {'category': 'database', 'weight': 1.0, 'aliases': []}
                },
                'cloud_platforms': {
                    'aws': {'category': 'cloud', 'weight': 1.0, 'aliases': ['amazon web services']},
                    'azure': {'category': 'cloud', 'weight': 1.0, 'aliases': ['microsoft azure']},
                    'gcp': {'category': 'cloud', 'weight': 1.0, 'aliases': ['google cloud platform', 'google cloud']},
                    'docker': {'category': 'containerization', 'weight': 1.0, 'aliases': []},
                    'kubernetes': {'category': 'containerization', 'weight': 1.0, 'aliases': ['k8s']},
                    'terraform': {'category': 'infrastructure', 'weight': 1.0, 'aliases': []}
                }
            }

        elif dict_type == 'soft_skills':
            return {
                'leadership': {'category': 'management', 'weight': 1.0, 'aliases': ['team leadership']},
                'communication': {'category': 'interpersonal', 'weight': 1.0, 'aliases': ['communication skills']},
                'teamwork': {'category': 'interpersonal', 'weight': 1.0, 'aliases': ['team work', 'collaboration']},
                'problem solving': {'category': 'analytical', 'weight': 1.0, 'aliases': ['problem-solving']},
                'critical thinking': {'category': 'analytical', 'weight': 1.0, 'aliases': []},
                'project management': {'category': 'management', 'weight': 1.0, 'aliases': []},
                'time management': {'category': 'organization', 'weight': 1.0, 'aliases': []},
                'adaptability': {'category': 'personal', 'weight': 1.0, 'aliases': ['flexibility']},
                'creativity': {'category': 'personal', 'weight': 1.0, 'aliases': ['innovative thinking']},
                'analytical thinking': {'category': 'analytical', 'weight': 1.0, 'aliases': []}
            }

        elif dict_type == 'industry_terms':
            return {
                'methodologies': {
                    'agile': {'category': 'methodology', 'weight': 1.0, 'aliases': ['agile development']},
                    'scrum': {'category': 'methodology', 'weight': 1.0, 'aliases': []},
                    'kanban': {'category': 'methodology', 'weight': 1.0, 'aliases': []},
                    'waterfall': {'category': 'methodology', 'weight': 1.0, 'aliases': []},
                    'devops': {'category': 'methodology', 'weight': 1.0, 'aliases': ['dev ops']},
                    'ci/cd': {'category': 'methodology', 'weight': 1.0, 'aliases': ['continuous integration', 'continuous deployment']}
                },
                'roles': {
                    'full stack developer': {'category': 'role', 'weight': 1.0, 'aliases': ['fullstack developer']},
                    'frontend developer': {'category': 'role', 'weight': 1.0, 'aliases': ['front-end developer']},
                    'backend developer': {'category': 'role', 'weight': 1.0, 'aliases': ['back-end developer']},
                    'data scientist': {'category': 'role', 'weight': 1.0, 'aliases': []},
                    'machine learning engineer': {'category': 'role', 'weight': 1.0, 'aliases': ['ml engineer']},
                    'devops engineer': {'category': 'role', 'weight': 1.0, 'aliases': []},
                    'product manager': {'category': 'role', 'weight': 1.0, 'aliases': ['pm']},
                    'software architect': {'category': 'role', 'weight': 1.0, 'aliases': []}
                }
            }

        return {}

    def _compile_patterns(self):
        """Compile regex patterns for better matching performance."""
        # Create a combined pattern for all keywords
        all_keywords = set()

        for dict_data in [self.skills_dict, self.tech_dict, self.soft_skills_dict, self.industry_terms_dict]:
            for category_data in dict_data.values():
                if isinstance(category_data, dict):
                    all_keywords.update(category_data.keys())
                    # Add aliases
                    for item_data in category_data.values():
                        if isinstance(item_data, dict) and 'aliases' in item_data:
                            all_keywords.update(item_data['aliases'])

        # Sort by length (longest first) for better matching
        self.all_keywords = sorted(all_keywords, key=len, reverse=True)

        # Create pattern for word boundaries
        self.word_boundary_pattern = re.compile(r'\b[\w\s\-\+\.]+\b', re.IGNORECASE)

    def match(self, text: str) -> Dict[str, Any]:
        """Match keywords in text against all dictionaries."""
        # Clean and normalize text
        normalized_text = self._normalize_text(text)

        results = {
            'skills': [],
            'technologies': [],
            'soft_skills': [],
            'industry_terms': [],
            'confidence': 0.0,
            'total_matches': 0
        }

        # Match against each dictionary
        skills_matches = self._match_against_dictionary(normalized_text, self.skills_dict, 'skills')
        tech_matches = self._match_against_dictionary(normalized_text, self.tech_dict, 'technologies')
        soft_skills_matches = self._match_against_dictionary(normalized_text, self.soft_skills_dict, 'soft_skills')
        industry_matches = self._match_against_dictionary(normalized_text, self.industry_terms_dict, 'industry_terms')

        results['skills'] = skills_matches
        results['technologies'] = tech_matches
        results['soft_skills'] = soft_skills_matches
        results['industry_terms'] = industry_matches

        # Calculate statistics
        total_matches = sum(len(matches) for matches in [skills_matches, tech_matches, soft_skills_matches, industry_matches])
        results['total_matches'] = total_matches
        results['confidence'] = self._calculate_confidence(results)

        return results

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching."""
        # Convert to lowercase
        text = text.lower()

        # Replace common separators with spaces
        text = re.sub(r'[/\-_\.]', ' ', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _match_against_dictionary(self, text: str, dictionary: Dict[str, Any], dict_type: str) -> List[Dict[str, Any]]:
        """Match text against a specific dictionary."""
        matches = []

        for category_name, category_data in dictionary.items():
            if not isinstance(category_data, dict):
                continue

            for keyword, keyword_data in category_data.items():
                # Direct match
                if self._is_keyword_in_text(keyword, text):
                    match = self._create_match_result(keyword, keyword_data, 1.0, 'exact', category_name)
                    matches.append(match)
                    continue

                # Check aliases
                if isinstance(keyword_data, dict) and 'aliases' in keyword_data:
                    for alias in keyword_data['aliases']:
                        if self._is_keyword_in_text(alias, text):
                            match = self._create_match_result(keyword, keyword_data, 0.9, 'alias', category_name, alias)
                            matches.append(match)
                            break

                # Fuzzy matching if enabled
                if self.fuzzy_matching:
                    fuzzy_score = self._fuzzy_match(keyword, text)
                    if fuzzy_score >= self.similarity_threshold:
                        match = self._create_match_result(keyword, keyword_data, fuzzy_score, 'fuzzy', category_name)
                        matches.append(match)

        # Remove duplicates and sort by score
        unique_matches = {match['keyword']: match for match in matches}
        return sorted(unique_matches.values(), key=lambda x: x['score'], reverse=True)

    def _is_keyword_in_text(self, keyword: str, text: str) -> bool:
        """Check if keyword exists in text with word boundaries."""
        # Escape special regex characters in keyword
        escaped_keyword = re.escape(keyword)
        pattern = rf'\\b{escaped_keyword}\\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _fuzzy_match(self, keyword: str, text: str) -> float:
        """Perform fuzzy matching between keyword and text."""
        if not FUZZY_AVAILABLE:
            return 0.0

        # Extract potential matches from text
        words = text.split()

        # Single word keyword
        if ' ' not in keyword:
            best_match = process.extractOne(keyword, words, scorer=fuzz.ratio)
            return (best_match[1] / 100.0) if best_match and best_match[1] >= (self.similarity_threshold * 100) else 0.0

        # Multi-word keyword - check against phrases
        phrases = []
        keyword_len = len(keyword.split())
        for i in range(len(words) - keyword_len + 1):
            phrase = ' '.join(words[i:i + keyword_len])
            phrases.append(phrase)

        if phrases:
            best_match = process.extractOne(keyword, phrases, scorer=fuzz.ratio)
            return (best_match[1] / 100.0) if best_match and best_match[1] >= (self.similarity_threshold * 100) else 0.0

        return 0.0

    def _create_match_result(self, keyword: str, keyword_data: Dict[str, Any], score: float,
                           match_type: str, category: str, matched_text: str = None) -> Dict[str, Any]:
        """Create a standardized match result."""
        return {
            'keyword': keyword,
            'matched_text': matched_text or keyword,
            'score': score,
            'match_type': match_type,
            'category': category,
            'weight': keyword_data.get('weight', 1.0) if isinstance(keyword_data, dict) else 1.0,
            'subcategory': keyword_data.get('category', '') if isinstance(keyword_data, dict) else ''
        }

    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate overall confidence score for keyword matching."""
        total_matches = results['total_matches']

        if total_matches == 0:
            return 0.0

        # Weight different types of matches
        weighted_score = 0.0
        total_weight = 0.0

        for match_list in [results['skills'], results['technologies'], results['soft_skills'], results['industry_terms']]:
            for match in match_list:
                score = match['score'] * match['weight']
                weighted_score += score
                total_weight += match['weight']

        if total_weight == 0:
            return 0.0

        # Normalize by total weight and apply diminishing returns
        confidence = weighted_score / total_weight

        # Apply bonus for diversity of matches
        match_categories = set()
        for match_list in [results['skills'], results['technologies'], results['soft_skills'], results['industry_terms']]:
            for match in match_list:
                match_categories.add(match['category'])

        diversity_bonus = min(len(match_categories) / 10.0, 0.2)  # Max 0.2 bonus

        return min(confidence + diversity_bonus, 1.0)

    def get_top_matches(self, results: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top matches across all categories."""
        all_matches = []

        for category in ['skills', 'technologies', 'soft_skills', 'industry_terms']:
            for match in results.get(category, []):
                match['match_category'] = category
                all_matches.append(match)

        # Sort by score and return top matches
        return sorted(all_matches, key=lambda x: x['score'], reverse=True)[:limit]
