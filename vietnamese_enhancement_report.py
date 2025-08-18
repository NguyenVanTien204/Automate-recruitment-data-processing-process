#!/usr/bin/env python3
"""Vietnamese Keywords Enhancement - Final Report."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.storage import JobStorage

def generate_final_report():
    print("="*80)
    print("           VIETNAMESE KEYWORDS ENHANCEMENT - FINAL REPORT")
    print("="*80)

    storage = JobStorage()

    # Overall statistics
    total_linkedin_jobs = storage.db.jobs.count_documents({'source': 'linkedin'})
    processed_jobs = storage.db.jobs.count_documents({'vietnamese_analysis_completed': True})
    jobs_with_vn = storage.db.jobs.count_documents({
        'vietnamese_keywords': {'$exists': True, '$not': {'$size': 0}}
    })

    print(f"\n📊 OVERVIEW STATISTICS")
    print(f"Total LinkedIn jobs: {total_linkedin_jobs}")
    print(f"Jobs processed with Vietnamese analysis: {processed_jobs}")
    print(f"Jobs containing Vietnamese keywords: {jobs_with_vn}")
    print(f"Coverage: {(processed_jobs/total_linkedin_jobs*100):.1f}%")
    print(f"Vietnamese content detection rate: {(jobs_with_vn/processed_jobs*100):.1f}%")

    # Get detailed analysis
    vn_jobs = list(storage.db.jobs.find({
        'vietnamese_keywords': {'$exists': True, '$not': {'$size': 0}}
    }))

    if not vn_jobs:
        print("\nNo jobs with Vietnamese keywords found.")
        return

    # Analyze seniority levels
    seniority_counts = {}
    for job in vn_jobs:
        for seniority in job.get('seniority_levels', []):
            keyword = seniority.get('keyword', 'Unknown')
            seniority_counts[keyword] = seniority_counts.get(keyword, 0) + 1

    print(f"\n🎯 SENIORITY LEVELS DETECTED")
    print("-" * 50)
    for keyword, count in sorted(seniority_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / jobs_with_vn * 100)
        print(f"{keyword:<15} │ {count:>3} jobs │ {percentage:>5.1f}%")

    # Analyze Vietnamese categories
    vn_categories = {}
    all_vn_keywords = {}

    for job in vn_jobs:
        for vn_kw in job.get('vietnamese_keywords', []):
            category = vn_kw.get('category', 'Unknown')
            keyword = vn_kw.get('keyword', 'Unknown')

            vn_categories[category] = vn_categories.get(category, 0) + 1

            if category not in all_vn_keywords:
                all_vn_keywords[category] = {}
            all_vn_keywords[category][keyword] = all_vn_keywords[category].get(keyword, 0) + 1

    print(f"\n🇻🇳 VIETNAMESE KEYWORDS BY CATEGORY")
    print("-" * 50)
    for category, count in sorted(vn_categories.items(), key=lambda x: x[1], reverse=True):
        print(f"{category:<30} │ {count:>3} mentions")

        # Show top keywords in each category
        if category in all_vn_keywords:
            top_keywords = sorted(all_vn_keywords[category].items(),
                                key=lambda x: x[1], reverse=True)[:3]
            for keyword, kw_count in top_keywords:
                print(f"  └─ {keyword:<25} │ {kw_count:>3} jobs")

    # Extended technologies analysis
    tech_jobs = list(storage.db.jobs.find({
        'extended_technologies': {'$exists': True, '$not': {'$size': 0}}
    }))

    tech_categories = {}
    for job in tech_jobs:
        for tech in job.get('extended_technologies', []):
            category = tech.get('category', 'Unknown')
            tech_categories[category] = tech_categories.get(category, 0) + 1

    print(f"\n💻 EXTENDED TECHNOLOGY CATEGORIES")
    print("-" * 50)
    print(f"Jobs with extended tech info: {len(tech_jobs)}")
    for category, count in sorted(tech_categories.items(), key=lambda x: x[1], reverse=True)[:8]:
        print(f"{category:<30} │ {count:>3} mentions")

    # Sample job analysis
    print(f"\n📝 SAMPLE ANALYSIS")
    print("-" * 50)

    sample_jobs = vn_jobs[:3]
    for i, job in enumerate(sample_jobs, 1):
        print(f"\n{i}. {job['title']}")
        print(f"   Company: {job.get('company', 'Unknown')}")

        vn_keywords = [kw['keyword'] for kw in job.get('vietnamese_keywords', [])]
        seniority = [s['keyword'] for s in job.get('seniority_levels', [])]
        ext_tech = [t['keyword'] for t in job.get('extended_technologies', [])]

        print(f"   Vietnamese: {vn_keywords[:4]}")
        print(f"   Seniority: {seniority}")
        print(f"   Technologies: {ext_tech[:5]}")

    # Success metrics
    print(f"\n✅ SUCCESS METRICS")
    print("-" * 50)

    # Calculate success rates
    jobs_with_seniority = storage.db.jobs.count_documents({
        'seniority_levels': {'$exists': True, '$not': {'$size': 0}}
    })

    jobs_with_extended_tech = storage.db.jobs.count_documents({
        'extended_technologies': {'$exists': True, '$not': {'$size': 0}}
    })

    print(f"Seniority detection rate: {(jobs_with_seniority/processed_jobs*100):.1f}%")
    print(f"Extended tech detection rate: {(jobs_with_extended_tech/processed_jobs*100):.1f}%")
    print(f"Vietnamese content detection: {(jobs_with_vn/processed_jobs*100):.1f}%")

    # New features summary
    print(f"\n🚀 NEW FEATURES IMPLEMENTED")
    print("-" * 50)
    print("✓ Vietnamese keyword detection (seniority, skills, benefits, requirements)")
    print("✓ Seniority level extraction (junior, senior, lead, manager, etc.)")
    print("✓ Extended technology dictionary (programming languages, frameworks, tools)")
    print("✓ Enhanced NLP pipeline with multilingual support")
    print("✓ Comprehensive MongoDB integration")
    print("✓ Statistical analysis and reporting")

    print(f"\n🎉 VIETNAMESE KEYWORDS ENHANCEMENT COMPLETED SUCCESSFULLY!")
    print("="*80)

if __name__ == "__main__":
    generate_final_report()
