from typing import List

from selenium.webdriver.common.by import By

from .base_site import BaseSiteCrawler, JobPosting


class TopCV_Crawler(BaseSiteCrawler):
    def __init__(self, *, headless: bool = True, max_pages: int = 1):
        super().__init__(
            base_url="https://www.topcv.vn",
            headless=headless,
            max_pages=max_pages,
        )

    def build_search_url(self, keyword: str, location: str | None = None, **kwargs) -> str:
        # Example: https://www.topcv.vn/tim-viec-lam?keyword=data&province=ho-chi-minh
        params = []
        if keyword:
            params.append(f"keyword={keyword}")
        if location:
            params.append(f"province={location}")
        q = ("&".join(params)) if params else ""
        return f"{self.base_url}/tim-viec-lam" + (f"?{q}" if q else "")

    def parse_job_cards(self) -> List[JobPosting]:
        driver = self.driver
        assert driver is not None

        jobs: List[JobPosting] = []
        cards = driver.find_elements(By.CSS_SELECTOR, "div.job-item-default, div.box-job, .job-list .job-item")
        for card in cards:
            try:
                title_el = card.find_element(By.CSS_SELECTOR, "h3 a, .title a")
                title = self._txt(title_el)
                url = title_el.get_attribute("href")
            except Exception:
                continue

            company = None
            try:
                company_el = card.find_element(By.CSS_SELECTOR, ".company, .company-name a, .company-name")
                company = self._txt(company_el) or None
            except Exception:
                pass

            loc = None
            try:
                loc_el = card.find_element(By.CSS_SELECTOR, ".address, .job-address, .job-location")
                loc = self._txt(loc_el) or None
            except Exception:
                pass

            salary = None
            try:
                sal_el = card.find_element(By.CSS_SELECTOR, ".salary, .job-salary")
                salary = self._txt(sal_el) or None
            except Exception:
                pass

            jobs.append(
                JobPosting(
                    title=title,
                    company=company,
                    location=loc,
                    url=url,
                    salary=salary,
                    source="topcv",
                    raw={"card_html": card.get_attribute("outerHTML")},
                )
            )
        return jobs
