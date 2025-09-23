"""
Document handling module for Agar product catalog.

This module handles the extraction and processing of documents (PDFs, datasheets, etc.)
from product pages, including type detection and metadata extraction.
"""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime

from .schemas import DocumentSchema, DocumentType, ProductSchema, ScrapingConfig
from .utils import generate_document_id, detect_document_type, clean_text, extract_version_from_filename


class DocumentHandler:
    """
    Handles document extraction and processing for product pages.
    """
    
    def __init__(self, config: ScrapingConfig):
        """
        Initialize the DocumentHandler.
        
        Args:
            config: Scraping configuration
        """
        self.config = config
    
    def extract_documents_from_product(self, product: ProductSchema, raw_extracted_data: Dict[str, Any]) -> List[DocumentSchema]:
        """
        Extract document files from a product's raw extracted data.
        
        Args:
            product: Product schema object
            raw_extracted_data: Raw data extracted from the product page
            
        Returns:
            List of DocumentSchema objects
        """
        if not self.config.include_documents:
            return []
        
        documents = []
        
        # Extract document URLs and their associated text
        attachment_links = raw_extracted_data.get("attachment_links", [])
        attachment_texts = raw_extracted_data.get("attachment_texts", [])
        
        # Normalize to lists
        if isinstance(attachment_links, str):
            attachment_links = [attachment_links]
        if isinstance(attachment_texts, str):
            attachment_texts = [attachment_texts]
        
        # Ensure attachment_texts list is same length as attachment_links
        while len(attachment_texts) < len(attachment_links):
            attachment_texts.append("")
        
        # Process each document link
        for doc_url, link_text in zip(attachment_links, attachment_texts):
            if not doc_url:
                continue
            
            document = self._create_document_schema(product, doc_url, link_text)
            if document:
                documents.append(document)
        
        # Also look for documents in the product content/description
        content_documents = self._extract_documents_from_content(product, raw_extracted_data)
        documents.extend(content_documents)
        
        # Remove duplicates based on URL
        documents = self._filter_duplicate_documents(documents)
        
        if self.config.verbose and documents:
            print(f"  Found {len(documents)} documents for product: {product.product_name}")
        
        return documents
    
    def _create_document_schema(self, product: ProductSchema, doc_url: str, link_text: str = "") -> Optional[DocumentSchema]:
        """
        Create a DocumentSchema from URL and link text.
        
        Args:
            product: Product schema object
            doc_url: URL of the document
            link_text: Text of the link pointing to the document
            
        Returns:
            DocumentSchema object or None if creation fails
        """
        try:
            # Make absolute URL
            if not doc_url.startswith('http'):
                doc_url = urljoin(str(product.product_url), doc_url)
            
            # Generate document ID
            document_id = generate_document_id(product.product_id, doc_url)
            
            # Extract filename from URL
            parsed_url = urlparse(doc_url)
            filename = parsed_url.path.split('/')[-1] if parsed_url.path else "document"
            
            # Detect document type
            doc_type = detect_document_type(doc_url, link_text)
            
            # Create document name from link text or filename
            document_name = clean_text(link_text) if link_text else filename
            if not document_name:
                document_name = f"{doc_type} Document"
            
            # Extract version information
            version = extract_version_from_filename(filename) or extract_version_from_filename(link_text)
            
            # Try to extract upload date from link text or URL
            uploaded_at = self._extract_upload_date(link_text, doc_url)
            
            # Create DocumentSchema
            document = DocumentSchema(
                document_id=document_id,
                product_id=product.product_id,
                document_type=DocumentType(doc_type),
                document_name=document_name,
                document_url=doc_url,
                version=version,
                uploaded_at=uploaded_at,
                metadata={
                    "link_text": link_text,
                    "filename": filename,
                    "extraction_source": "attachment_links"
                }
            )
            
            return document
            
        except Exception as e:
            if self.config.verbose:
                print(f"  Error creating document schema for {doc_url}: {e}")
            return None
    
    def _extract_documents_from_content(self, product: ProductSchema, raw_data: Dict[str, Any]) -> List[DocumentSchema]:
        """
        Extract documents mentioned in product content or description.
        
        Args:
            product: Product schema object
            raw_data: Raw extracted data
            
        Returns:
            List of DocumentSchema objects
        """
        documents = []
        
        # Content sections to search
        content_sections = [
            raw_data.get("product_content", ""),
            raw_data.get("product_description", ""),
        ]
        
        # PDF link patterns
        pdf_patterns = [
            r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
            r'(https?://[^\s<>"{}|\\^`\[\]]*\.pdf)',
            r'(www\.[^\s<>"{}|\\^`\[\]]*\.pdf)',
        ]
        
        for content in content_sections:
            if not content:
                continue
            
            for pattern in pdf_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    doc_url = match.group(1)
                    
                    # Try to find context text around the URL
                    start_pos = max(0, match.start() - 100)
                    end_pos = min(len(content), match.end() + 100)
                    context = content[start_pos:end_pos]
                    
                    # Clean up context to get likely link text
                    link_text = self._extract_link_text_from_context(context, doc_url)
                    
                    document = self._create_document_schema(product, doc_url, link_text)
                    if document:
                        # Mark as extracted from content
                        document.metadata["extraction_source"] = "product_content"
                        documents.append(document)
        
        return documents
    
    def _extract_link_text_from_context(self, context: str, doc_url: str) -> str:
        """
        Extract likely link text from context surrounding a document URL.
        
        Args:
            context: Text context containing the URL
            doc_url: Document URL
            
        Returns:
            Extracted link text or empty string
        """
        # Look for text patterns that often indicate link text
        text_patterns = [
            r'<a[^>]*>[^<]*(?=' + re.escape(doc_url) + ')',
            r'>([^<]*)</a>',
            r'title=["\']([^"\']*)["\']',
            r'alt=["\']([^"\']*)["\']'
        ]
        
        for pattern in text_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                link_text = clean_text(match.group(1))
                if link_text and len(link_text) > 2:
                    return link_text
        
        return ""
    
    def _extract_upload_date(self, link_text: str, doc_url: str) -> Optional[datetime]:
        """
        Try to extract upload/creation date from link text or URL.
        
        Args:
            link_text: Text of the link
            doc_url: Document URL
            
        Returns:
            Datetime object if date found, None otherwise
        """
        # Date patterns to look for
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{1,2}/\d{1,2}/\d{2})',  # M/D/YY
            r'(\d{4}\d{2}\d{2})',  # YYYYMMDD
            r'(\w+ \d{1,2}, \d{4})',  # Month DD, YYYY
        ]
        
        search_text = f"{link_text} {doc_url}"
        
        for pattern in date_patterns:
            match = re.search(pattern, search_text)
            if match:
                date_str = match.group(1)
                try:
                    # Try different date parsing approaches
                    if '-' in date_str:
                        return datetime.strptime(date_str, '%Y-%m-%d')
                    elif '/' in date_str:
                        # Try different formats
                        for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%m/%d/%y', '%d/%m/%y']:
                            try:
                                return datetime.strptime(date_str, fmt)
                            except ValueError:
                                continue
                    elif date_str.isdigit() and len(date_str) == 8:
                        return datetime.strptime(date_str, '%Y%m%d')
                    else:
                        # Try parsing month name format
                        try:
                            return datetime.strptime(date_str, '%B %d, %Y')
                        except ValueError:
                            try:
                                return datetime.strptime(date_str, '%b %d, %Y')
                            except ValueError:
                                pass
                                
                except ValueError:
                    continue
        
        return None
    
    def _filter_duplicate_documents(self, documents: List[DocumentSchema]) -> List[DocumentSchema]:
        """
        Filter out duplicate documents based on URL.
        
        Args:
            documents: List of documents
            
        Returns:
            Filtered list without duplicates
        """
        seen_urls = set()
        filtered_documents = []
        
        for document in documents:
            doc_url_str = str(document.document_url)
            if doc_url_str not in seen_urls:
                seen_urls.add(doc_url_str)
                filtered_documents.append(document)
            elif self.config.verbose:
                print(f"  Filtering duplicate document: {doc_url_str}")
        
        return filtered_documents
    
    def group_documents_by_type(self, documents: List[DocumentSchema]) -> Dict[str, List[DocumentSchema]]:
        """
        Group documents by their type.
        
        Args:
            documents: List of documents
            
        Returns:
            Dictionary mapping document types to lists of documents
        """
        grouped = {}
        
        for document in documents:
            doc_type = document.document_type
            if doc_type not in grouped:
                grouped[doc_type] = []
            grouped[doc_type].append(document)
        
        return grouped
    
    def sort_documents_by_version(self, documents: List[DocumentSchema]) -> List[DocumentSchema]:
        """
        Sort documents by version number (highest first).
        
        Args:
            documents: List of documents
            
        Returns:
            Sorted list of documents
        """
        def version_key(doc):
            if not doc.version:
                return (0, 0, 0)  # No version goes to bottom
            
            try:
                # Parse version string like "1.2.3" into tuple (1, 2, 3)
                parts = [int(x) for x in doc.version.split('.')]
                # Pad to 3 parts for consistent sorting
                while len(parts) < 3:
                    parts.append(0)
                return tuple(parts[:3])
            except (ValueError, AttributeError):
                return (0, 0, 0)
        
        return sorted(documents, key=version_key, reverse=True)
    
    def get_latest_document_by_type(self, documents: List[DocumentSchema], doc_type: str) -> Optional[DocumentSchema]:
        """
        Get the latest version of a document by type.
        
        Args:
            documents: List of documents
            doc_type: Document type to filter by
            
        Returns:
            Latest document of specified type or None
        """
        type_documents = [doc for doc in documents if doc.document_type == doc_type]
        if not type_documents:
            return None
        
        sorted_docs = self.sort_documents_by_version(type_documents)
        return sorted_docs[0] if sorted_docs else None
