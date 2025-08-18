"""
Integration module to process LinkedIn job descriptions using enhanced NLP pipeline.

This module:
1. Reads job data from MongoDB
2. Processes descriptions through NLP pipeline (English + Vietnamese)
3. Saves enriched data back to database
4. Enhanced with Vietnamese keywords, seniority levels, and extended technologies
"""

import logging
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from core.storage import JobStorage
from core.processing.processor import JobDescriptionProcessor, ProcessedJobInfo
from vietnamese_enhancement_report import generate_final_report
# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))



logger = logging.getLogger(__name__)


class LinkedInJobProcessor:
    """Process LinkedIn job descriptions and save enriched data with Vietnamese support."""

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "crawler",
        input_collection: str = "demo",
        output_collection: str = "processed_jobs",
        config_path: Optional[str] = None
    ):
        self.storage = JobStorage(mongo_uri, db_name, input_collection)
        self.output_storage = JobStorage(mongo_uri, db_name, output_collection)

        # Initialize enhanced NLP processor
        config_file = config_path or str(project_root / "core" / "processing" / "config.json")
        self.nlp_processor = JobDescriptionProcessor(config_file if Path(config_file).exists() else None)

        logger.info(f"LinkedInJobProcessor initialized - Input: {input_collection}, Output: {output_collection}")
        print(f"🇻🇳 Enhanced with Vietnamese keywords support")

    def process_all_jobs(self, limit: Optional[int] = None, skip_processed: bool = True) -> Dict[str, Any]:
        """Process all jobs in the input collection with enhanced Vietnamese support."""
        try:
            # Get jobs from database
            jobs = self._get_jobs_to_process(limit, skip_processed)

            if not jobs:
                logger.info("No jobs to process")
                return {"processed": 0, "errors": 0, "skipped": 0}

            logger.info(f"Processing {len(jobs)} job descriptions with Vietnamese keywords...")

            # Process jobs
            results = {
                "processed": 0,
                "errors": 0,
                "skipped": 0,
                "start_time": datetime.now().isoformat(),
                "job_details": [],
                # Enhanced stats
                "vietnamese_detected": 0,
                "seniority_detected": 0,
                "extended_tech_detected": 0
            }

            for i, job in enumerate(jobs):
                try:
                    logger.info(f"Processing job {i+1}/{len(jobs)}: {job.get('title', 'Unknown')}")

                    # Process description with enhanced NLP
                    processed_result = self._process_single_job(job)

                    if processed_result:
                        # Save to output collection with enhanced data
                        enriched_job = self._create_enriched_job(job, processed_result)
                        self._save_processed_job(enriched_job)

                        results["processed"] += 1

                        # Track Vietnamese enhancements
                        if processed_result.vietnamese_keywords:
                            results["vietnamese_detected"] += 1
                        if processed_result.seniority_levels:
                            results["seniority_detected"] += 1
                        if processed_result.extended_technologies:
                            results["extended_tech_detected"] += 1

                        results["job_details"].append({
                            "title": job.get('title', 'Unknown'),
                            "company": job.get('company', 'Unknown'),
                            "processing_time": processed_result.processing_time,
                            "extractions": {
                                "skills": len(processed_result.skills),
                                "technologies": len(processed_result.technologies),
                                "roles": len(processed_result.roles),
                                "responsibilities": len(processed_result.responsibilities),
                                # Enhanced extractions
                                "vietnamese_keywords": len(processed_result.vietnamese_keywords),
                                "seniority_levels": len(processed_result.seniority_levels),
                                "extended_technologies": len(processed_result.extended_technologies)
                            },
                            # Show sample Vietnamese keywords
                            "sample_vietnamese": [kw.get('keyword', '') for kw in processed_result.vietnamese_keywords[:3]],
                            "sample_seniority": [s.get('keyword', '') for s in processed_result.seniority_levels[:2]]
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
            logger.info(f"Vietnamese enhancements: {results['vietnamese_detected']} VN keywords, {results['seniority_detected']} seniority, {results['extended_tech_detected']} extended tech")
            return results

        except Exception as e:
            logger.error(f"Error in process_all_jobs: {e}")
            raise

    def _get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about processed jobs."""
        print(f"\n=== Comprehensive Vietnamese Keywords Statistics ===")

        # Overall statistics
        total_linkedin_jobs = self.storage.collection.count_documents({'source': 'linkedin'})
        processed_jobs = self.storage.collection.count_documents({'vietnamese_analysis_completed': True})
        jobs_with_vn = self.storage.collection.count_documents({
            'extracted.vietnamese_keywords': {'$exists': True, '$not': {'$size': 0}}
        })

        print(f"\n📊 OVERVIEW")
        print(f"Total LinkedIn jobs: {total_linkedin_jobs}")
        print(f"Processed with Vietnamese analysis: {processed_jobs}")
        print(f"Jobs containing Vietnamese keywords: {jobs_with_vn}")
        if processed_jobs > 0:
            print(f"Coverage: {(processed_jobs/total_linkedin_jobs*100):.1f}%")
            print(f"Vietnamese detection rate: {(jobs_with_vn/processed_jobs*100):.1f}%")

        # Get detailed analysis
        vn_jobs = list(self.storage.collection.find({
            'extracted.vietnamese_keywords': {'$exists': True, '$not': {'$size': 0}}
        }))

        if not vn_jobs:
            print("No jobs with Vietnamese keywords found.")
            return {"total_jobs": total_linkedin_jobs, "processed": processed_jobs, "vietnamese": 0}

        # Analyze seniority levels
        seniority_counts = {}
        vn_category_counts = {}
        tech_category_counts = {}

        for job in vn_jobs:
            # Count seniority levels
            for seniority in job.get('extracted', {}).get('seniority_levels', []):
                keyword = seniority.get('keyword', 'Unknown')
                seniority_counts[keyword] = seniority_counts.get(keyword, 0) + 1

            # Count Vietnamese categories
            for vn_kw in job.get('extracted', {}).get('vietnamese_keywords', []):
                category = vn_kw.get('category', 'Unknown')
                vn_category_counts[category] = vn_category_counts.get(category, 0) + 1

            # Count tech categories
            for tech in job.get('extracted', {}).get('extended_technologies', []):
                category = tech.get('category', 'Unknown')
                tech_category_counts[category] = tech_category_counts.get(category, 0) + 1

        # Display seniority statistics
        if seniority_counts:
            print(f"\n🎯 SENIORITY LEVELS")
            for keyword, count in sorted(seniority_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / jobs_with_vn * 100)
                print(f"  {keyword:<15} │ {count:>3} jobs │ {percentage:>5.1f}%")

        # Display Vietnamese categories
        if vn_category_counts:
            print(f"\n🇻🇳 VIETNAMESE KEYWORDS")
            for category, count in sorted(vn_category_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {category:<25} │ {count:>3} mentions")

        # Display tech categories
        if tech_category_counts:
            print(f"\n💻 TECHNOLOGY CATEGORIES")
            top_tech_categories = sorted(tech_category_counts.items(), key=lambda x: x[1], reverse=True)[:8]
            for category, count in top_tech_categories:
                print(f"  {category:<25} │ {count:>3} mentions")

        # Show sample jobs
        print(f"\n📝 SAMPLE JOBS WITH VIETNAMESE CONTENT")
        sample_jobs = vn_jobs[:3]
        for i, job in enumerate(sample_jobs, 1):
            title = job.get('title', 'Untitled')[:40]
            company = job.get('company', 'Unknown')[:30]

            vn_keywords = [kw['keyword'] for kw in job.get('extracted', {}).get('vietnamese_keywords', [])]
            seniority = [s['keyword'] for s in job.get('extracted', {}).get('seniority_levels', [])]

            print(f"\n  {i}. {title}...")
            print(f"     Company: {company}")
            print(f"     Vietnamese: {vn_keywords[:4]}")
            print(f"     Seniority: {seniority}")

        return {
            "total_jobs": total_linkedin_jobs,
            "processed": processed_jobs,
            "vietnamese": jobs_with_vn,
            "seniority_counts": seniority_counts,
            "vn_categories": vn_category_counts,
            "tech_categories": tech_category_counts
        }

    def show_detailed_analysis(self) -> None:
        """Show detailed analysis of Vietnamese keywords and job insights."""
        print(f"\n=== Detailed Vietnamese Keywords Analysis ===")

        # Get jobs with Vietnamese keywords
        pipeline = [
            {
                '$match': {
                    'source': 'linkedin',
                    'extracted.vietnamese_keywords': {'$exists': True, '$ne': []},
                    'extracted.seniority_levels': {'$exists': True}
                }
            },
            {
                '$project': {
                    'title': 1,
                    'company': 1,
                    'description': {'$substr': ['$description', 0, 100]},
                    'extracted.vietnamese_keywords': 1,
                    'extracted.seniority_levels': 1,
                    'extracted.extended_technologies': 1
                }
            }
        ]

        detailed_jobs = list(self.storage.collection.aggregate(pipeline))

        if not detailed_jobs:
            print("No detailed data available.")
            return

        print(f"Found {len(detailed_jobs)} jobs with detailed Vietnamese analysis")

        # Analyze keyword combinations
        keyword_combinations = {}
        for job in detailed_jobs:
            vn_keywords = [kw['keyword'] for kw in job.get('extracted', {}).get('vietnamese_keywords', [])]
            seniority = [s['keyword'] for s in job.get('extracted', {}).get('seniority_levels', [])]

            # Create combination key
            if vn_keywords or seniority:
                key = f"{'+'.join(sorted(seniority))}"
                if vn_keywords:
                    vn_filtered = [kw for kw in vn_keywords if kw not in seniority]
                    if vn_filtered:
                        key += f"|{'+'.join(sorted(vn_filtered)[:2])}"

                keyword_combinations[key] = keyword_combinations.get(key, 0) + 1

        # Show top combinations
        print(f"\n🔗 TOP KEYWORD COMBINATIONS")
        top_combinations = sorted(keyword_combinations.items(), key=lambda x: x[1], reverse=True)[:10]
        for combo, count in top_combinations:
            print(f"  {combo:<30} │ {count:>2} jobs")

        # Company analysis
        company_vn_stats = {}
        for job in detailed_jobs:
            company = job.get('company', 'Unknown')
            vn_count = len(job.get('extracted', {}).get('vietnamese_keywords', []))

            if company not in company_vn_stats:
                company_vn_stats[company] = {'jobs': 0, 'vn_keywords': 0}

            company_vn_stats[company]['jobs'] += 1
            company_vn_stats[company]['vn_keywords'] += vn_count

        # Show companies with most Vietnamese content
        print(f"\n🏢 COMPANIES WITH MOST VIETNAMESE CONTENT")
        sorted_companies = sorted(company_vn_stats.items(),
                                key=lambda x: x[1]['vn_keywords'], reverse=True)[:5]

        for company, stats in sorted_companies:
            avg_vn = stats['vn_keywords'] / stats['jobs'] if stats['jobs'] > 0 else 0
            company_name = company[:25] if company != 'Unknown' else 'Unknown'
            print(f"  {company_name:<25} │ {stats['jobs']:>2} jobs │ {avg_vn:>4.1f} avg VN")

    def quick_test(self, sample_size: int = 3) -> None:
        """Quick test with a few sample jobs."""
        print(f"\n=== Quick Test ({sample_size} jobs) ===")

        # Get sample jobs that haven't been processed
        sample_jobs = list(self.storage.collection.find({
            'source': 'linkedin',
            'vietnamese_analysis_completed': {'$ne': True}
        }).limit(sample_size))

        if not sample_jobs:
            print("No unprocessed jobs for testing. Showing processed samples...")
            sample_jobs = list(self.storage.collection.find({
                'source': 'linkedin'
            }).limit(sample_size))

        for i, job in enumerate(sample_jobs, 1):
            print(f"\n--- Sample {i}: {job.get('title', 'Untitled')[:40]}... ---")

            description = job.get('description', '')[:200]
            print(f"Description: {description}...")

            # Process if not already done
            if not job.get('vietnamese_analysis_completed'):
                result = self.nlp_processor.process(job.get('description', ''))

                vn_keywords = [kw['keyword'] for kw in result.vietnamese_keywords]
                seniority = [s['keyword'] for s in result.seniority_levels]
                technologies = [t['keyword'] for t in result.extended_technologies[:3]]

                print(f"Vietnamese Keywords: {vn_keywords}")
                print(f"Seniority Levels: {seniority}")
                print(f"Technologies: {technologies}")
            else:
                vn_keywords = [kw['keyword'] for kw in job.get('extracted', {}).get('vietnamese_keywords', [])]
                seniority = [s['keyword'] for s in job.get('extracted', {}).get('seniority_levels', [])]

                print(f"Vietnamese Keywords (cached): {vn_keywords}")
                print(f"Seniority Levels (cached): {seniority}")

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
            query = {"description": {"$exists": True, "$nin": ["", None]}}

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
            'matched_technologies': processed_info.matched_technologies,
            
            # Vietnamese enhancements - organized within extracted section
            'vietnamese_keywords': processed_info.vietnamese_keywords,
            'seniority_levels': processed_info.seniority_levels,
            'extended_technologies': processed_info.extended_technologies
        }

        # Keep analysis completion flag at root level for easy querying
        enriched['vietnamese_analysis_completed'] = True

        # Add summary statistics
        enriched['extraction_stats'] = {
            'total_skills': len(processed_info.skills),
            'total_technologies': len(processed_info.technologies),
            'total_responsibilities': len(processed_info.responsibilities),
            'total_qualifications': len(processed_info.qualifications),
            'total_matches': len(processed_info.matched_skills) + len(processed_info.matched_technologies),
            'text_length_original': len(processed_info.original_description),
            'text_length_cleaned': len(processed_info.cleaned_text),
            # Vietnamese enhancement stats
            'vietnamese_keywords_count': len(processed_info.vietnamese_keywords),
            'seniority_levels_count': len(processed_info.seniority_levels),
            'extended_technologies_count': len(processed_info.extended_technologies)
        }

        # Store cleaned description
        enriched['description_cleaned'] = processed_info.cleaned_text

        return enriched

    def _save_processed_job(self, enriched_job: Dict[str, Any]):
        """Update the original job with processed data."""
        try:
            # Get the original job ID
            job_id = enriched_job.get('_id')
            if not job_id:
                logger.error("No job ID found for updating")
                return

            # Prepare update data (without _id)
            update_data = {k: v for k, v in enriched_job.items() if k != '_id'}

            # Update the original job in place
            result = self.storage.collection.update_one(
                {'_id': job_id},
                {'$set': update_data}
            )

            if result.modified_count > 0:
                logger.debug(f"Successfully updated job {job_id}")
            else:
                logger.warning(f"Job {job_id} was not updated")

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
    """Main function with integrated Vietnamese keywords processing."""
    print("🇻🇳 Enhanced LinkedIn Job Processor with Vietnamese Keywords")
    print("="*70)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Initialize enhanced processor
        processor = LinkedInJobProcessor()

        # Interactive menu
        while True:
            print(f"\n" + "="*50)
            print("🎯 ENHANCED LINKEDIN JOB PROCESSOR MENU")
            print("="*50)
            print("1. 🚀 Process ALL LinkedIn jobs with Vietnamese keywords")
            print("2. 📊 Show comprehensive statistics")
            print("3. 🔍 Show vietnamese report")
            print("4. ⚡ Quick test (3 sample jobs)")
            print("5. 📈 Process specific number of jobs")
            print("6. 🔄 Force reprocess all jobs")
            print("7. 📋 Generate final report")
            print("0. ❌ Exit")

            choice = input("\nSelect option (0-7): ").strip()

            if choice == "1":
                # Process all jobs
                print("\n🚀 Processing ALL LinkedIn jobs...")
                results = processor.process_all_jobs()

                if results["processed"] > 0:
                    processor._get_comprehensive_statistics()

            elif choice == "2":
                # Show statistics
                processor._get_comprehensive_statistics()

            elif choice == "3":
                # Detailed analysis
                generate_final_report()

            elif choice == "4":
                # Quick test
                processor.quick_test(sample_size=3)

            elif choice == "5":
                # Process specific number
                try:
                    limit = int(input("Enter number of jobs to process: "))
                    results = processor.process_all_jobs(limit=limit)
                    if results["processed"] > 0:
                        processor._get_comprehensive_statistics()
                except ValueError:
                    print("❌ Invalid number")

            elif choice == "6":
                # Force reprocess
                print("\n🔄 Force reprocessing ALL jobs...")
                confirm = input("This will reprocess ALL jobs. Continue? (y/N): ")
                if confirm.lower() == 'y':
                    results = processor.process_all_jobs(skip_processed=False)
                    processor._get_comprehensive_statistics()
                else:
                    print("Cancelled.")

            elif choice == "7":
                # Generate final report
                print("\n📋 Generating comprehensive final report...")
                stats = processor._get_comprehensive_statistics()
                processor.show_detailed_analysis()

                print(f"\n" + "="*70)
                print("🎉 VIETNAMESE KEYWORDS ENHANCEMENT REPORT")
                print("="*70)
                print(f"✅ Total LinkedIn jobs: {stats.get('total_jobs', 0)}")
                print(f"✅ Jobs processed: {stats.get('processed', 0)}")
                print(f"✅ Vietnamese keywords detected: {stats.get('vietnamese', 0)}")

                if stats.get('seniority_counts'):
                    print(f"✅ Seniority levels found: {len(stats['seniority_counts'])}")

                if stats.get('tech_categories'):
                    print(f"✅ Technology categories: {len(stats['tech_categories'])}")

                print(f"\n🚀 Features implemented:")
                print(f"   • Vietnamese keyword detection")
                print(f"   • Seniority level extraction")
                print(f"   • Extended technology matching")
                print(f"   • Comprehensive statistical analysis")
                print(f"   • Real-time job processing")

            elif choice == "0":
                print("\n👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please select 0-7.")

            if choice != "0":
                input("\nPress Enter to continue...")

    except KeyboardInterrupt:
        print("\n\n👋 Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
