from typing import List, Optional
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from .base_site import BaseSiteCrawler, JobPosting


from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions

class Linkedin_Crawler(BaseSiteCrawler):
    def __init__(self, *, headless: bool = False, max_pages: int = 1,
                 pause: float = 1.5, scroll_pause: float = 1.0,
                 profile_dir: Optional[str] = None,
                 user_data_dir: Optional[str] = None):
        """
        profile_dir: thư mục profile Edge (ví dụ: "Default" hoặc "Profile 1")
        user_data_dir: thư mục user data (ví dụ: C:\\Users\\<USERNAME>\\AppData\\Local\\Microsoft\\Edge\\User Data)
        """
        super().__init__(
            base_url="https://www.linkedin.com/jobs",
            headless=headless,
            max_pages=max_pages,
            pause=pause,
        )
        self.scroll_pause = scroll_pause
        self.profile_dir = profile_dir
        self.user_data_dir = user_data_dir

    def _build_driver(self):
        """Khởi tạo Edge driver với profile (để giữ đăng nhập)."""
        opts = EdgeOptions()
        opts.use_chromium = True
        if self.headless:
            opts.add_argument("--headless=new")
        if self.user_data_dir:
            opts.add_argument(f"user-data-dir={self.user_data_dir}")
        if self.profile_dir:
            opts.add_argument(f"profile-directory={self.profile_dir}")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")

        service = EdgeService("msedgedriver.exe")
        return webdriver.Edge(service=service, options=opts)

    def build_search_url(self, keyword: str, location: Optional[str] = None, **kwargs) -> str:
        params = []
        if keyword:
            params.append(f"keywords={keyword}")
        if location:
            params.append(f"location={location}")
        q = ("&".join(params)) if params else ""
        return f"{self.base_url}/search/" + (f"?{q}" if q else "")

    def _infinite_scroll(self, limit: int) -> None:
        """Scroll trang để load thêm job cards (LinkedIn lazy load)."""
        driver = self.driver
        assert driver is not None

        last_height = driver.execute_script("return document.body.scrollHeight")
        collected = 0
        while collected < limit:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(self.scroll_pause + random.uniform(0.2, 0.8))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # hết job để load
                break
            last_height = new_height
            # đếm số job hiện có
            collected = len(driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li"))

    def parse_job_cards(self) -> List[JobPosting]:
        driver = self.driver
        assert driver is not None

        # Scroll để load đủ job
        self._infinite_scroll(limit=50)

        jobs: List[JobPosting] = []
        cards = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li")
        for card in cards:
            try:
                title_el = card.find_element(By.CSS_SELECTOR, "a.job-card-list__title, a[href*='/jobs/view/']")
                title = self._txt(title_el)
                url = title_el.get_attribute("href")
            except Exception:
                continue

            company, loc, desc, posted_at = None, None, None, None

            # Công ty
            try:
                company_el = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name, .base-search-card__subtitle a, .job-card-list__subtitle a")
                company = self._txt(company_el) or None
            except Exception:
                pass

            # Địa điểm
            try:
                loc_el = card.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-item, .job-search-card__location")
                loc = self._txt(loc_el) or None
            except Exception:
                pass

            # --- NEW: mở card để lấy mô tả chi tiết ---
            try:
                driver.execute_script("arguments[0].click();", title_el)
                time.sleep(self.pause + random.uniform(0.5, 1.2))

                # Panel bên phải chứa chi tiết job
                desc_el = driver.find_element(By.CSS_SELECTOR, ".jobs-description__content, .show-more-less-html__markup")
                desc = self._txt(desc_el)

                try:
                    posted_el = driver.find_element(By.CSS_SELECTOR, ".jobs-unified-top-card__posted-date")
                    posted_at = self._txt(posted_el) or None
                except Exception:
                    pass
            except Exception:
                pass

            jobs.append(
                JobPosting(
                    title=title,
                    company=company,
                    location=loc,
                    url=url,
                    source="linkedin",
                    posted_at=posted_at,
                    description=desc,
                    raw={"card_html": card.get_attribute("outerHTML")},
                )
            )
        return jobs
