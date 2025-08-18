from pymongo import MongoClient
import json

client = MongoClient('mongodb://localhost:27017/')
db = client['crawler']
collection = db['demo']

# Get a sample job with Vietnamese analysis
job = collection.find_one({'vietnamese_analysis_completed': True})

if job:
    print('Sample job structure:')
    print('Title:', job.get('title', 'N/A'))
    print('Company:', job.get('company', 'N/A'))
    print()
    print('Extracted structure:')
    extracted = job.get('extracted', {})
    print('- vietnamese_keywords:', len(extracted.get('vietnamese_keywords', [])))
    print('- seniority_levels:', len(extracted.get('seniority_levels', [])))
    print('- extended_technologies:', len(extracted.get('extended_technologies', [])))
    print('- skills:', len(extracted.get('skills', [])))
    print('- technologies:', len(extracted.get('technologies', [])))
    print()
    
    # Show sample Vietnamese keywords
    vn_keywords = extracted.get('vietnamese_keywords', [])[:3]
    print('Sample Vietnamese keywords:')
    for kw in vn_keywords:
        print(f'  - {kw.get("keyword", "N/A")} (category: {kw.get("category", "N/A")})')
        
    # Show sample seniority levels  
    seniority = extracted.get('seniority_levels', [])[:3]
    print('Sample Seniority levels:')
    for s in seniority:
        print(f'  - {s.get("keyword", "N/A")} (category: {s.get("category", "N/A")})')
        
    print()
    print('✅ Vietnamese keywords are now stored in extracted section alongside English data!')
else:
    print('No processed jobs found')
