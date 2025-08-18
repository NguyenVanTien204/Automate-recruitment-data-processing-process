#!/usr/bin/env python3
"""Quick test to verify Vietnamese keywords update."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.storage import JobStorage
from core.processing.processor import JobDescriptionProcessor

def test_update():
    storage = JobStorage()
    processor = JobDescriptionProcessor()
    
    # Get one job
    job = list(storage.db.jobs.find().limit(1))[0]
    print(f"Processing job: {job['title']}")
    
    # Process description  
    result = processor.process(job['description'])
    print(f"Vietnamese keywords found: {len(result.vietnamese_keywords)}")
    print(f"Sample Vietnamese keywords: {[kw['keyword'] for kw in result.vietnamese_keywords[:3]]}")
    
    # Update job
    update_data = {
        'vietnamese_keywords': result.vietnamese_keywords,
        'seniority_levels': result.seniority_levels,
        'test_field': 'test_value'
    }
    
    print(f"Updating job with fields: {list(update_data.keys())}")
    result_update = storage.db.jobs.update_one(
        {'_id': job['_id']},
        {'$set': update_data}
    )
    print(f"Update result: matched={result_update.matched_count}, modified={result_update.modified_count}")
    
    # Verify update
    updated_job = storage.db.jobs.find_one({'_id': job['_id']})
    print(f"Fields in updated job: {list(updated_job.keys())}")
    print(f"Vietnamese keywords in DB: {updated_job.get('vietnamese_keywords', 'NOT FOUND')}")

if __name__ == "__main__":
    test_update()
