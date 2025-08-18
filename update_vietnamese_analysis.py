#!/usr/bin/env python3
"""Update LinkedIn jobs in MongoDB with Vietnamese keywords and seniority detection."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.processing.processor import JobDescriptionProcessor
from core.storage import JobStorage
import time

def update_linkedin_jobs_with_vietnamese():
    """Update existing LinkedIn jobs with Vietnamese keyword analysis."""
    print("=== Updating LinkedIn Jobs with Vietnamese Keywords ===")

    # Initialize components
    processor = JobDescriptionProcessor()
    storage = JobStorage()

    # Get all LinkedIn jobs
    print("Fetching LinkedIn jobs from MongoDB...")
    jobs = storage.get_jobs(source='linkedin', limit=100)  # Process first 100 jobs
    print(f"Found {len(jobs)} LinkedIn jobs to process")

    if not jobs:
        print("No LinkedIn jobs found in database")
        return

    processed_count = 0
    updated_count = 0

    # Process each job
    for i, job in enumerate(jobs, 1):
        print(f"\nProcessing job {i}/{len(jobs)}: {job.get('title', 'Untitled')[:50]}...")

        try:
            # Get job description
            description = job.get('description', '')
            if not description or len(description.strip()) < 20:
                print(f"  Skipping - empty or too short description")
                continue

            # Process with NLP pipeline
            start_time = time.time()
            result = processor.process(description)
            processing_time = time.time() - start_time

            # Prepare update data with Vietnamese fields
            update_data = {
                'vietnamese_keywords': result.vietnamese_keywords,
                'seniority_levels': result.seniority_levels,
                'extended_technologies': result.extended_technologies,
                'matched_soft_skills': result.matched_soft_skills,
                'matched_industry_terms': result.matched_industry_terms,
                'nlp_processing_enhanced': True,
                'vietnamese_analysis_date': result.timestamp,
                'enhanced_confidence_scores': result.confidence_scores
            }

            # Update the job in MongoDB
            storage.db.jobs.update_one(
                {'_id': job['_id']},
                {'$set': update_data}
            )

            processed_count += 1
            updated_count += 1

            # Show results summary
            vn_count = len(result.vietnamese_keywords)
            seniority_count = len(result.seniority_levels)
            tech_count = len(result.extended_technologies)

            print(f"  ✓ Updated - VN:{vn_count}, Seniority:{seniority_count}, Tech:{tech_count} ({processing_time:.2f}s)")

            # Show some Vietnamese keywords found
            if result.vietnamese_keywords:
                vn_keywords = [kw.get('keyword', 'Unknown') for kw in result.vietnamese_keywords[:3]]
                print(f"    Vietnamese: {vn_keywords}")

            if result.seniority_levels:
                seniority = [level.get('keyword', 'Unknown') for level in result.seniority_levels]
                print(f"    Seniority: {seniority}")

        except Exception as e:
            print(f"  ✗ Error processing job: {e}")
            continue

        # Small delay to avoid overwhelming the system
        if i % 10 == 0:
            print(f"\n--- Processed {i} jobs so far ---")
            time.sleep(0.5)

    print(f"\n=== Update Summary ===")
    print(f"Jobs processed: {processed_count}")
    print(f"Jobs updated: {updated_count}")
    print(f"Success rate: {(updated_count/len(jobs)*100):.1f}%")

def analyze_vietnamese_statistics():
    """Analyze Vietnamese keywords statistics from updated jobs."""
    print(f"\n=== Vietnamese Keywords Statistics ===")

    storage = JobStorage()

    # Get jobs with Vietnamese analysis
    pipeline = [
        {
            '$match': {
                'source': 'linkedin',
                'vietnamese_keywords': {'$exists': True, '$ne': []}
            }
        },
        {
            '$project': {
                'title': 1,
                'vietnamese_keywords': 1,
                'seniority_levels': 1,
                'extended_technologies': 1
            }
        }
    ]

    jobs_with_vn = list(storage.db.jobs.aggregate(pipeline))
    print(f"Jobs with Vietnamese keywords: {len(jobs_with_vn)}")

    if not jobs_with_vn:
        print("No jobs with Vietnamese keywords found")
        return

    # Count Vietnamese keywords by category
    vn_categories = {}
    seniority_counts = {}
    tech_categories = {}

    for job in jobs_with_vn:
        # Count Vietnamese keywords
        for vn_kw in job.get('vietnamese_keywords', []):
            category = vn_kw.get('category', 'Unknown')
            keyword = vn_kw.get('keyword', 'Unknown')

            if category not in vn_categories:
                vn_categories[category] = {}
            if keyword not in vn_categories[category]:
                vn_categories[category][keyword] = 0
            vn_categories[category][keyword] += 1

        # Count seniority levels
        for seniority in job.get('seniority_levels', []):
            keyword = seniority.get('keyword', 'Unknown')
            if keyword not in seniority_counts:
                seniority_counts[keyword] = 0
            seniority_counts[keyword] += 1

        # Count extended technologies by category
        for tech in job.get('extended_technologies', []):
            category = tech.get('category', 'Unknown')
            if category not in tech_categories:
                tech_categories[category] = 0
            tech_categories[category] += 1

    # Display statistics
    print(f"\nVietnamese Keywords by Category:")
    for category, keywords in sorted(vn_categories.items()):
        print(f"  {category}:")
        # Show top 3 keywords in each category
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:3]
        for keyword, count in sorted_keywords:
            print(f"    {keyword}: {count} jobs")

    print(f"\nSeniority Levels Distribution:")
    sorted_seniority = sorted(seniority_counts.items(), key=lambda x: x[1], reverse=True)
    for keyword, count in sorted_seniority:
        print(f"  {keyword}: {count} jobs")

    print(f"\nExtended Technology Categories:")
    sorted_tech_cats = sorted(tech_categories.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_tech_cats[:5]:  # Top 5 categories
        print(f"  {category}: {count} mentions")

def show_sample_vietnamese_jobs():
    """Show sample jobs with Vietnamese content."""
    print(f"\n=== Sample Jobs with Vietnamese Content ===")

    storage = JobStorage()

    # Find jobs with Vietnamese keywords
    jobs = storage.db.jobs.find({
        'source': 'linkedin',
        'vietnamese_keywords': {'$exists': True, '$ne': []},
        'seniority_levels': {'$exists': True, '$ne': []}
    }).limit(3)

    for i, job in enumerate(jobs, 1):
        print(f"\n--- Sample Job {i} ---")
        print(f"Title: {job.get('title', 'Untitled')}")
        print(f"Company: {job.get('company', 'Unknown')}")

        # Show Vietnamese keywords
        vn_keywords = [kw.get('keyword', 'Unknown') for kw in job.get('vietnamese_keywords', [])]
        print(f"Vietnamese Keywords: {vn_keywords[:5]}")

        # Show seniority
        seniority = [level.get('keyword', 'Unknown') for level in job.get('seniority_levels', [])]
        print(f"Seniority Levels: {seniority}")

        # Show description preview
        description = job.get('description', '')
        print(f"Description preview: {description[:150]}...")

if __name__ == "__main__":
    # Update jobs with Vietnamese analysis
    update_linkedin_jobs_with_vietnamese()

    # Analyze statistics
    analyze_vietnamese_statistics()

    # Show samples
    show_sample_vietnamese_jobs()

    print(f"\n=== Vietnamese Enhancement Complete! ===")
