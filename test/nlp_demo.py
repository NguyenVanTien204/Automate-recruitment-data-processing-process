"""
Example script demonstrating the NLP pipeline for job description processing.

This script shows how to:
1. Initialize the JobDescriptionProcessor
2. Process a sample job description
3. Extract and display various types of information
"""

import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.processing.processor import JobDescriptionProcessor

def main():
    print("=== Job Description NLP Pipeline Demo ===\n")

    # Sample job description (typical LinkedIn job posting)
    sample_description = """
    Senior Data Scientist - Machine Learning Engineer

    We are looking for a Senior Data Scientist with 5+ years of experience to join our AI team.

    Responsibilities:
    • Develop and implement machine learning models using Python, TensorFlow, and PyTorch
    • Collaborate with cross-functional teams to deliver data-driven solutions
    • Design and build scalable data pipelines using AWS and Docker
    • Perform statistical analysis and data visualization using pandas, matplotlib, and Tableau
    • Work with large datasets and big data technologies like Spark and Hadoop
    • Participate in code reviews and maintain version control using Git

    Requirements:
    • Master's degree in Computer Science, Statistics, or related field
    • 5+ years of experience in machine learning and data science
    • Proficiency in Python, SQL, and R
    • Experience with cloud platforms (AWS, Azure, or GCP)
    • Knowledge of deep learning frameworks (TensorFlow, PyTorch, Keras)
    • Strong communication skills and team collaboration
    • Experience with Agile/Scrum methodologies

    Benefits:
    • Competitive salary $120,000 - $150,000 per year
    • Remote work opportunity with flexible hours
    • Health insurance and dental coverage
    • Professional development budget

    Apply at: careers@company.com or visit our website www.company.com/careers
    Contact: (555) 123-4567

    Posted: January 15, 2024
    Location: San Francisco, CA (Remote OK)
    """

    try:
        # Initialize the processor
        print("1. Initializing NLP Processor...")
        config_path = project_root / "core" / "processing" / "config.json"
        processor = JobDescriptionProcessor(str(config_path) if config_path.exists() else None)
        print("✓ Processor initialized successfully\n")

        # Process the job description
        print("2. Processing job description...")
        result = processor.process(sample_description)
        print(f"✓ Processing completed in {result.processing_time:.2f} seconds\n")

        # Display results
        print("3. EXTRACTION RESULTS:")
        print("=" * 50)

        # Rule-based extractions
        print("\n📅 DATES & DURATIONS:")
        if result.dates:
            print(f"  Dates: {', '.join(result.dates)}")
        if result.durations:
            print(f"  Durations: {', '.join(result.durations)}")

        print("\n📧 CONTACT INFORMATION:")
        if result.emails:
            print(f"  Emails: {', '.join(result.emails)}")
        if result.phone_numbers:
            print(f"  Phone: {', '.join(result.phone_numbers)}")
        if result.urls:
            print(f"  URLs: {', '.join(result.urls)}")

        # NER extractions
        print("\n🔧 TECHNICAL SKILLS:")
        if result.skills:
            print(f"  Skills: {', '.join(result.skills[:10])}")  # Limit to 10
        if result.technologies:
            print(f"  Technologies: {', '.join(result.technologies[:10])}")

        print("\n💼 ROLES & RESPONSIBILITIES:")
        if result.roles:
            print(f"  Roles: {', '.join(result.roles)}")
        if result.responsibilities:
            print(f"  Responsibilities: {', '.join(result.responsibilities[:5])}")

        print("\n🎓 QUALIFICATIONS & BENEFITS:")
        if result.qualifications:
            print(f"  Qualifications: {', '.join(result.qualifications[:5])}")
        if result.benefits:
            print(f"  Benefits: {', '.join(result.benefits[:5])}")

        # Keyword matching results
        print("\n🔍 KEYWORD MATCHES:")
        if result.matched_skills:
            print("  Top Skills:")
            for skill in result.matched_skills[:5]:
                print(f"    • {skill.get('keyword', 'N/A')} (score: {skill.get('score', 0):.2f})")

        if result.matched_technologies:
            print("  Top Technologies:")
            for tech in result.matched_technologies[:5]:
                print(f"    • {tech.get('keyword', 'N/A')} (score: {tech.get('score', 0):.2f})")

        # Confidence scores
        print("\n📊 CONFIDENCE SCORES:")
        for metric, score in result.confidence_scores.items():
            print(f"  {metric}: {score:.2f}")

        # Save results to file (optional)
        output_path = project_root / "data" / "sample_output.json"
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {output_path}")

        # Summary statistics
        print("\n📈 SUMMARY STATISTICS:")
        total_extractions = (
            len(result.skills) + len(result.technologies) + len(result.roles) +
            len(result.responsibilities) + len(result.qualifications) +
            len(result.emails) + len(result.urls) + len(result.phone_numbers)
        )
        print(f"  Total extractions: {total_extractions}")
        print(f"  Processing time: {result.processing_time:.2f}s")
        print(f"  Original text length: {len(sample_description)} characters")
        print(f"  Cleaned text length: {len(result.cleaned_text)} characters")

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

def test_batch_processing():
    """Test batch processing with multiple job descriptions."""
    print("\n=== BATCH PROCESSING TEST ===\n")

    # Sample job descriptions
    job_descriptions = [
        "Software Engineer position requiring Python, React, and AWS experience. 3+ years required.",
        "Data Analyst role with SQL, Tableau, and Excel skills. Bachelor's degree preferred.",
        "Product Manager opening for SaaS company. Agile/Scrum experience needed. MBA preferred."
    ]

    try:
        processor = JobDescriptionProcessor()
        results = processor.process_batch(job_descriptions)

        print(f"✓ Processed {len(results)} job descriptions")

        for i, result in enumerate(results, 1):
            print(f"\nJob {i}:")
            print(f"  Skills: {len(result.skills)}")
            print(f"  Technologies: {len(result.technologies)}")
            print(f"  Processing time: {result.processing_time:.2f}s")

    except Exception as e:
        print(f"❌ Batch processing error: {e}")

if __name__ == "__main__":
    main()
    test_batch_processing()
