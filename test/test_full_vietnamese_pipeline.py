#!/usr/bin/env python3
"""Test complete NLP pipeline with Vietnamese keywords support."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.processing.processor import JobDescriptionProcessor

def test_vietnamese_nlp_pipeline():
    """Test the complete NLP pipeline with Vietnamese content."""
    print("=== Testing Complete NLP Pipeline with Vietnamese Keywords ===")
    
    # Test job descriptions with Vietnamese content
    test_jobs = [
        {
            "title": "Senior Python Developer - Vietnamese Job",
            "description": """
            Tuyển dụng Senior Python Developer
            
            Yêu cầu:
            - 5+ năm kinh nghiệm lập trình Python
            - Thành thạo Django, Flask, FastAPI
            - Kinh nghiệm với cơ sở dữ liệu MySQL, PostgreSQL, MongoDB
            - Biết Machine Learning, AI (TensorFlow, PyTorch)
            - Kỹ năng giao tiếp tốt, làm việc nhóm hiệu quả
            - Tiếng Anh trung bình trở lên
            - Có khả năng giải quyết vấn đề phức tạp
            
            Quyền lợi:
            - Lương cạnh tranh: 25-40 triệu (thỏa thuận theo năng lực)
            - Bảo hiểm đầy đủ (BHXH, BHYT, BHTN)
            - Thưởng hiệu suất hàng quý
            - Đào tạo và phát triển kỹ năng
            - Môi trường trẻ, năng động
            - Nghỉ phép 12 ngày/năm + nghỉ lễ tết
            - Hỗ trợ làm việc từ xa (remote/hybrid)
            
            Hình thức làm việc: Toàn thời gian
            Địa điểm: Hà Nội (có thể remote 2-3 ngày/tuần)
            """
        },
        {
            "title": "Junior Frontend Developer",
            "description": """
            Looking for a Junior Frontend Developer to join our team.
            
            Requirements:
            - 1-2 years experience in web development
            - Strong skills in JavaScript, React, Vue.js
            - Experience with HTML5, CSS3, SASS/SCSS
            - Knowledge of responsive design
            - Git version control
            - Good communication skills
            - Fresh graduates are welcome
            
            We offer:
            - Competitive salary
            - Health insurance
            - Performance bonus
            - Training opportunities
            - Modern office environment
            - Team building activities
            
            This is a full-time position with growth opportunities.
            """
        },
        {
            "title": "Data Scientist - AI/ML Position",
            "description": """
            Chuyên viên Khoa học Dữ liệu (Data Scientist)
            
            Mô tả công việc:
            - Phân tích dữ liệu lớn (Big Data) để đưa ra insights
            - Xây dựng và triển khai các mô hình Machine Learning
            - Phát triển hệ thống AI/Deep Learning
            - Sử dụng Python, R, SQL cho phân tích dữ liệu
            - Làm việc với các tools: Jupyter, Pandas, NumPy, Scikit-learn
            - Visualization với Tableau, Power BI
            
            Yêu cầu:
            - Tốt nghiệp đại học chuyên ngành IT, Toán, Thống kê
            - 3+ năm kinh nghiệm về Data Science/Analytics
            - Thành thạo Python, SQL, R
            - Hiểu biết về Machine Learning algorithms
            - Kinh nghiệm với Cloud platforms (AWS, Azure, GCP)
            - Kỹ năng thuyết trình và báo cáo
            
            Mức lương: Thỏa thuận (30-50 triệu)
            Địa điểm: TP.HCM + Remote hybrid
            """
        }
    ]
    
    # Initialize processor
    processor = JobDescriptionProcessor()
    
    for i, job in enumerate(test_jobs, 1):
        print(f"\n{'='*60}")
        print(f"Processing Job {i}: {job['title']}")
        print(f"{'='*60}")
        
        # Process the job description
        result = processor.process(job['description'])
        
        # Display processing results
        print(f"Processing time: {result.processing_time:.3f}s")
        print(f"Text length: {len(result.cleaned_text)} characters")
        
        # Show confidence scores
        print(f"\nConfidence Scores:")
        for key, value in result.confidence_scores.items():
            print(f"  {key}: {value}")
        
        # Show rule-based extractions
        if result.emails or result.urls or result.dates:
            print(f"\nRule-based Extractions:")
            if result.emails:
                print(f"  Emails: {result.emails}")
            if result.urls:
                print(f"  URLs: {result.urls}")
            if result.dates:
                print(f"  Dates: {result.dates}")
        
        # Show NER results
        if result.skills or result.technologies or result.roles:
            print(f"\nNER Extractions:")
            if result.skills:
                print(f"  Skills: {result.skills[:5]}")  # Show first 5
            if result.technologies:
                print(f"  Technologies: {result.technologies[:5]}")
            if result.roles:
                print(f"  Roles: {result.roles[:3]}")
        
        # Show matched skills and technologies
        if result.matched_skills or result.matched_technologies:
            print(f"\nKeyword Matching Results:")
            if result.matched_skills:
                skills_names = [skill.get('keyword', 'Unknown') for skill in result.matched_skills[:5]]
                print(f"  Matched Skills: {skills_names}")
            if result.matched_technologies:
                tech_names = [tech.get('keyword', 'Unknown') for tech in result.matched_technologies[:5]]
                print(f"  Matched Technologies: {tech_names}")
        
        # Show Vietnamese keywords (NEW!)
        if result.vietnamese_keywords:
            print(f"\nVietnamese Keywords:")
            vn_by_category = {}
            for keyword in result.vietnamese_keywords:
                category = keyword.get('category', 'Unknown')
                if category not in vn_by_category:
                    vn_by_category[category] = []
                vn_by_category[category].append(keyword.get('keyword', 'Unknown'))
            
            for category, keywords in vn_by_category.items():
                print(f"  {category}: {keywords[:3]}")  # Show first 3 per category
        
        # Show seniority levels (NEW!)
        if result.seniority_levels:
            print(f"\nSeniority Levels Detected:")
            seniority_names = [level.get('keyword', 'Unknown') for level in result.seniority_levels]
            print(f"  Levels: {seniority_names}")
        
        # Show extended technologies (NEW!)
        if result.extended_technologies:
            print(f"\nExtended Technologies:")
            extended_by_category = {}
            for tech in result.extended_technologies:
                category = tech.get('category', 'Unknown')
                if category not in extended_by_category:
                    extended_by_category[category] = []
                extended_by_category[category].append(tech.get('keyword', 'Unknown'))
            
            for category, techs in extended_by_category.items():
                print(f"  {category}: {techs[:3]}")  # Show first 3 per category
        
        # Summary statistics
        total_extractions = (len(result.skills) + len(result.technologies) + 
                           len(result.matched_skills) + len(result.matched_technologies) +
                           len(result.vietnamese_keywords) + len(result.extended_technologies))
        print(f"\nSummary: {total_extractions} total extractions")

def test_specific_keywords():
    """Test specific Vietnamese keyword detection."""
    print(f"\n{'='*60}")
    print("Testing Specific Vietnamese Keywords")
    print(f"{'='*60}")
    
    test_cases = [
        "Tuyển fresher lập trình Python với 0-1 năm kinh nghiệm",
        "Senior developer với 5+ years experience in machine learning",
        "Vị trí junior phát triển web, làm việc nhóm tốt",
        "Tech lead position - trưởng nhóm kỹ thuật cần 7+ năm kinh nghiệm",
        "Thực tập sinh IT, fresh graduate, môi trường trẻ năng động"
    ]
    
    processor = JobDescriptionProcessor()
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. Text: {text}")
        result = processor.process(text)
        
        # Show Vietnamese keywords found
        if result.vietnamese_keywords:
            vn_keywords = [kw.get('keyword', 'Unknown') for kw in result.vietnamese_keywords]
            print(f"   Vietnamese: {vn_keywords}")
        
        # Show seniority levels
        if result.seniority_levels:
            seniority = [level.get('keyword', 'Unknown') for level in result.seniority_levels]
            print(f"   Seniority: {seniority}")
        
        # Show extended technologies
        if result.extended_technologies:
            ext_tech = [tech.get('keyword', 'Unknown') for tech in result.extended_technologies[:3]]
            print(f"   Technologies: {ext_tech}")

if __name__ == "__main__":
    test_vietnamese_nlp_pipeline()
    test_specific_keywords()
    print(f"\n{'='*60}")
    print("All tests completed!")
    print(f"{'='*60}")
