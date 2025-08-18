"""Named Entity Recognition and phrase extraction for job descriptions.

Uses SpaCy for:
- Skills extraction
- Role/position identification
- Technology detection
- Responsibility parsing
- Qualification extraction
"""

import logging
from typing import Dict, List, Any, Set, Tuple
import re

# Try to import spaCy, fallback gracefully if not available
try:
    import spacy
    from spacy.matcher import Matcher, PhraseMatcher
    from spacy.tokens import Doc, Span
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

logger = logging.getLogger(__name__)


class NERExtractor:
    """Extract entities and phrases using SpaCy NLP."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.model_name = self.config.get('model_name', 'en_core_web_sm')
        self.custom_entities = self.config.get('custom_entities', True)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)

        self.nlp = None
        self.matcher = None
        self.phrase_matcher = None

        if SPACY_AVAILABLE:
            self._load_model()
            self._setup_matchers()
        else:
            logger.warning("SpaCy not available. NER extraction will use fallback methods.")

    def _load_model(self):
        """Load SpaCy model."""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Loaded SpaCy model: {self.model_name}")
        except OSError:
            logger.warning(f"Could not load {self.model_name}. Trying en_core_web_sm...")
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded fallback model: en_core_web_sm")
            except OSError:
                logger.error("No SpaCy model available. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None

    def _setup_matchers(self):
        """Setup pattern matchers for job-specific entities."""
        if not self.nlp:
            return

        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        # Define patterns for different entity types
        self._setup_skill_patterns()
        self._setup_role_patterns()
        self._setup_tech_patterns()
        self._setup_responsibility_patterns()
        self._setup_qualification_patterns()

    def _setup_skill_patterns(self):
        """Setup patterns for skill detection."""
        # Programming skills patterns
        programming_patterns = [
            [{"LOWER": {"IN": ["python", "java", "javascript", "c++", "c#", "php", "ruby", "go", "rust", "swift"]}}],
            [{"LOWER": "machine"}, {"LOWER": "learning"}],
            [{"LOWER": "data"}, {"LOWER": "science"}],
            [{"LOWER": "artificial"}, {"LOWER": "intelligence"}],
            [{"LOWER": "deep"}, {"LOWER": "learning"}],
            [{"LOWER": "natural"}, {"LOWER": "language"}, {"LOWER": "processing"}],
            [{"LOWER": "computer"}, {"LOWER": "vision"}],
            [{"LOWER": "big"}, {"LOWER": "data"}],
            [{"LOWER": "data"}, {"LOWER": "analysis"}],
            [{"LOWER": "data"}, {"LOWER": "visualization"}]
        ]

        # Soft skills patterns
        soft_skill_patterns = [
            [{"LOWER": "problem"}, {"LOWER": "solving"}],
            [{"LOWER": "critical"}, {"LOWER": "thinking"}],
            [{"LOWER": "team"}, {"LOWER": "work"}],
            [{"LOWER": "communication"}, {"LOWER": "skills"}],
            [{"LOWER": "leadership"}],
            [{"LOWER": "project"}, {"LOWER": "management"}],
            [{"LOWER": "time"}, {"LOWER": "management"}]
        ]

        # Add patterns to matcher
        self.matcher.add("PROGRAMMING_SKILL", programming_patterns)
        self.matcher.add("SOFT_SKILL", soft_skill_patterns)

    def _setup_role_patterns(self):
        """Setup patterns for role/position detection."""
        role_patterns = [
            [{"LOWER": {"IN": ["developer", "engineer", "programmer", "architect", "analyst", "scientist"]}}],
            [{"LOWER": "software"}, {"LOWER": {"IN": ["developer", "engineer"]}}],
            [{"LOWER": "data"}, {"LOWER": {"IN": ["scientist", "engineer", "analyst"]}}],
            [{"LOWER": "machine"}, {"LOWER": "learning"}, {"LOWER": "engineer"}],
            [{"LOWER": "full"}, {"LOWER": "stack"}, {"LOWER": "developer"}],
            [{"LOWER": "frontend"}, {"LOWER": "developer"}],
            [{"LOWER": "backend"}, {"LOWER": "developer"}],
            [{"LOWER": "devops"}, {"LOWER": "engineer"}],
            [{"LOWER": "product"}, {"LOWER": "manager"}],
            [{"LOWER": "project"}, {"LOWER": "manager"}],
            [{"LOWER": "tech"}, {"LOWER": "lead"}],
            [{"LOWER": "team"}, {"LOWER": "lead"}]
        ]

        self.matcher.add("JOB_ROLE", role_patterns)

    def _setup_tech_patterns(self):
        """Setup patterns for technology detection."""
        tech_patterns = [
            # Frameworks
            [{"LOWER": {"IN": ["react", "angular", "vue", "django", "flask", "spring", "laravel", "express"]}}],
            [{"LOWER": "react"}, {"LOWER": "js"}],
            [{"LOWER": "node"}, {"LOWER": "js"}],
            [{"LOWER": "vue"}, {"LOWER": "js"}],

            # Databases
            [{"LOWER": {"IN": ["mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra"]}}],
            [{"LOWER": "sql"}, {"LOWER": "server"}],

            # Cloud platforms
            [{"LOWER": {"IN": ["aws", "azure", "gcp", "docker", "kubernetes"]}}],
            [{"LOWER": "amazon"}, {"LOWER": "web"}, {"LOWER": "services"}],
            [{"LOWER": "google"}, {"LOWER": "cloud"}, {"LOWER": "platform"}],

            # Tools
            [{"LOWER": {"IN": ["git", "jenkins", "jira", "confluence", "slack", "tableau", "powerbi"]}}],
        ]

        self.matcher.add("TECHNOLOGY", tech_patterns)

    def _setup_responsibility_patterns(self):
        """Setup patterns for responsibility detection."""
        responsibility_patterns = [
            [{"LOWER": {"IN": ["develop", "design", "implement", "maintain", "create", "build"]}}],
            [{"LOWER": "work"}, {"LOWER": "with"}],
            [{"LOWER": "collaborate"}, {"LOWER": "with"}],
            [{"LOWER": "responsible"}, {"LOWER": "for"}],
            [{"LOWER": "manage"}],
            [{"LOWER": "lead"}],
            [{"LOWER": "coordinate"}],
            [{"LOWER": "ensure"}],
            [{"LOWER": "support"}],
            [{"LOWER": "participate"}, {"LOWER": "in"}]
        ]

        self.matcher.add("RESPONSIBILITY", responsibility_patterns)

    def _setup_qualification_patterns(self):
        """Setup patterns for qualification detection."""
        qualification_patterns = [
            [{"LOWER": "bachelor"}, {"LOWER": "degree"}],
            [{"LOWER": "master"}, {"LOWER": "degree"}],
            [{"LOWER": "phd"}],
            [{"LOWER": {"IN": ["years", "year"]}}, {"LOWER": "experience"}],
            [{"LOWER": "experience"}, {"LOWER": "in"}],
            [{"LOWER": "knowledge"}, {"LOWER": "of"}],
            [{"LOWER": "familiar"}, {"LOWER": "with"}],
            [{"LOWER": "proficient"}, {"LOWER": "in"}],
            [{"LOWER": "expert"}, {"LOWER": "in"}],
        ]

        self.matcher.add("QUALIFICATION", qualification_patterns)

    def extract(self, text: str) -> Dict[str, Any]:
        """Extract entities from text using SpaCy."""
        if not SPACY_AVAILABLE or not self.nlp:
            return self._fallback_extraction(text)

        doc = self.nlp(text)

        results = {
            'skills': [],
            'roles': [],
            'technologies': [],
            'responsibilities': [],
            'qualifications': [],
            'benefits': [],
            'entities': [],
            'confidence': 0.0
        }

        # Extract named entities
        entities = self._extract_named_entities(doc)
        results['entities'] = entities

        # Extract using pattern matching
        matches = self.matcher(doc)
        pattern_results = self._process_pattern_matches(doc, matches)

        # Merge results
        for key in ['skills', 'roles', 'technologies', 'responsibilities', 'qualifications']:
            if key in pattern_results:
                results[key].extend(pattern_results[key])

        # Extract skills using multiple methods
        results['skills'].extend(self._extract_skills_contextual(doc))
        results['technologies'].extend(self._extract_technologies_contextual(doc))

        # Remove duplicates - only process lists that should contain strings
        string_lists = ['skills', 'roles', 'technologies', 'responsibilities', 'qualifications', 'benefits']
        for key in string_lists:
            if key in results and isinstance(results[key], list) and results[key]:
                # Only process if all items are strings
                if all(isinstance(item, str) for item in results[key]):
                    results[key] = list(dict.fromkeys(results[key]))

        # Calculate confidence score
        results['confidence'] = self._calculate_confidence(results)

        return results

    def _extract_named_entities(self, doc) -> List[Dict[str, Any]]:
        """Extract standard named entities."""
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': getattr(ent, 'confidence', 1.0)
            })
        return entities

    def _process_pattern_matches(self, doc, matches) -> Dict[str, List[str]]:
        """Process pattern matcher results."""
        results = {
            'skills': [],
            'roles': [],
            'technologies': [],
            'responsibilities': [],
            'qualifications': []
        }

        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            text = span.text.lower().strip()

            if label == "PROGRAMMING_SKILL" or label == "SOFT_SKILL":
                results['skills'].append(text)
            elif label == "JOB_ROLE":
                results['roles'].append(text)
            elif label == "TECHNOLOGY":
                results['technologies'].append(text)
            elif label == "RESPONSIBILITY":
                results['responsibilities'].append(text)
            elif label == "QUALIFICATION":
                results['qualifications'].append(text)

        return results

    def _extract_skills_contextual(self, doc) -> List[str]:
        """Extract skills using contextual analysis."""
        skills = []

        # Look for skills in context of "experience with", "knowledge of", etc.
        skill_contexts = ["experience with", "knowledge of", "proficient in", "skilled in", "expert in"]

        for sent in doc.sents:
            sent_text = sent.text.lower()
            for context in skill_contexts:
                if context in sent_text:
                    # Extract potential skills after the context
                    match = re.search(f"{context}\\s+([^.]+)", sent_text)
                    if match:
                        skill_text = match.group(1).strip()
                        # Clean and split skills
                        skill_items = [s.strip() for s in re.split(r'[,;]|\\band\\b', skill_text) if s.strip()]
                        # Filter out very short or common words
                        valid_skills = [skill for skill in skill_items
                                      if len(skill) > 2 and skill not in ['and', 'or', 'the', 'of', 'in', 'to', 'for']]
                        skills.extend(valid_skills[:3])  # Limit to 3 skills per context

        return skills

    def _extract_technologies_contextual(self, doc) -> List[str]:
        """Extract technologies using contextual analysis."""
        technologies = []

        # Common technology keywords
        tech_keywords = [
            'framework', 'library', 'database', 'platform', 'tool', 'technology',
            'stack', 'environment', 'system', 'software'
        ]

        for token in doc:
            if (token.text.lower() in tech_keywords and
                token.head.pos_ in ['NOUN', 'PROPN'] and
                token.head.text.lower() not in tech_keywords and
                len(token.head.text) > 2):  # Filter short words
                tech_name = token.head.text.lower()
                # Additional filtering for common words
                if tech_name not in ['team', 'work', 'job', 'role', 'data', 'big', 'new', 'good', 'best']:
                    technologies.append(tech_name)

        return technologies

    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate overall confidence score based on extraction results."""
        total_extractions = sum(len(v) for k, v in results.items()
                              if isinstance(v, list) and k != 'entities')

        if total_extractions == 0:
            return 0.0

        # Higher confidence for more diverse extractions
        extraction_types = sum(1 for k, v in results.items()
                             if isinstance(v, list) and len(v) > 0 and k != 'entities')

        base_confidence = min(total_extractions / 10.0, 1.0)  # Max 1.0
        diversity_bonus = extraction_types / 6.0  # 6 main categories

        return min(base_confidence + diversity_bonus * 0.2, 1.0)

    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction when SpaCy is not available."""
        logger.warning("Using fallback extraction methods")

        # Simple keyword-based extraction
        skills = self._fallback_skill_extraction(text)
        technologies = self._fallback_tech_extraction(text)
        roles = self._fallback_role_extraction(text)

        return {
            'skills': skills,
            'roles': roles,
            'technologies': technologies,
            'responsibilities': [],
            'qualifications': [],
            'benefits': [],
            'entities': [],
            'confidence': 0.5  # Lower confidence for fallback
        }

    def _fallback_skill_extraction(self, text: str) -> List[str]:
        """Simple keyword-based skill extraction."""
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue',
            'machine learning', 'data science', 'sql', 'git', 'docker',
            'aws', 'azure', 'kubernetes', 'teamwork', 'leadership',
            'communication', 'problem solving'
        ]

        found_skills = []
        text_lower = text.lower()

        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill)

        return found_skills

    def _fallback_tech_extraction(self, text: str) -> List[str]:
        """Simple keyword-based technology extraction."""
        tech_keywords = [
            'react', 'angular', 'vue', 'django', 'flask', 'spring',
            'mysql', 'postgresql', 'mongodb', 'redis', 'docker',
            'kubernetes', 'aws', 'azure', 'git', 'jenkins'
        ]

        found_tech = []
        text_lower = text.lower()

        for tech in tech_keywords:
            if tech in text_lower:
                found_tech.append(tech)

        return found_tech

    def _fallback_role_extraction(self, text: str) -> List[str]:
        """Simple keyword-based role extraction."""
        role_keywords = [
            'developer', 'engineer', 'analyst', 'scientist', 'manager',
            'architect', 'lead', 'senior', 'junior', 'intern'
        ]

        found_roles = []
        text_lower = text.lower()

        for role in role_keywords:
            if role in text_lower:
                found_roles.append(role)

        return found_roles
