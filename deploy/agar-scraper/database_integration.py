"""
Database Integration Module for Agar Scraper Service.

Handles saving scraped data to PostgreSQL database in normalized format
and provides query methods for the Ask Agar API integration.
"""

import asyncio
import asyncpg
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from crawl4ai.agar.schemas import (
    AgarCatalogData, ProductSchema, MediaSchema, 
    DocumentSchema, CategorySchema, ProductCategoryRelation
)

logger = logging.getLogger(__name__)


class AgarDatabaseIntegrator:
    """Handles database operations for Agar scraped data."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def connect(self):
        """Create database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            logger.info("Database connection pool created successfully")
            
            # Ensure tables exist
            await self.ensure_tables_exist()
            
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def ensure_tables_exist(self):
        """Create database tables if they don't exist."""
        schema_sql = """
        -- Products table (normalized from scraped data)
        CREATE TABLE IF NOT EXISTS agar_products (
            product_id VARCHAR(50) PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            product_url TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );

        -- Media table
        CREATE TABLE IF NOT EXISTS agar_media (
            media_id VARCHAR(50) PRIMARY KEY,
            product_id VARCHAR(50) REFERENCES agar_products(product_id) ON DELETE CASCADE,
            media_type VARCHAR(20) NOT NULL,
            media_format VARCHAR(10) NOT NULL,
            media_url TEXT NOT NULL,
            sequence_order INTEGER DEFAULT 1,
            alt_text TEXT,
            dimensions JSONB,
            file_size_kb INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );

        -- Documents table
        CREATE TABLE IF NOT EXISTS agar_documents (
            document_id VARCHAR(50) PRIMARY KEY,
            product_id VARCHAR(50) REFERENCES agar_products(product_id) ON DELETE CASCADE,
            document_type VARCHAR(20) NOT NULL,
            document_name VARCHAR(255) NOT NULL,
            document_url TEXT NOT NULL,
            version VARCHAR(10),
            uploaded_at TIMESTAMP,
            file_size_kb INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );

        -- Categories table
        CREATE TABLE IF NOT EXISTS agar_categories (
            category_id VARCHAR(50) PRIMARY KEY,
            category_name VARCHAR(255) NOT NULL,
            parent_category_id VARCHAR(50) REFERENCES agar_categories(category_id),
            description TEXT,
            slug VARCHAR(255),
            level INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );

        -- Product-Category relationships
        CREATE TABLE IF NOT EXISTS agar_product_categories (
            product_id VARCHAR(50) REFERENCES agar_products(product_id) ON DELETE CASCADE,
            category_id VARCHAR(50) REFERENCES agar_categories(category_id) ON DELETE CASCADE,
            is_primary BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (product_id, category_id)
        );

        -- Scraping jobs tracking
        CREATE TABLE IF NOT EXISTS agar_scraping_jobs (
            job_id SERIAL PRIMARY KEY,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            status VARCHAR(20) DEFAULT 'running',
            products_scraped INTEGER DEFAULT 0,
            media_processed INTEGER DEFAULT 0,
            documents_processed INTEGER DEFAULT 0,
            categories_processed INTEGER DEFAULT 0,
            error_message TEXT,
            metadata JSONB
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_agar_products_name ON agar_products(product_name);
        CREATE INDEX IF NOT EXISTS idx_agar_media_product_id ON agar_media(product_id);
        CREATE INDEX IF NOT EXISTS idx_agar_documents_product_id ON agar_documents(product_id);
        CREATE INDEX IF NOT EXISTS idx_agar_categories_parent ON agar_categories(parent_category_id);
        CREATE INDEX IF NOT EXISTS idx_agar_product_categories_product ON agar_product_categories(product_id);
        CREATE INDEX IF NOT EXISTS idx_agar_scraping_jobs_status ON agar_scraping_jobs(status);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
            logger.info("Database schema ensured")
    
    async def create_scraping_job(self) -> int:
        """Create a new scraping job record."""
        async with self.pool.acquire() as conn:
            job_id = await conn.fetchval(
                "INSERT INTO agar_scraping_jobs (started_at, status) VALUES ($1, $2) RETURNING job_id",
                datetime.now(), 'running'
            )
            logger.info(f"Created scraping job {job_id}")
            return job_id
    
    async def update_job_status(self, job_id: int, status: str, catalog_data: AgarCatalogData = None):
        """Update job status and statistics."""
        async with self.pool.acquire() as conn:
            if catalog_data:
                await conn.execute("""
                    UPDATE agar_scraping_jobs 
                    SET status = $1, completed_at = $2, products_scraped = $3, 
                        media_processed = $4, documents_processed = $5, categories_processed = $6
                    WHERE job_id = $7
                """, status, datetime.now(), len(catalog_data.products), 
                    len(catalog_data.media), len(catalog_data.documents), 
                    len(catalog_data.categories), job_id)
            else:
                await conn.execute(
                    "UPDATE agar_scraping_jobs SET status = $1, completed_at = $2 WHERE job_id = $3",
                    status, datetime.now(), job_id
                )
    
    async def update_job_error(self, job_id: int, error_message: str):
        """Update job with error status."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE agar_scraping_jobs SET status = $1, error_message = $2, completed_at = $3 WHERE job_id = $4",
                'failed', error_message, datetime.now(), job_id
            )
    
    async def save_catalog_data(self, catalog_data: AgarCatalogData, job_id: int):
        """Save complete catalog data to database."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Save products
                for product in catalog_data.products:
                    await self._save_product(conn, product)
                
                # Save media
                for media in catalog_data.media:
                    await self._save_media(conn, media)
                
                # Save documents
                for document in catalog_data.documents:
                    await self._save_document(conn, document)
                
                # Save categories
                for category in catalog_data.categories:
                    await self._save_category(conn, category)
                
                # Save relationships
                for relation in catalog_data.product_categories:
                    await self._save_product_category(conn, relation)
                
                # Update job status
                await self.update_job_status(job_id, 'completed', catalog_data)
                
                logger.info(f"Saved complete catalog data for job {job_id}")
    
    async def _save_product(self, conn, product: ProductSchema):
        """Save or update a product."""
        await conn.execute("""
            INSERT INTO agar_products 
            (product_id, product_name, product_url, description, updated_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (product_id) DO UPDATE SET
                product_name = EXCLUDED.product_name,
                product_url = EXCLUDED.product_url,
                description = EXCLUDED.description,
                updated_at = EXCLUDED.updated_at,
                metadata = EXCLUDED.metadata
        """, product.product_id, product.product_name, str(product.product_url), 
             product.description, product.updated_at, json.dumps(product.metadata))
    
    async def _save_media(self, conn, media: MediaSchema):
        """Save or update media."""
        dimensions_json = json.dumps(media.dimensions.dict()) if media.dimensions else None
        
        await conn.execute("""
            INSERT INTO agar_media 
            (media_id, product_id, media_type, media_format, media_url, 
             sequence_order, alt_text, dimensions, file_size_kb, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (media_id) DO UPDATE SET
                media_type = EXCLUDED.media_type,
                media_format = EXCLUDED.media_format,
                media_url = EXCLUDED.media_url,
                sequence_order = EXCLUDED.sequence_order,
                alt_text = EXCLUDED.alt_text,
                dimensions = EXCLUDED.dimensions,
                file_size_kb = EXCLUDED.file_size_kb,
                metadata = EXCLUDED.metadata
        """, media.media_id, media.product_id, media.media_type.value, 
             media.media_format.value, str(media.media_url), media.sequence_order,
             media.alt_text, dimensions_json, media.file_size_kb, json.dumps(media.metadata))
    
    async def _save_document(self, conn, document: DocumentSchema):
        """Save or update document."""
        await conn.execute("""
            INSERT INTO agar_documents 
            (document_id, product_id, document_type, document_name, document_url, 
             version, uploaded_at, file_size_kb, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (document_id) DO UPDATE SET
                document_type = EXCLUDED.document_type,
                document_name = EXCLUDED.document_name,
                document_url = EXCLUDED.document_url,
                version = EXCLUDED.version,
                uploaded_at = EXCLUDED.uploaded_at,
                file_size_kb = EXCLUDED.file_size_kb,
                metadata = EXCLUDED.metadata
        """, document.document_id, document.product_id, document.document_type.value,
             document.document_name, str(document.document_url), document.version,
             document.uploaded_at, document.file_size_kb, json.dumps(document.metadata))
    
    async def _save_category(self, conn, category: CategorySchema):
        """Save or update category."""
        await conn.execute("""
            INSERT INTO agar_categories 
            (category_id, category_name, parent_category_id, description, slug, level, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (category_id) DO UPDATE SET
                category_name = EXCLUDED.category_name,
                parent_category_id = EXCLUDED.parent_category_id,
                description = EXCLUDED.description,
                slug = EXCLUDED.slug,
                level = EXCLUDED.level,
                metadata = EXCLUDED.metadata
        """, category.category_id, category.category_name, category.parent_category_id,
             category.description, category.slug, category.level, json.dumps(category.metadata))
    
    async def _save_product_category(self, conn, relation: ProductCategoryRelation):
        """Save or update product-category relationship."""
        await conn.execute("""
            INSERT INTO agar_product_categories (product_id, category_id, is_primary)
            VALUES ($1, $2, $3)
            ON CONFLICT (product_id, category_id) DO UPDATE SET
                is_primary = EXCLUDED.is_primary
        """, relation.product_id, relation.category_id, relation.primary)
    
    async def get_products(self, page: int = 1, limit: int = 20, 
                          category: str = None, search: str = None) -> List[Dict[str, Any]]:
        """Get products with optional filtering."""
        offset = (page - 1) * limit
        
        query = "SELECT * FROM agar_products"
        params = []
        where_clauses = []
        
        if search:
            where_clauses.append("(product_name ILIKE $1 OR description ILIKE $1)")
            params.append(f"%{search}%")
        
        if category:
            where_clauses.append("""
                product_id IN (
                    SELECT pc.product_id FROM agar_product_categories pc
                    JOIN agar_categories c ON pc.category_id = c.category_id
                    WHERE c.category_name ILIKE $2
                )
            """)
            params.append(f"%{category}%")
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += f" ORDER BY updated_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_product_with_relations(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product with all related media, documents, and categories."""
        async with self.pool.acquire() as conn:
            # Get product
            product = await conn.fetchrow(
                "SELECT * FROM agar_products WHERE product_id = $1", product_id
            )
            
            if not product:
                return None
            
            # Get related data
            media = await conn.fetch(
                "SELECT * FROM agar_media WHERE product_id = $1 ORDER BY sequence_order", 
                product_id
            )
            
            documents = await conn.fetch(
                "SELECT * FROM agar_documents WHERE product_id = $1 ORDER BY document_type", 
                product_id
            )
            
            categories = await conn.fetch("""
                SELECT c.* FROM agar_categories c
                JOIN agar_product_categories pc ON c.category_id = pc.category_id
                WHERE pc.product_id = $1
                ORDER BY pc.is_primary DESC, c.category_name
            """, product_id)
            
            return {
                'product': dict(product),
                'media': [dict(m) for m in media],
                'documents': [dict(d) for d in documents],
                'categories': [dict(c) for c in categories]
            }
    
    async def get_job_status(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get scraping job status."""
        async with self.pool.acquire() as conn:
            job = await conn.fetchrow(
                "SELECT * FROM agar_scraping_jobs WHERE job_id = $1", job_id
            )
            return dict(job) if job else None
    
    async def get_last_successful_job(self) -> Optional[Dict[str, Any]]:
        """Get the most recent successful scraping job."""
        async with self.pool.acquire() as conn:
            job = await conn.fetchrow("""
                SELECT * FROM agar_scraping_jobs 
                WHERE status = 'completed' 
                ORDER BY completed_at DESC 
                LIMIT 1
            """)
            return dict(job) if job else None
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
