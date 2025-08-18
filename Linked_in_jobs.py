from sites.linkedin_crawler import Linkedin_Crawler
from core.storage import JobStorage
CRAWLER_CONFIG = {
    "headless": False,          # có hiện cửa sổ Chrome không
    "max_pages": 1,            # số trang (LinkedIn thường =1, dùng scroll)
    "pause": 2.0,              # delay sau mỗi action
    "scroll_pause": 1.5,       # delay giữa các lần scroll
    "limit": 50,               # giảm về 1 để test debug
    "keyword": "data analyst",  # thay đổi keyword để tìm job có nhiều applicants hơn
    "location": "Vietnam",
    "LINKEDIN_USER_DATA_DIR": "C:\\Users\\Admin\\AppData\\Local\\Microsoft\\Edge\\User Data",
    "LINKEDIN_PROFILE": "Default"
}

if __name__ == "__main__":
    crawler = Linkedin_Crawler(
        headless=CRAWLER_CONFIG["headless"],
        max_pages=CRAWLER_CONFIG["max_pages"],
        pause=CRAWLER_CONFIG["pause"],
        scroll_pause=CRAWLER_CONFIG["scroll_pause"],
        profile_dir=CRAWLER_CONFIG["LINKEDIN_PROFILE"],
        user_data_dir=CRAWLER_CONFIG["LINKEDIN_USER_DATA_DIR"],

    )

    try:
        jobs = crawler.run(
            keyword=CRAWLER_CONFIG["keyword"],
            location=CRAWLER_CONFIG["location"],
            limit=CRAWLER_CONFIG["limit"],
        )
        storage = JobStorage()
        storage.save_jobs(jobs)
    finally:
        crawler.close()
