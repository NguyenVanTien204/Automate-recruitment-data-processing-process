#!/usr/bin/env python3
"""Test script for Vietnamese keywords and seniority level detection."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.processing.keyword_matcher import KeywordMatcher

def test_vietnamese_keywords():
    """Test Vietnamese keyword detection."""
    print("=== Testing Vietnamese Keywords ===")
    
    # Test descriptions with Vietnamese content
    test_descriptions = [
        # Vietnamese job description
        """
        Tuyển dụng lập trình viên Python junior
        Yêu cầu:
        - 1-2 năm kinh nghiệm
        - Biết Python, Django, MySQL
        - Kỹ năng giao tiếp tốt
        - Làm việc nhóm hiệu quả
        - Tiếng Anh cơ bản
        
        Quyền lợi:
        - Lương cạnh tranh
        - Bảo hiểm đầy đủ
        - Thưởng hiệu suất
        - Đào tạo chuyên sâu
        - Môi trường trẻ, năng động
        """,
        
        # Mixed Vietnamese-English
        """
        Senior Developer Position
        We are looking for a senior lập trình viên with experience in:
        - Python programming (5+ years kinh nghiệm)
        - Machine learning và trí tuệ nhân tạo
        - Phát triển web với Django/Flask
        - Cơ sở dữ liệu MySQL, PostgreSQL
        - Làm việc nhóm và kỹ năng giao tiếp
        
        Benefits:
        - Competitive lương cạnh tranh
        - Full bảo hiểm
        - Performance thưởng
        - Remote work options
        """,
        
        # Seniority levels test
        """
        Multiple positions available:
        - Fresher Developer (0-1 year)
        - Junior Software Engineer (1-3 years) 
        - Mid-level/Intermediate Developer (3-5 years)
        - Senior Engineer (5+ years)
        - Tech Lead/Team Leader
        - Engineering Manager
        - Solution Architect
        
        Requirements vary by seniority level.
        Fresh graduates welcome for entry level positions.
        Experienced professionals for senior roles.
        """,
        
        # Vietnamese benefits and requirements
        """
        Vị trí: Full-stack Developer
        Loại hình: Toàn thời gian, có thể remote
        
        Yêu cầu:
        - Tốt nghiệp đại học ngành IT
        - 2+ năm kinh nghiệm phát triển web
        - Thành thạo JavaScript, React, Node.js
        - Kiến thức về cơ sở dữ liệu
        - Giải quyết vấn đề tốt
        
        Quyền lợi:
        - Mức lương hấp dẫn (thỏa thuận)
        - Nghỉ phép 12 ngày/năm
        - Đào tạo và phát triển kỹ năng
        - Team building, du lịch công ty
        """
    ]
    
    # Initialize keyword matcher
    matcher = KeywordMatcher()
    
    for i, description in enumerate(test_descriptions, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Description preview: {description[:100]}...")
        
        results = matcher.match(description)
        
        print(f"Total matches: {results['total_matches']}")
        print(f"Confidence: {results['confidence']:.2f}")
        
        # Print Vietnamese keywords found
        if results['vietnamese_keywords']:
            print("\nVietnamese Keywords Found:")
            for match in results['vietnamese_keywords']:
                print(f"  - {match['keyword']} (category: {match.get('category', 'N/A')}, confidence: {match.get('confidence', 0):.2f})")
        
        # Print seniority levels
        if results['seniority_levels']:
            print("\nSeniority Levels Found:")
            for match in results['seniority_levels']:
                print(f"  - {match['keyword']} (category: {match.get('category', 'N/A')})")
        
        # Print extended technologies
        if results['extended_technologies']:
            print("\nExtended Technologies Found:")
            for match in results['extended_technologies'][:5]:  # Show first 5
                print(f"  - {match['keyword']} (category: {match.get('category', 'N/A')})")
            if len(results['extended_technologies']) > 5:
                print(f"  ... and {len(results['extended_technologies']) - 5} more")
        
        # Print regular skills
        if results['skills']:
            print("\nRegular Skills Found:")
            for match in results['skills'][:3]:  # Show first 3
                print(f"  - {match['keyword']} (category: {match.get('category', 'N/A')})")

def test_seniority_detection():
    """Test seniority level detection specifically."""
    print("\n\n=== Testing Seniority Level Detection ===")
    
    test_cases = [
        "Looking for a junior developer with 1-2 years experience",
        "Senior Python engineer position available", 
        "Fresh graduate internship program",
        "We need a tech lead for our team",
        "Engineering manager role - 7+ years experience",
        "Entry level position for new graduates",
        "Mid-level developer with 3-5 years experience",
        "Solution architect opportunity",
        "Nhân viên lập trình junior",
        "Chuyên viên phát triển phần mềm senior", 
        "Trưởng nhóm kỹ thuật",
        "Thực tập sinh IT"
    ]
    
    matcher = KeywordMatcher()
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. Text: {text}")
        results = matcher.match(text)
        
        # Look for seniority in Vietnamese keywords
        seniority_found = []
        if results['vietnamese_keywords']:
            for match in results['vietnamese_keywords']:
                if 'level' in match.get('category', '') or any(level in match['keyword'].lower() 
                    for level in ['junior', 'senior', 'fresh', 'lead', 'manager', 'architect']):
                    seniority_found.append(match)
        
        # Also check regular matches for seniority terms
        all_matches = results['skills'] + results['technologies'] + results['industry_terms']
        for match in all_matches:
            if any(level in match['keyword'].lower() 
                   for level in ['junior', 'senior', 'fresh', 'lead', 'manager', 'architect']):
                seniority_found.append(match)
        
        if seniority_found:
            print(f"   Seniority detected: {[m['keyword'] for m in seniority_found]}")
        else:
            print("   No seniority level detected")

if __name__ == "__main__":
    test_vietnamese_keywords()
    test_seniority_detection()
    print("\n=== Test completed ===")
