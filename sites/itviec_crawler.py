from typing import List

from selenium.webdriver.common.by import By

from .base_site import BaseSiteCrawler, JobPosting


class ITviec_Crawler(BaseSiteCrawler):
    def __init__(self, *, headless: bool = True, max_pages: int = 1):
        super().__init__(
            base_url="https://itviec.com",
            headless=headless,
            max_pages=max_pages,
        )

    def build_search_url(self, keyword: str, location: str | None = None, **kwargs) -> str:
        # Example: https://itviec.com/it-jobs?query=data&location=ho-chi-minh
        params = []
        if keyword:
            params.append(f"query={keyword}")
        if location:
            params.append(f"location={location}")
        q = ("&".join(params)) if params else ""
        return f"{self.base_url}/it-jobs" + (f"?{q}" if q else "")

    def parse_job_cards(self) -> List[JobPosting]:
        driver = self.driver
        assert driver is not None

        jobs: List[JobPosting] = []
        cards = driver.find_elements(By.CSS_SELECTOR, "div.job, div.job-details, div#jobs div.job-info")
        for card in cards:
            try:
                title_el = card.find_element(By.CSS_SELECTOR, "a.title, a.job__title, h3 a")
                title = self._txt(title_el)
                url = title_el.get_attribute("href")
            except Exception:
                continue

            company = ""
            try:
                company_el = card.find_element(By.CSS_SELECTOR, "a.company, .company, .employer")
                company = self._txt(company_el)
            except Exception:
                pass

            loc = ""
            try:
                loc_el = card.find_element(By.CSS_SELECTOR, ".location, .cities, li.city")
                loc = self._txt(loc_el)
            except Exception:
                pass

            jobs.append(
                JobPosting(
                    title=title,
                    company=company or None,
                    location=loc or None,
                    url=url,
                    source="itviec",
                    raw={"card_html": card.get_attribute("outerHTML")},
                )
            )
        return jobs
