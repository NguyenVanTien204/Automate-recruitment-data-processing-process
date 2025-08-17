import sys
from pathlib import Path

# Ensure project root (HR) is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sites.itviec_crawler import ITviec_Crawler
from sites.topcv_crawler import TopCV_Crawler
from sites.vietnamworks_crawler import VietnamWorks_Crawler
from sites.linkedin_crawler import Linkedin_Crawler


def smoke():
    crawlers = [
        ITviec_Crawler(headless=True),
        TopCV_Crawler(headless=True),
        VietnamWorks_Crawler(headless=True),
        Linkedin_Crawler(headless=True),
    ]
    for c in crawlers:
        print(f"Testing {c.__class__.__name__}")
        url = c.build_search_url("data", location="ho-chi-minh")
        print("  URL:", url)


if __name__ == "__main__":
    smoke()
