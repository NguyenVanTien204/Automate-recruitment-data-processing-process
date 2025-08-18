#!/usr/bin/env python3
"""Check Vietnamese keywords statistics."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.storage import JobStorage

def main():
    storage = JobStorage()
    
    # Check jobs with vietnamese_keywords field
    jobs_with_vn_field = list(storage.db.jobs.find({'vietnamese_keywords': {'$exists': True}}).limit(5))
    print(f"Found {len(jobs_with_vn_field)} jobs with vietnamese_keywords field")
    
    for job in jobs_with_vn_field:
        vn_count = len(job.get('vietnamese_keywords', []))
        seniority_count = len(job.get('seniority_levels', []))
        print(f"  {job['title'][:40]}... - VN:{vn_count}, Seniority:{seniority_count}")
    
    # Count jobs with non-empty vietnamese_keywords
    count_non_empty = storage.db.jobs.count_documents({
        'vietnamese_keywords': {'$exists': True, '$not': {'$size': 0}}
    })
    print(f"\nJobs with non-empty Vietnamese keywords: {count_non_empty}")
    
    # Show sample Vietnamese keywords
    if jobs_with_vn_field:
        job = jobs_with_vn_field[0]
        vn_keywords = job.get('vietnamese_keywords', [])
        print(f"\nSample Vietnamese keywords from '{job['title']}':")
        for kw in vn_keywords[:5]:
            print(f"  - {kw.get('keyword', 'Unknown')} (category: {kw.get('category', 'Unknown')})")

if __name__ == "__main__":
    main()
