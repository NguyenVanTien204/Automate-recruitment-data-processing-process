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

    def _parse_applicants_from_card(self, card) -> Optional[int]:
        """Parse applicants info with simplified, more robust approach."""
        try:
            # 1. Lấy toàn bộ text content một lần
            card_text = (card.get_attribute("textContent") or "").strip().lower()

            # 2. Early applicant check - ưu tiên cao nhất
            early_patterns = [
                "be an early applicant",
                "early applicant",
                "be among the first",
                "first to apply"
            ]

            if any(pattern in card_text for pattern in early_patterns):
                print("DEBUG: Found early applicant pattern")
                return 0

            # 3. Tìm pattern số + applicant với regex đơn giản
            applicant_patterns = [
                r'(\d+)\s+(?:applicants?|people\s+applied|people\s+clicked\s+apply)',
                r'(\d+)\s+(?:người\s+đã\s+nộp|đã\s+ứng\s+tuyển)',
                r'applicants?:\s*(\d+)',
                r'(\d+)\s*applicants?'
            ]

            for pattern in applicant_patterns:
                matches = re.findall(pattern, card_text)
                if matches:
                    try:
                        # Lấy số lớn nhất (thường là số applicants chính xác nhất)
                        applicant_count = max(int(match) for match in matches)
                        print(f"DEBUG: Found {applicant_count} applicants using pattern: {pattern}")
                        return applicant_count
                    except (ValueError, TypeError):
                        continue

            # 4. Fallback: tìm trong specific elements với aria-label hoặc data attributes
            try:
                applicant_elements = card.find_elements(By.CSS_SELECTOR,
                    "[aria-label*='applicant'], [data-tracking*='applicant'], .job-card-container__applicant-count, span, div")

                for elem in applicant_elements:
                    elem_text = (elem.get_attribute("textContent") or "").strip().lower()
                    aria_label = (elem.get_attribute("aria-label") or "").strip().lower()

                    # Check both text content and aria-label
                    for text_source in [elem_text, aria_label]:
                        if text_source:
                            # Early applicant check
                            if any(pattern in text_source for pattern in early_patterns):
                                print(f"DEBUG: Found early applicant in element: {text_source}")
                                return 0

                            # Number extraction
                            for pattern in applicant_patterns:
                                matches = re.findall(pattern, text_source)
                                if matches:
                                    try:
                                        applicant_count = int(matches[0])
                                        print(f"DEBUG: Found {applicant_count} applicants in element: {text_source}")
                                        return applicant_count
                                    except (ValueError, TypeError):
                                        continue
            except Exception as e:
                print(f"DEBUG: Error in element search: {e}")

            print("DEBUG: No applicants info found")
            return None

        except Exception as e:
            print(f"DEBUG: Error in _parse_applicants_from_card: {e}")
            return None

    def _parse_posted_at_from_card(self, card) -> Optional[str]:
        """Parse posted time with simplified approach."""
        try:
            card_text = (card.get_attribute("textContent") or "").strip()

            # Split into lines for more precise matching
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]

            # Time keywords
            time_tokens = [
                "ago", "posted", "reposted", "today", "yesterday",
                "giờ trước", "phút trước", "ngày trước", "vừa xong", "hôm nay", "hôm qua",
                "days ago", "hours ago", "minutes ago", "weeks ago", "months ago",
                "hour ago", "day ago", "week ago", "month ago"
            ]

            # First check lines (more precise)
            for line in lines:
                line_lower = line.lower()
                if any(tk in line_lower for tk in time_tokens):
                    print(f"DEBUG: Found posted_at in line: {line}")
                    return line

            # Fallback: regex patterns on full text
            time_patterns = [
                r'(\d+\s+(?:minutes?|hours?|days?|weeks?|months?)\s+ago)',
                r'(posted\s+\d+\s+(?:minutes?|hours?|days?|weeks?|months?)\s+ago)',
                r'(today|yesterday|hôm\s+nay|hôm\s+qua)',
                r'(\d+\s+(?:giờ|phút|ngày)\s+trước)'
            ]

            for pattern in time_patterns:
                matches = re.findall(pattern, card_text.lower())
                if matches:
                    found_time = matches[0].strip()
                    print(f"DEBUG: Found posted_at with regex: {found_time}")
                    return found_time

            # Last resort: check time elements
            try:
                time_elements = card.find_elements(By.CSS_SELECTOR, "time, [datetime], .job-card-container__metadata-item")
                for elem in time_elements:
                    text = (elem.get_attribute("textContent") or "").strip()
                    if text and any(keyword in text.lower() for keyword in ["ago", "posted", "today", "yesterday"]):
                        print(f"DEBUG: Found posted_at in time element: {text}")
                        return text
            except Exception:
                pass

            print("DEBUG: No posted_at info found")
            return None

        except Exception as e:
            print(f"DEBUG: Error in _parse_posted_at_from_card: {e}")
            return None

    def parse_job_cards(self, limit: int = 3) -> List[JobPosting]:
        driver = self.driver
        assert driver is not None

        # Scroll để load đủ job
        self._infinite_scroll(limit=limit)

        jobs: List[JobPosting] = []
        cards = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li")

        for i, card in enumerate(cards[:limit], 1):
            try:
                title_el = card.find_element(By.CSS_SELECTOR, "a.job-card-list__title, a[href*='/jobs/view/']")
                title = self._txt(title_el)
                url = title_el.get_attribute("href")
            except Exception:
                print(f"DEBUG: Card {i} - Cannot find title/url, skipping")
                continue

            company, loc, desc = None, None, None

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

            # === SỬ DỤNG HELPER FUNCTIONS ===
            print(f"DEBUG: Processing card {i} - {title}")

            # Parse thông tin metadata từ card
            posted_at = self._parse_posted_at_from_card(card)
            applicants = self._parse_applicants_from_card(card)

            print(f"DEBUG: Card {i} results - posted_at: {posted_at}, applicants: {applicants}")

            # === XỬ LÝ DESCRIPTION ===
            # Chỉ click để lấy description nếu cần thiết
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

            # Tạo JobPosting object
            job = JobPosting(
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

            jobs.append(job)
            print(f"DEBUG: Card {i} completed - {title} | {company} | {posted_at} | {applicants} applicants")

            # Thêm delay giữa các cards để tránh bị detect
            if i < len(cards[:limit]):
                time.sleep(self.pause + random.uniform(0.2, 0.5))

        print(f"DEBUG: Completed parsing {len(jobs)} jobs")
        return jobs
