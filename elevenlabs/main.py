import os
from fastapi import FastAPI
from firecrawl import FirecrawlApp
from pydantic import BaseModel

app = FastAPI()
# Initialize Firecrawl with your API Key
firecrawl = FirecrawlApp(api_key="fc-db13fe87a60d41eea93582a1999db33b")

class SearchQuery(BaseModel):
    query: str

@app.post("/search")
async def search_the_web(data: SearchQuery):
    # Search the web and get structured markdown back
    search_result = firecrawl.search(
        query=data.query,
        limit=3,
        scrape_options={"formats": ["markdown"]}
    )
    
    # Combine results into a tight context for the agent
    context = ""
    for entry in search_result.get('data', []):
        context += f"Source: {entry['url']}\nContent: {entry['markdown'][:500]}\n---\n"
    
    return {"result": context}