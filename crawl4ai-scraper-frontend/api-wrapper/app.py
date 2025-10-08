#!/usr/bin/env python3
"""
Crawl4AI API Wrapper
Exposes Crawl4AI functionality through a REST API for the frontend interface
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import Crawl4AI components
try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import LLMExtractionStrategy, CosineStrategy
    from crawl4ai.chunking_strategy import RegexChunking
except ImportError as e:
    print(f"Error importing Crawl4AI: {e}")
    print("Please ensure Crawl4AI is installed: pip install crawl4ai")
    raise

app = FastAPI(
    title="Crawl4AI API Wrapper",
    description="REST API wrapper for Crawl4AI web scraping library",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use database for production)
jobs: Dict[str, Dict] = {}
results: List[Dict] = []
categories: List[str] = []
stats = {
    "total_results": 0,
    "total_categories": 0,
    "total_jobs": 0,
    "successful_jobs": 0,
    "last_update": None
}

# Request/Response Models
class ScrapeConfig(BaseModel):
    urls: Optional[List[str]] = None
    max_items: Optional[int] = 100
    include_media: bool = True
    include_documents: bool = True
    include_metadata: bool = True
    extraction_strategy: Optional[str] = "basic"
    chunking_strategy: Optional[str] = "regex"

class ScrapeResponse(BaseModel):
    success: bool
    job_id: str
    message: str

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str

# Global crawler instance
crawler = None

async def get_crawler():
    """Get or create AsyncWebCrawler instance"""
    global crawler
    if crawler is None:
        crawler = AsyncWebCrawler(verbose=True)
        await crawler.start()
    return crawler

@app.on_event("startup")
async def startup_event():
    """Initialize crawler on startup"""
    await get_crawler()
    print("🕷️ Crawl4AI API Wrapper started successfully")

@app.on_event("shutdown")  
async def shutdown_event():
    """Cleanup on shutdown"""
    global crawler
    if crawler:
        await crawler.close()
        print("👋 Crawl4AI API Wrapper shut down")

# API Endpoints

@app.get("/health")
async def health_simple():
    """Simple health check for Docker"""
    return {"status": "healthy", "service": "crawl4ai-api"}

@app.get("/api/scraper/health", response_model=HealthResponse)
async def health_check():
    """Check API health status"""
    try:
        crawler = await get_crawler()
        return HealthResponse(
            status="healthy",
            message="Crawl4AI API is running",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/api/scraper/trigger", response_model=ScrapeResponse)
async def trigger_scraping(config: ScrapeConfig, background_tasks: BackgroundTasks):
    """Start a new scraping job"""
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    # Create job record
    job = {
        "job_id": job_id,
        "status": "queued",
        "config": config.dict(),
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "error": None,
        "results_count": 0
    }
    
    jobs[job_id] = job
    stats["total_jobs"] += 1
    
    # Start background scraping task
    background_tasks.add_task(execute_scraping_job, job_id, config)
    
    return ScrapeResponse(
        success=True,
        job_id=job_id,
        message="Scraping job queued successfully"
    )

async def execute_scraping_job(job_id: str, config: ScrapeConfig):
    """Execute the actual scraping job"""
    global results, categories, stats
    
    job = jobs[job_id]
    job["status"] = "running"
    job["started_at"] = datetime.now().isoformat()
    
    try:
        crawler = await get_crawler()
        
        # Default URLs if none provided
        urls_to_crawl = config.urls or [
            "https://example.com",
            "https://httpbin.org/html",
            "https://quotes.toscrape.com"
        ]
        
        # Limit URLs based on max_items
        if config.max_items:
            urls_to_crawl = urls_to_crawl[:config.max_items]
        
        scraped_results = []
        
        for i, url in enumerate(urls_to_crawl):
            try:
                print(f"Scraping {i+1}/{len(urls_to_crawl)}: {url}")
                
                # Configure extraction strategy
                extraction_strategy = None
                if config.extraction_strategy == "llm":
                    # This would require LLM setup - simplified for demo
                    pass
                elif config.extraction_strategy == "cosine":
                    extraction_strategy = CosineStrategy()
                
                # Configure chunking
                chunking_strategy = RegexChunking() if config.chunking_strategy == "regex" else None
                
                # Perform the crawl
                result = await crawler.arun(
                    url=url,
                    extraction_strategy=extraction_strategy,
                    chunking_strategy=chunking_strategy,
                    bypass_cache=True
                )
                
                if result.success:
                    # Process result
                    scraped_result = {
                        "id": f"result_{uuid.uuid4().hex[:8]}",
                        "url": url,
                        "title": result.metadata.get("title", f"Page {i+1}"),
                        "description": result.cleaned_html[:200] + "..." if len(result.cleaned_html) > 200 else result.cleaned_html,
                        "content": result.markdown if config.include_metadata else result.cleaned_html,
                        "scraped_at": datetime.now().isoformat(),
                        "success": True,
                        "links_found": len(result.links) if hasattr(result, 'links') else 0,
                        "media_found": len(result.media) if hasattr(result, 'media') and config.include_media else 0
                    }
                    
                    scraped_results.append(scraped_result)
                    results.append(scraped_result)
                    
                    # Extract categories (simplified)
                    if result.metadata.get("keywords"):
                        page_categories = result.metadata["keywords"][:3]  # Take first 3 keywords as categories
                        for cat in page_categories:
                            if cat not in categories:
                                categories.append(cat)
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                # Continue with next URL
                continue
        
        # Update job status
        job["status"] = "completed"
        job["completed_at"] = datetime.now().isoformat()
        job["results_count"] = len(scraped_results)
        
        # Update stats
        stats["successful_jobs"] += 1
        stats["total_results"] = len(results)
        stats["total_categories"] = len(categories)
        stats["last_update"] = datetime.now().isoformat()
        
        print(f"✅ Job {job_id} completed successfully. Scraped {len(scraped_results)} pages.")
        
    except Exception as e:
        # Update job with error
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.now().isoformat()
        print(f"❌ Job {job_id} failed: {e}")

@app.get("/api/scraper/status")
async def get_scraping_status():
    """Get current scraping status"""
    # Find most recent job
    current_job = None
    last_successful = None
    
    if jobs:
        sorted_jobs = sorted(jobs.values(), key=lambda x: x["created_at"], reverse=True)
        current_job = sorted_jobs[0] if sorted_jobs else None
        
        # Find last successful job
        for job in sorted_jobs:
            if job["status"] == "completed":
                last_successful = job
                break
    
    return {
        "current_job": current_job,
        "last_successful_scrape": last_successful,
        "scraping_available": True,
        "active_jobs": sum(1 for job in jobs.values() if job["status"] in ["queued", "running"])
    }

@app.get("/api/scraper/results")
async def get_results(page: int = 1, limit: int = 10, search: str = "", category: str = ""):
    """Get paginated scraping results"""
    filtered_results = results
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        filtered_results = [
            r for r in results 
            if search_lower in r["title"].lower() or search_lower in r["description"].lower()
        ]
    
    # Apply category filter (simplified)
    if category:
        # This would need proper category association - simplified for demo
        pass
    
    # Apply pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_results = filtered_results[start_idx:end_idx]
    
    return {
        "results": paginated_results,
        "total": len(filtered_results),
        "page": page,
        "limit": limit,
        "has_more": end_idx < len(filtered_results)
    }

@app.get("/api/scraper/categories")
async def get_categories():
    """Get available categories"""
    return categories

@app.get("/api/scraper/stats")
async def get_stats():
    """Get scraping statistics"""
    return stats

@app.get("/api/scraper/search")
async def search_results(q: str, category: str = "", page: int = 1, limit: int = 20):
    """Search through scraped results"""
    return await get_results(page=page, limit=limit, search=q, category=category)

# Additional endpoints for job management
@app.get("/api/scraper/jobs")
async def get_jobs(limit: int = 10):
    """Get recent jobs"""
    sorted_jobs = sorted(jobs.values(), key=lambda x: x["created_at"], reverse=True)
    return {"jobs": sorted_jobs[:limit]}

@app.get("/api/scraper/jobs/{job_id}")
async def get_job(job_id: str):
    """Get specific job details"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
