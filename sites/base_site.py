"""Base crawler definitions and utilities for job sites.

Provides:
- JobPosting dataclass to standardize crawled fields
- BaseSiteCrawler with setup, navigation, pagination, and run loop

Subclasses should override build_search_url() and parse_job_cards().
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import time

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Optional driver managers (gracefully fallback if not installed)
try:
	from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
except Exception:  # pragma: no cover - optional dep
	ChromeDriverManager = None  # type: ignore


@dataclass
class JobPosting:
	title: str
	company: Optional[str] = None
	location: Optional[str] = None
	url: Optional[str] = None
	source: Optional[str] = None
	salary: Optional[str] = None
	posted_at: Optional[str] = None
	applicants: Optional[int] = None  # Number of applicants, if available
	description: Optional[str] = None
	tags: List[str] = field(default_factory=list)
	raw: Dict[str, Any] = field(default_factory=dict)
	timestamp: time = field(default_factory=lambda: datetime.now().isoformat())
	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)


class BaseSiteCrawler:
	"""Base class with Selenium driver lifecycle and crawl loop.

	Parameters
	- base_url: site base URL used by build_search_url
	- headless: run browser in headless mode
	- timeout: explicit wait timeout seconds
	- max_pages: default max pages to traverse
	- pause: small sleep between actions to be polite
	"""

	def __init__(
		self,
		base_url: str,
		*,
		headless: bool = True,
		timeout: int = 15,
		max_pages: int = 1,
		pause: float = 1.2,
	) -> None:
		self.base_url = base_url.rstrip("/")
		self.headless = headless
		self.timeout = timeout
		self.max_pages = max_pages
		self.pause = pause
		self.driver = None  # type: ignore

	# ---------- Driver ----------
	def setup_driver(self) -> None:
		options = EdgeOptions()
		if self.headless:
			options.add_argument("--headless=new")
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("--window-size=1366,900")
		options.add_argument("--disable-gpu")
		options.add_argument("--disable-blink-features=AutomationControlled")

		try:
			from webdriver_manager.microsoft import EdgeChromiumDriverManager
			service = EdgeService(EdgeChromiumDriverManager().install())
			self.driver = webdriver.Edge(service=service, options=options)

		except Exception:
			# fallback: require msedgedriver on PATH
			self.driver = webdriver.Edge(options=options)

		self.wait = WebDriverWait(self.driver, self.timeout)


	def close(self) -> None:
		try:
			if self.driver:
				self.driver.quit()
		finally:
			self.driver = None

	# ---------- Hooks to override ----------
	def build_search_url(self, keyword: str, location: Optional[str] = None, **kwargs: Any) -> str:
		raise NotImplementedError

	def parse_job_cards(self) -> List[JobPosting]:
		"""Parse current page and return list of JobPosting."""
		raise NotImplementedError

	def go_next_page(self) -> bool:
		"""Default paginator: try to click an element with rel='next' or a typical next button.
		Return True if navigated to next page, else False.
		Subclasses can override for site-specific pagination.
		"""
		driver = self.driver
		assert driver is not None
		try:
			# Try rel=next
			next_el = driver.find_elements(By.CSS_SELECTOR, "a[rel='next'], button[rel='next']")
			if not next_el:
				# Common next patterns
				next_el = driver.find_elements(By.XPATH, "//a[contains(., 'Next') or contains(., 'Sau') or contains(., 'Tiếp') or contains(., '>')][not(contains(@class,'disabled'))]")
			if next_el:
				next_el[0].click()
				time.sleep(self.pause)
				return True
		except Exception:
			return False
		return False

	# ---------- Utilities ----------
	@staticmethod
	def _txt(el) -> str:
		try:
			return el.text.strip()
		except Exception:
			return ""

	# ---------- Main entry ----------
	def run(
		self,
		keyword: str,
		*,
		location: Optional[str] = None,
		limit: int = 50,
		pages: Optional[int] = None,
		extra: Optional[Dict[str, Any]] = None,
	) -> List[Dict[str, Any]]:
		"""Run crawl and return list of dict job records.

		Note: This is a best-effort skeleton and may need selector updates.
		"""
		if self.driver is None:
			self.setup_driver()
		driver = self.driver
		assert driver is not None

		url = self.build_search_url(keyword, location, **(extra or {}))
		driver.get(url)
		self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
		time.sleep(self.pause)

		collected: List[JobPosting] = []
		max_pages = pages if pages is not None else self.max_pages

		for _ in range(max_pages):
			try:
				jobs = self.parse_job_cards()
				for j in jobs:
					collected.append(j)
					if len(collected) >= limit:
						raise StopIteration
				if len(collected) >= limit:
					break
				if not self.go_next_page():
					break
				# Wait next page
				self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
				time.sleep(self.pause)
			except StopIteration:
				break
			except Exception:
				# Best-effort: break on unexpected errors
				break

		# Convert to dicts
		return [j.to_dict() for j in collected]

