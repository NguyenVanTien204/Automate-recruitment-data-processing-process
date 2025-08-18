#!/usr/bin/env python3
"""Batch update all LinkedIn jobs with Vietnamese keywords."""

import sys
from pathlib import Path

# Add project root to path

from core.processing.processor import JobDescriptionProcessor
from core.storage import JobStorage
import time

def batch_update_vietnamese():
    print("=== Batch Update Vietnamese Keywords ===")

    processor = JobDescriptionProcessor()
    storage = JobStorage()

    # Get all LinkedIn jobs that haven't been processed for Vietnamese yet
    all_jobs = list(storage.db.jobs.find({
        'source': 'linkedin',
        'vietnamese_keywords': {'$exists': False}
    }))

    print(f"Found {len(all_jobs)} LinkedIn jobs to process")

    if not all_jobs:
        print("All jobs already processed!")
        return

    success_count = 0

    for i, job in enumerate(all_jobs, 1):
        print(f"\nProcessing {i}/{len(all_jobs)}: {job['title'][:50]}...")

        try:
            description = job.get('description', '')
            if len(description.strip()) < 20:
                print("  Skipping - description too short")
                continue

            # Process with NLP
            result = processor.process(description)

            # Update job
            update_data = {
                'vietnamese_keywords': result.vietnamese_keywords,
                'seniority_levels': result.seniority_levels,
                'extended_technologies': result.extended_technologies,
                'matched_soft_skills': result.matched_soft_skills,
                'matched_industry_terms': result.matched_industry_terms,
                'vietnamese_analysis_completed': True,
                'vietnamese_analysis_timestamp': result.timestamp
            }

            storage.db.jobs.update_one(
                {'_id': job['_id']},
                {'$set': update_data}
            )

            success_count += 1

            # Show summary
            vn_count = len(result.vietnamese_keywords)
            seniority_count = len(result.seniority_levels)
            ext_tech_count = len(result.extended_technologies)

            print(f"  ✓ VN:{vn_count}, Seniority:{seniority_count}, ExtTech:{ext_tech_count}")

            if result.vietnamese_keywords:
                keywords = [kw['keyword'] for kw in result.vietnamese_keywords[:3]]
                print(f"    Keywords: {keywords}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

    print(f"\n=== Batch Update Complete ===")
    print(f"Successfully updated: {success_count}/{len(all_jobs)} jobs")

def show_final_statistics():
    print(f"\n=== Final Vietnamese Keywords Statistics ===")

    storage = JobStorage()

    # Count processed jobs
    processed_count = storage.db.jobs.count_documents({
        'vietnamese_analysis_completed': True
    })
    print(f"Total processed jobs: {processed_count}")

    # Jobs with Vietnamese keywords
    vn_jobs = list(storage.db.jobs.find({
        'vietnamese_keywords': {'$exists': True, '$not': {'$size': 0}}
    }))
    print(f"Jobs with Vietnamese keywords: {len(vn_jobs)}")

    # Seniority statistics
    seniority_stats = {}
    vn_category_stats = {}

    for job in vn_jobs:
        # Count seniority levels
        for seniority in job.get('seniority_levels', []):
            keyword = seniority.get('keyword', 'unknown')
            seniority_stats[keyword] = seniority_stats.get(keyword, 0) + 1

        # Count Vietnamese categories
        for vn_kw in job.get('vietnamese_keywords', []):
            category = vn_kw.get('category', 'unknown')
            vn_category_stats[category] = vn_category_stats.get(category, 0) + 1

    print(f"\nSeniority Levels Distribution:")
    for keyword, count in sorted(seniority_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {keyword}: {count} jobs")

    print(f"\nVietnamese Keywords by Category:")
    for category, count in sorted(vn_category_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count} mentions")

    # Show sample jobs
    print(f"\nSample jobs with Vietnamese content:")
    for i, job in enumerate(vn_jobs[:3], 1):
        vn_keywords = [kw['keyword'] for kw in job.get('vietnamese_keywords', [])]
        seniority = [s['keyword'] for s in job.get('seniority_levels', [])]
        print(f"  {i}. {job['title'][:40]}...")
        print(f"     VN: {vn_keywords[:3]}")
        print(f"     Seniority: {seniority}")

if __name__ == "__main__":
    batch_update_vietnamese()
    show_final_statistics()
