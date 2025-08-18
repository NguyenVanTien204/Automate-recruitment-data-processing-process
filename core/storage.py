"""Lưu CSV/DB"""
import logging
from typing import List, Union
from pymongo import MongoClient
from dataclasses import asdict, is_dataclass
from sites.base_site import JobPosting

logger = logging.getLogger("storage")
logger.setLevel(logging.INFO)


class JobStorage:
    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "crawler", collection: str = "intern"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection]

    def _to_dict(self, job: Union[JobPosting, dict]) -> dict:
        """Convert JobPosting/dataclass hoặc dict sang dict chuẩn để lưu DB."""
        if is_dataclass(job):
            return asdict(job)
        elif isinstance(job, dict):
            return job
        else:
            raise TypeError(f"Không hỗ trợ kiểu dữ liệu: {type(job)}")

    def save_jobs(self, jobs: List[Union[JobPosting, dict]]):
        if not jobs:
            logger.warning("Không có job nào để lưu")
            return

        docs = [self._to_dict(job) for job in jobs]
        if docs:
            self.collection.insert_many(docs)
            logger.info(f"Đã lưu {len(docs)} jobs vào MongoDB ({self.collection.full_name})")
        else:
            logger.warning("Danh sách jobs sau khi convert rỗng")
