# Crawl4AI Content Exclusion Guide

Based on the analysis of the webpage sections marked for exclusion (top navigation, product enquiry form, and footer subscription), this guide provides multiple methods to exclude unwanted content using Crawl4AI's powerful filtering capabilities.

## Sections to Exclude (from image analysis)

1. **Top Navigation Bar** - Contains menu items, distributors, contact info
2. **Product Enquiry Form** - Contact form with name, email, questions fields
3. **Footer Subscription** - Email subscription section with newsletter signup

## Method 1: Using `excluded_selector` (Recommended)

The most precise method using CSS selectors to target specific elements:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def scrape_with_excluded_selectors():
    config = CrawlerRunConfig(
        # Exclude specific sections using CSS selectors
        excluded_selector="""
            nav,
            header,
            .product-enquiry,
            .enquiry-form,
            form[class*="enquiry"],
            form[class*="contact"],
            .footer-subscription,
            .newsletter,
            .email-subscription,
            footer form,
            .subscribe
        """,
        # Additional content filtering
        content_filter=PruningContentFilter(threshold=0.5),
        verbose=True
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="your-target-url",
            config=config
        )
        return result.markdown
```

## Method 2: Using `excluded_tags` for Broader Exclusion

Remove entire categories of HTML tags:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def scrape_with_excluded_tags():
    config = CrawlerRunConfig(
        # Remove entire tag types
        excluded_tags=["nav", "footer", "form", "aside", "header"],
        
        # Also remove overlay elements that might contain forms
        remove_overlay_elements=True,
        remove_forms=True,
        
        # Use content filtering for additional noise removal
        content_filter=BM25ContentFilter(bm25_threshold=1.2),
        verbose=True
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="your-target-url", 
            config=config
        )
        return result.markdown
```

## Method 3: Focus on Specific Content with `css_selector`

Instead of excluding, focus only on the main content area:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def scrape_focused_content():
    config = CrawlerRunConfig(
        # Focus only on main content areas
        css_selector="main, article, .product-details, .description, .content",
        
        # Additional filtering
        word_count_threshold=10,
        content_filter=PruningContentFilter(),
        verbose=True
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="your-target-url",
            config=config
        )
        return result.markdown
```

## Method 4: Advanced LLM-Based Content Filtering

Use AI to intelligently remove noise and keep only relevant content:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import LLMContentFilter
from crawl4ai import LLMConfig

async def scrape_with_llm_filtering():
    # Configure LLM for content filtering
    llm_config = LLMConfig(
        provider="openai",  # or your preferred provider
        api_token="your-api-token"
    )
    
    config = CrawlerRunConfig(
        # Use LLM to intelligently filter content
        content_filter=LLMContentFilter(
            llm_config=llm_config,
            instruction="""
            Convert this HTML to clean markdown, focusing on:
            - Product information and descriptions
            - Technical specifications
            - Key benefits and features
            
            Exclude:
            - Navigation menus
            - Contact forms
            - Newsletter signups
            - Footer content
            - Social sharing buttons
            """
        ),
        
        # Remove obvious noise first
        excluded_tags=["script", "style", "nav", "footer"],
        remove_forms=True,
        remove_overlay_elements=True,
        verbose=True
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="your-target-url",
            config=config
        )
        return result.markdown
```

## Method 5: Combined Approach (Most Effective)

Combine multiple exclusion methods for maximum effectiveness:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import BM25ContentFilter

async def comprehensive_content_filtering():
    config = CrawlerRunConfig(
        # 1. Remove unwanted tags entirely
        excluded_tags=["script", "style", "nav", "header", "aside"],
        
        # 2. Remove specific elements by CSS selector
        excluded_selector="""
            form,
            .enquiry,
            .contact-form,
            .newsletter,
            .subscription,
            .social-share,
            .breadcrumb,
            .sidebar,
            footer
        """,
        
        # 3. Remove forms and overlays
        remove_forms=True,
        remove_overlay_elements=True,
        
        # 4. Apply intelligent content filtering
        content_filter=BM25ContentFilter(
            bm25_threshold=1.0,
            use_stemming=True
        ),
        
        # 5. Set minimum word count threshold
        word_count_threshold=5,
        
        # 6. Focus on main content if possible
        # css_selector="main, article, .product-content",  # Uncomment if you know the main content selector
        
        verbose=True
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="your-target-url",
            config=config
        )
        return result.markdown
```

## Built-in Exclusion Patterns

Crawl4AI's content filters automatically exclude common noise patterns:

- **Navigation elements**: `nav`, `header`, `aside`
- **Forms**: `form`, `input`, `textarea`
- **Scripts and styles**: `script`, `style`
- **Social elements**: Elements with classes containing "social", "share"
- **Advertising**: Elements with classes containing "ads", "advert", "promo"
- **Comments**: Elements with classes containing "comment"

## Specific Selectors for Your Use Case

Based on the image analysis, here are targeted selectors:

```python
# For the specific webpage shown in the image
specific_exclusions = """
    /* Top navigation */
    nav, header, 
    .top-menu, .main-menu,
    
    /* Product enquiry form */
    .product-enquiry,
    form[action*="enquiry"],
    .enquiry-section,
    
    /* Footer subscription */
    .footer-subscription,
    .email-subscription,
    footer form,
    .newsletter-signup,
    
    /* Additional common elements */
    .breadcrumb,
    .social-links,
    .share-buttons
"""

config = CrawlerRunConfig(
    excluded_selector=specific_exclusions,
    content_filter=PruningContentFilter(threshold=0.5)
)
```

## Testing and Validation

To test your exclusion settings:

```python
async def test_exclusions():
    config = CrawlerRunConfig(
        excluded_selector="nav, footer, form",
        verbose=True  # Enable detailed logging
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="your-target-url",
            config=config
        )
        
        # Check what was excluded
        print("Original HTML length:", len(result.html))
        print("Cleaned HTML length:", len(result.cleaned_html))
        print("Markdown length:", len(result.markdown))
        
        # Save for manual inspection
        with open("cleaned_result.md", "w") as f:
            f.write(result.markdown)
        
        return result
```

## Performance Considerations

1. **Order matters**: Apply exclusions in order of efficiency:
   - `excluded_tags` (fastest)
   - `excluded_selector` (fast)  
   - `content_filter` (slower but more intelligent)

2. **LLM filtering**: Most powerful but slowest and costs API tokens

3. **CSS selector precision**: More specific selectors are faster than broad ones

## Summary

**Yes, it's absolutely possible** to exclude the sections marked with red lines in your image using Crawl4AI's extensive content filtering capabilities. The framework provides multiple complementary approaches:

- **Tag-based exclusion** for removing entire element types
- **CSS selector exclusion** for precise element targeting  
- **Content-aware filtering** using BM25, pruning, or LLM strategies
- **Built-in noise removal** for common unwanted patterns

The recommended approach is to combine multiple methods for maximum effectiveness while balancing performance needs.
