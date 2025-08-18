from typing import List, Optional
import time
import random
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from .base_site import BaseSiteCrawler, JobPosting

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
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

    def _extract_full_description(self, driver) -> Optional[str]:
        """Trích xuất toàn bộ description của job, bao gồm việc click 'Show more' nếu cần."""
        try:
            # Đầu tiên, thử click vào nút "Show more" hoặc "See more" nếu có
            show_more_selectors = [
                ".show-more-less-html__button--more",
                ".jobs-description__footer button",
                "[data-test-job-description-footer-action='expand']",
                "button[aria-label*='Show more']",
                "button[aria-label*='See more']",
                ".artdeco-button--tertiary:contains('Show more')",
                ".show-more-less-html__button[aria-expanded='false']"
            ]

            for selector in show_more_selectors:
                try:
                    show_more_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if show_more_btn.is_displayed() and show_more_btn.is_enabled():
                        driver.execute_script("arguments[0].click();", show_more_btn)
                        print("DEBUG: Clicked 'Show more' button")
                        time.sleep(0.5)  # Chờ content load
                        break
                except Exception:
                    continue

            # Sau đó, lấy content từ nhiều selectors khác nhau
            description_selectors = [
                ".jobs-description__content",
                ".show-more-less-html__markup",
                ".jobs-description-content__text",
                ".job-details-jobs-unified-top-card__job-description",
                ".jobs-unified-top-card__job-description",
                ".jobs-description",
                ".description__text"
            ]

            descriptions = []

            for selector in description_selectors:
                try:
                    desc_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for desc_el in desc_elements:
                        if desc_el.is_displayed():
                            text = self._txt(desc_el)
                            if text and text.strip() and text not in descriptions:
                                descriptions.append(text.strip())
                except Exception:
                    continue

            # Nếu không tìm thấy từ các selectors chính, thử lấy từ toàn bộ job details panel
            if not descriptions:
                try:
                    job_panel_selectors = [
                        ".jobs-search__job-details--container",
                        ".scaffold-layout__detail"
                    ]

                    for panel_selector in job_panel_selectors:
                        panels = driver.find_elements(By.CSS_SELECTOR, panel_selector)
                        if panels:
                            panel = panels[0]
                            # Tìm tất cả các phần text trong panel
                            text_elements = panel.find_elements(By.CSS_SELECTOR, "p, div, span, li, h1, h2, h3, h4, h5, h6")
                            panel_texts = []
                            for elem in text_elements:
                                try:
                                    elem_text = self._txt(elem)
                                    if elem_text and len(elem_text.strip()) > 10:  # Chỉ lấy text có ý nghĩa
                                        parent_class = elem.get_attribute("class") or ""
                                        # Bỏ qua các elements không liên quan đến description
                                        if not any(skip in parent_class for skip in [
                                            "job-title", "company-name", "location", "metadata",
                                            "applicant", "posted", "nav", "button", "header"
                                        ]):
                                            panel_texts.append(elem_text.strip())
                                except Exception:
                                    continue

                            if panel_texts:
                                # Loại bỏ duplicate và kết hợp
                                unique_texts = []
                                for text in panel_texts:
                                    if text not in unique_texts and len(text) > 20:  # Text có ý nghĩa
                                        unique_texts.append(text)

                                if unique_texts:
                                    descriptions.extend(unique_texts[:5])  # Lấy tối đa 5 phần quan trọng nhất
                            break
                except Exception as e:
                    print(f"DEBUG: Error extracting from job panel: {e}")

            # Kết hợp tất cả descriptions
            if descriptions:
                # Loại bỏ các phần trùng lặp và kết hợp
                final_desc = "\n\n".join(descriptions)
                print(f"DEBUG: Extracted description length: {len(final_desc)} chars")
                return final_desc
            else:
                print("DEBUG: No description found")
                return None

        except Exception as e:
            print(f"DEBUG: Error in _extract_full_description: {e}")
            return None

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

    def parse_job_cards(self, limit: int = 3) -> List[JobPosting]:
        driver = self.driver
        assert driver is not None

        # Scroll để load đủ job
        self._infinite_scroll(limit=limit)

        jobs: List[JobPosting] = []
        cards = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li")

        for card in cards[:limit]:
            try:
                title_el = card.find_element(By.CSS_SELECTOR, "a.job-card-list__title, a[href*='/jobs/view/']")
                title = self._txt(title_el)
                url = title_el.get_attribute("href")
            except Exception:
                continue

            company, loc, desc, posted_at, applicants = None, None, None, None, None

            # Công ty
            try:
                company_el = card.find_element(
                    By.CSS_SELECTOR,
                    ".job-card-container__company-name, .base-search-card__subtitle a, .job-card-list__subtitle a"
                )
                company = self._txt(company_el) or None
            except Exception:
                pass

            # Địa điểm
            try:
                loc_el = card.find_element(
                    By.CSS_SELECTOR,
                    ".job-card-container__metadata-item, .job-search-card__location"
                )
                loc = self._txt(loc_el) or None
            except Exception:
                pass

            # Thông tin thời gian và applicants từ card (trước khi click)
            try:
                # Tìm text trong card chứa thông tin metadata
                card_text = (card.get_attribute("textContent") or "").strip()
                print(f"DEBUG: Card {cards.index(card)+1} text: {card_text[:200]}...")

                # Tách thành các dòng
                lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                print(f"DEBUG: Card lines: {lines}")

                # Thử tìm thông tin applicants từ các elements con trong card
                try:
                    # Tìm các span hoặc div có thể chứa thông tin applicants
                    applicant_elements = card.find_elements(By.CSS_SELECTOR, "span, div, li")
                    for elem in applicant_elements:
                        elem_text = (elem.get_attribute("textContent") or "").strip()
                        if elem_text:
                            elem_lower = elem_text.lower()
                            if "be an early applicant" in elem_lower:
                                applicants = 0
                                print(f"DEBUG: Found 'be an early applicant' in element: {elem_text}")
                                break
                            elif any(k in elem_lower for k in ["applicant", "people applied"]):
                                # Tìm số
                                m = re.search(r"(\d+)", elem_text)
                                if m:
                                    try:
                                        applicants = int(m.group(1))
                                        print(f"DEBUG: Found {applicants} applicants in element: {elem_text}")
                                        break
                                    except Exception:
                                        continue
                except Exception as e:
                    print(f"DEBUG: Error searching elements in card: {e}")

                # Parse posted_at từ card
                time_tokens = [
                    "ago", "posted", "reposted", "today", "yesterday",
                    "giờ trước", "phút trước", "ngày trước", "vừa xong", "hôm nay", "hôm qua",
                    "days ago", "hours ago", "minutes ago", "weeks ago", "months ago",
                    "hour ago", "day ago", "week ago", "month ago"
                ]
                for line in lines:
                    line_lower = line.lower()
                    if any(tk in line_lower for tk in time_tokens):
                        posted_at = line
                        print(f"DEBUG: Found posted_at in card: {posted_at}")
                        break

                # Parse applicants từ card lines nếu chưa tìm thấy
                if applicants is None:
                    applicant_tokens = [
                        "applicant", "applicants", "people applied", "people clicked apply",
                        "người đã nộp", "đã ứng tuyển", "early applicant", "be an early applicant"
                    ]

                    print(f"DEBUG: Looking for applicants in lines: {lines}")

                    for line in lines:
                        line_lower = line.lower().strip()
                        print(f"DEBUG: Checking line: '{line}' (lower: '{line_lower}')")

                        if any(k in line_lower for k in applicant_tokens):
                            print(f"DEBUG: Found applicant keyword in line: '{line}'")

                            if "early applicant" in line_lower or "be an early applicant" in line_lower:
                                applicants = 0
                                print("DEBUG: Found early applicant in card")
                                break
                            else:
                                # Tìm số trong text
                                m = re.search(r"(\d[\d,.]*)", line)
                                if m:
                                    num = re.sub(r"[^0-9]", "", m.group(1))
                                    if num:
                                        try:
                                            applicants = int(num)
                                            print(f"DEBUG: Found applicants in card: {applicants}")
                                        except Exception:
                                            applicants = None
                                else:
                                    print(f"DEBUG: No number found in applicant line: '{line}'")
                                break

                    # Nếu chưa tìm thấy, thử tìm trong toàn bộ card text
                    if applicants is None:
                        card_text_lower = card_text.lower()
                        if "be an early applicant" in card_text_lower:
                            applicants = 0
                            print("DEBUG: Found 'be an early applicant' in full card text")
                        elif any(k in card_text_lower for k in applicant_tokens):
                            # Tìm số trong toàn bộ text
                            matches = re.findall(r"(\d+)\s*(?:applicant|people applied)", card_text_lower)
                            if matches:
                                try:
                                    applicants = int(matches[0])
                                    print(f"DEBUG: Found applicants in full text: {applicants}")
                                except Exception:
                                    pass

            except Exception as e:
                print(f"DEBUG: Error parsing card metadata: {e}")

            # --- Chỉ click vào job để lấy mô tả nếu cần thiết ---
            try:
                # Nếu đã có đủ thông tin cơ bản, có thể bỏ qua việc click để tránh timeout
                if applicants is not None and posted_at is not None:
                    print("DEBUG: Skipping job details click - already have basic info")
                    # Vẫn thử lấy description nhanh
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", card)
                        time.sleep(0.3)
                        driver.execute_script("arguments[0].click();", title_el)
                        time.sleep(1.5)  # Chờ ngắn hơn

                        desc = self._extract_full_description(driver)
                    except Exception:
                        desc = None
                else:
                    # Click để lấy thông tin chi tiết
                    driver.execute_script("arguments[0].scrollIntoView(true);", card)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", title_el)

                    # Chờ job details panel xuất hiện với timeout ngắn hơn
                    wait = WebDriverWait(driver, 5)  # Giảm từ 10 xuống 5 giây
                    try:
                        wait.until(
                            EC.any_of(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search__job-details--container")),
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details-jobs-unified-top-card")),
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-unified-top-card")),
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".scaffold-layout__detail"))
                            )
                        )
                    except Exception:
                        print("DEBUG: Timeout waiting for job details panel")

                    time.sleep(1)  # Giảm delay

                    # Mô tả - cải thiện để lấy toàn bộ content
                    try:
                        desc = self._extract_full_description(driver)
                    except Exception as e:
                        print(f"DEBUG: Error extracting description: {e}")
                        desc = None

            except Exception as e:
                print(f"DEBUG: Error processing job details: {e}")
                desc = None

            jobs.append(
                JobPosting(
                    title=title,
                    company=company,
                    location=loc,
                    url=url,
                    source="linkedin",
                    posted_at=posted_at,
                    applicants=applicants,
                    description=desc,
                    raw={"card_html": card.get_attribute("outerHTML")},
                )
            )
        return jobs

