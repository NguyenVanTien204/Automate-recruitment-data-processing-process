"""Chuẩn hóa, làm sạch dữ liệu job descriptions với NLP pipeline hoàn chỉnh.

Quy trình xử lý:
1. Preprocessing: Làm sạch text, chuẩn hóa
2. Rule-based extraction: Regex cho dates, emails, URLs
3. NER + Phrase extraction: SpaCy/BERT cho skills, roles, technologies
4. Keyword matching: So khớp với từ điển skills/technologies
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

from .preprocessor import TextPreprocessor
from .rule_extractor import RuleBasedExtractor
from .ner_extractor import NERExtractor
from .keyword_matcher import KeywordMatcher

logger = logging.getLogger(__name__)


@dataclass
class ProcessedJobInfo:
    """Kết quả xử lý chi tiết từ job description."""
    original_description: str
    cleaned_text: str

    # Rule-based extractions
    dates: List[str] = field(default_factory=list)
    durations: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    phone_numbers: List[str] = field(default_factory=list)

    # NER extractions
    skills: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    qualifications: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)

    # Keyword matching results
    matched_skills: List[Dict[str, Any]] = field(default_factory=list)
    matched_technologies: List[Dict[str, Any]] = field(default_factory=list)
    matched_soft_skills: List[Dict[str, Any]] = field(default_factory=list)
    matched_industry_terms: List[Dict[str, Any]] = field(default_factory=list)

    # Vietnamese and extended matching
    vietnamese_keywords: List[Dict[str, Any]] = field(default_factory=list)
    seniority_levels: List[Dict[str, Any]] = field(default_factory=list)
    extended_technologies: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    processing_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_description': self.original_description,
            'cleaned_text': self.cleaned_text,
            'dates': self.dates,
            'durations': self.durations,
            'emails': self.emails,
            'urls': self.urls,
            'phone_numbers': self.phone_numbers,
            'skills': self.skills,
            'roles': self.roles,
            'technologies': self.technologies,
            'responsibilities': self.responsibilities,
            'qualifications': self.qualifications,
            'benefits': self.benefits,
            'matched_skills': self.matched_skills,
            'matched_technologies': self.matched_technologies,
            'matched_soft_skills': self.matched_soft_skills,
            'matched_industry_terms': self.matched_industry_terms,
            'vietnamese_keywords': self.vietnamese_keywords,
            'seniority_levels': self.seniority_levels,
            'extended_technologies': self.extended_technologies,
            'confidence_scores': self.confidence_scores,
            'processing_time': self.processing_time,
            'timestamp': self.timestamp
        }


class JobDescriptionProcessor:
    """Main processor orchestrating the entire NLP pipeline."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

        # Initialize pipeline components
        self.preprocessor = TextPreprocessor(self.config.get('preprocessing', {}))
        self.rule_extractor = RuleBasedExtractor(self.config.get('rules', {}))
        self.ner_extractor = NERExtractor(self.config.get('ner', {}))
        self.keyword_matcher = KeywordMatcher(self.config.get('keywords', {}))

        logger.info("JobDescriptionProcessor initialized successfully")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            'preprocessing': {
                'remove_html': True,
                'normalize_whitespace': True,
                'remove_special_chars': False,
                'min_length': 10
            },
            'rules': {
                'extract_dates': True,
                'extract_emails': True,
                'extract_urls': True,
                'extract_phone': True
            },
            'ner': {
                'model_name': 'en_core_web_sm',
                'custom_entities': True,
                'confidence_threshold': 0.7
            },
            'keywords': {
                'skills_dict_path': 'data/skills_dictionary.json',
                'tech_dict_path': 'data/tech_dictionary.json',
                'fuzzy_matching': True,
                'similarity_threshold': 0.8
            }
        }

        if config_path:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load config from {config_path}: {e}")

        return default_config

    def process(self, description: str) -> ProcessedJobInfo:
        """Process a single job description through the complete pipeline."""
        start_time = datetime.now()

        try:
            # Step 1: Preprocessing
            logger.debug("Starting preprocessing...")
            cleaned_text = self.preprocessor.clean(description)

            # Step 2: Rule-based extraction
            logger.debug("Starting rule-based extraction...")
            rule_results = self.rule_extractor.extract(cleaned_text)

            # Step 3: NER extraction
            logger.debug("Starting NER extraction...")
            ner_results = self.ner_extractor.extract(cleaned_text)

            # Step 4: Keyword matching
            logger.debug("Starting keyword matching...")
            keyword_results = self.keyword_matcher.match(cleaned_text)

            # Combine results
            result = ProcessedJobInfo(
                original_description=description,
                cleaned_text=cleaned_text,

                # Rule-based
                dates=rule_results.get('dates', []),
                durations=rule_results.get('durations', []),
                emails=rule_results.get('emails', []),
                urls=rule_results.get('urls', []),
                phone_numbers=rule_results.get('phone_numbers', []),

                # NER
                skills=ner_results.get('skills', []),
                roles=ner_results.get('roles', []),
                technologies=ner_results.get('technologies', []),
                responsibilities=ner_results.get('responsibilities', []),
                qualifications=ner_results.get('qualifications', []),
                benefits=ner_results.get('benefits', []),

                # Keywords
                matched_skills=keyword_results.get('skills', []),
                matched_technologies=keyword_results.get('technologies', []),
                matched_soft_skills=keyword_results.get('soft_skills', []),
                matched_industry_terms=keyword_results.get('industry_terms', []),

                # Vietnamese and extended matching
                vietnamese_keywords=keyword_results.get('vietnamese_keywords', []),
                seniority_levels=keyword_results.get('seniority_levels', []),
                extended_technologies=keyword_results.get('extended_technologies', []),

                # Metadata
                confidence_scores={
                    'ner_confidence': ner_results.get('confidence', 0.0),
                    'keyword_confidence': keyword_results.get('confidence', 0.0),
                    'total_matches': keyword_results.get('total_matches', 0)
                },
                processing_time=(datetime.now() - start_time).total_seconds()
            )

            logger.info(f"Successfully processed job description in {result.processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Error processing job description: {e}")
            return ProcessedJobInfo(
                original_description=description,
                cleaned_text="",
                processing_time=(datetime.now() - start_time).total_seconds()
            )

    def process_batch(self, descriptions: List[str]) -> List[ProcessedJobInfo]:
        """Process multiple job descriptions."""
        results = []
        for i, desc in enumerate(descriptions):
            logger.info(f"Processing job description {i+1}/{len(descriptions)}")
            result = self.process(desc)
            results.append(result)
        return results
