"""
Integration module to process LinkedIn job descriptions using the NLP pipeline.

This module:
1. Reads job data from MongoDB
2. Processes descriptions through the NLP pipeline
3. Saves enriched data back to database
"""

import logging
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.storage import JobStorage
from core.processing.processor import JobDescriptionProcessor, ProcessedJobInfo

logger = logging.getLogger(__name__)


class LinkedInJobProcessor:
    """Process LinkedIn job descriptions and save enriched data."""

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "crawler",
        input_collection: str = "test",
        output_collection: str = "processed_jobs",
        config_path: Optional[str] = None
    ):
        self.storage = JobStorage(mongo_uri, db_name, input_collection)
        self.output_storage = JobStorage(mongo_uri, db_name, output_collection)

        # Initialize NLP processor
        config_file = config_path or str(project_root / "core" / "processing" / "config.json")
        self.nlp_processor = JobDescriptionProcessor(config_file if Path(config_file).exists() else None)

        logger.info(f"LinkedInJobProcessor initialized - Input: {input_collection}, Output: {output_collection}")

    def process_all_jobs(self, limit: Optional[int] = None, skip_processed: bool = True) -> Dict[str, Any]:
        """Process all jobs in the input collection."""
        try:
            # Get jobs from database
            jobs = self._get_jobs_to_process(limit, skip_processed)

            if not jobs:
                logger.info("No jobs to process")
                return {"processed": 0, "errors": 0, "skipped": 0}

            logger.info(f"Processing {len(jobs)} job descriptions...")

            # Process jobs
            results = {
                "processed": 0,
                "errors": 0,
                "skipped": 0,
                "start_time": datetime.now().isoformat(),
                "job_details": []
            }

            for i, job in enumerate(jobs):
                try:
                    logger.info(f"Processing job {i+1}/{len(jobs)}: {job.get('title', 'Unknown')}")

                    # Process description
                    processed_result = self._process_single_job(job)

                    if processed_result:
                        # Save to output collection
                        enriched_job = self._create_enriched_job(job, processed_result)
                        self._save_processed_job(enriched_job)

                        results["processed"] += 1
                        results["job_details"].append({
                            "title": job.get('title', 'Unknown'),
                            "company": job.get('company', 'Unknown'),
                            "processing_time": processed_result.processing_time,
                            "extractions": {
                                "skills": len(processed_result.skills),
                                "technologies": len(processed_result.technologies),
                                "roles": len(processed_result.roles),
                                "responsibilities": len(processed_result.responsibilities)
                            }
                        })
                    else:
                        results["skipped"] += 1

                except Exception as e:
                    logger.error(f"Error processing job {i+1}: {e}")
                    results["errors"] += 1

            results["end_time"] = datetime.now().isoformat()
            results["total_time"] = (datetime.fromisoformat(results["end_time"]) -
                                   datetime.fromisoformat(results["start_time"])).total_seconds()

            logger.info(f"Processing complete: {results['processed']} processed, {results['errors']} errors, {results['skipped']} skipped")
            return results

        except Exception as e:
            logger.error(f"Error in process_all_jobs: {e}")
            raise

    def _get_jobs_to_process(self, limit: Optional[int], skip_processed: bool) -> List[Dict[str, Any]]:
        """Get jobs from database that need processing."""
        try:
            # Query for jobs with descriptions
            query = {"description": {"$exists": True, "$ne": "", "$ne": None}}

            if skip_processed:
                # Skip jobs that have already been processed
                processed_urls = set()
                for doc in self.output_storage.collection.find({}, {"url": 1}):
                    if doc.get("url"):
                        processed_urls.add(doc["url"])

                if processed_urls:
                    query["url"] = {"$nin": list(processed_urls)}

            # Get jobs from database
            cursor = self.storage.collection.find(query)

            if limit:
                cursor = cursor.limit(limit)

            jobs = list(cursor)
            logger.info(f"Found {len(jobs)} jobs to process")

            return jobs

        except Exception as e:
            logger.error(f"Error querying jobs: {e}")
            return []

    def _process_single_job(self, job: Dict[str, Any]) -> Optional[ProcessedJobInfo]:
        """Process a single job description."""
        description = job.get('description', '')

        if not description or len(description.strip()) < 50:
            logger.warning(f"Job {job.get('title', 'Unknown')} has insufficient description")
            return None

        try:
            # Process through NLP pipeline
            result = self.nlp_processor.process(description)

            # Add job metadata
            result.job_id = str(job.get('_id', ''))
            result.job_title = job.get('title', '')
            result.company = job.get('company', '')
            result.location = job.get('location', '')
            result.url = job.get('url', '')
            result.source = job.get('source', 'linkedin')

            return result

        except Exception as e:
            logger.error(f"Error processing job description: {e}")
            return None

    def _create_enriched_job(self, original_job: Dict[str, Any], processed_info: ProcessedJobInfo) -> Dict[str, Any]:
        """Create enriched job document combining original data with NLP results."""
        # Start with original job data
        enriched = original_job.copy()

        # Add processing metadata
        enriched['processing'] = {
            'processed_at': datetime.now().isoformat(),
            'processing_time': processed_info.processing_time,
            'nlp_version': '1.0',
            'confidence_scores': processed_info.confidence_scores
        }

        # Add extracted information
        enriched['extracted'] = {
            # Contact and basic info
            'dates': processed_info.dates,
            'durations': processed_info.durations,
            'emails': processed_info.emails,
            'urls': processed_info.urls,
            'phone_numbers': processed_info.phone_numbers,

            # Skills and technologies
            'skills': processed_info.skills,
            'technologies': processed_info.technologies,
            'roles': processed_info.roles,

            # Job details
            'responsibilities': processed_info.responsibilities,
            'qualifications': processed_info.qualifications,
            'benefits': processed_info.benefits,

            # Keyword matches
            'matched_skills': processed_info.matched_skills,
            'matched_technologies': processed_info.matched_technologies
        }

        # Add summary statistics
        enriched['extraction_stats'] = {
            'total_skills': len(processed_info.skills),
            'total_technologies': len(processed_info.technologies),
            'total_responsibilities': len(processed_info.responsibilities),
            'total_qualifications': len(processed_info.qualifications),
            'total_matches': len(processed_info.matched_skills) + len(processed_info.matched_technologies),
            'text_length_original': len(processed_info.original_description),
            'text_length_cleaned': len(processed_info.cleaned_text)
        }

        # Store cleaned description
        enriched['description_cleaned'] = processed_info.cleaned_text

        return enriched

    def _save_processed_job(self, enriched_job: Dict[str, Any]):
        """Save processed job to output collection."""
        try:
            # Remove _id to avoid conflicts
            if '_id' in enriched_job:
                enriched_job['original_id'] = str(enriched_job.pop('_id'))

            self.output_storage.collection.insert_one(enriched_job)

        except Exception as e:
            logger.error(f"Error saving processed job: {e}")
            raise

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed jobs."""
        try:
            total_processed = self.output_storage.collection.count_documents({})

            # Get average processing time
            pipeline = [
                {"$group": {
                    "_id": None,
                    "avg_processing_time": {"$avg": "$processing.processing_time"},
                    "avg_skills_count": {"$avg": "$extraction_stats.total_skills"},
                    "avg_tech_count": {"$avg": "$extraction_stats.total_technologies"},
                    "avg_confidence": {"$avg": "$processing.confidence_scores.ner_confidence"}
                }}
            ]

            stats = list(self.output_storage.collection.aggregate(pipeline))

            result = {
                "total_processed": total_processed,
                "averages": stats[0] if stats else {}
            }

            # Get top skills and technologies
            result["top_skills"] = self._get_top_extracted_items("extracted.skills")
            result["top_technologies"] = self._get_top_extracted_items("extracted.technologies")

            return result

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def _get_top_extracted_items(self, field: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top extracted items across all processed jobs."""
        try:
            pipeline = [
                {"$unwind": f"${field}"},
                {"$group": {
                    "_id": f"${field}",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]

            results = list(self.output_storage.collection.aggregate(pipeline))
            return [{"item": r["_id"], "count": r["count"]} for r in results]

        except Exception as e:
            logger.error(f"Error getting top items for {field}: {e}")
            return []

    def process_specific_jobs(self, job_urls: List[str]) -> Dict[str, Any]:
        """Process specific jobs by their URLs."""
        query = {"url": {"$in": job_urls}}
        jobs = list(self.storage.collection.find(query))

        logger.info(f"Processing {len(jobs)} specific jobs")

        results = {"processed": 0, "errors": 0, "not_found": len(job_urls) - len(jobs)}

        for job in jobs:
            try:
                processed_result = self._process_single_job(job)
                if processed_result:
                    enriched_job = self._create_enriched_job(job, processed_result)
                    self._save_processed_job(enriched_job)
                    results["processed"] += 1
            except Exception as e:
                logger.error(f"Error processing specific job: {e}")
                results["errors"] += 1

        return results


def main():
    """Main function to run the LinkedIn job processor."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Initialize processor
        processor = LinkedInJobProcessor()

        # Process first 10 jobs as a test
        print("Processing LinkedIn job descriptions...")
        results = processor.process_all_jobs(limit=100)

        print(f"\nProcessing Results:")
        print(f"  Processed: {results['processed']}")
        print(f"  Errors: {results['errors']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Total time: {results.get('total_time', 0):.2f} seconds")

        # Get statistics
        stats = processor.get_processing_statistics()
        print(f"\nStatistics:")
        print(f"  Total processed jobs: {stats.get('total_processed', 0)}")

        if stats.get('top_skills'):
            print(f"\nTop Skills:")
            for skill in stats['top_skills'][:5]:
                print(f"    {skill['item']}: {skill['count']} jobs")

        if stats.get('top_technologies'):
            print(f"\nTop Technologies:")
            for tech in stats['top_technologies'][:5]:
                print(f"    {tech['item']}: {tech['count']} jobs")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
