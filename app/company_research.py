import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re


class CompanyResearcher:
    def __init__(self, llm):
        self.llm = llm
    
    def extract_company_domain(self, job_url):
        """Extract company domain from job URL"""
        parsed = urlparse(job_url)
        domain = parsed.netloc.replace('www.', '')
        # Remove common job board domains
        if 'jobs.' in domain:
            domain = domain.replace('jobs.', '')
        return domain
    
    def get_company_info(self, domain):
        """Scrape basic company info from website"""
        try:
            response = requests.get(f"https://{domain}/about", timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Get first few paragraphs
                paragraphs = soup.find_all('p')
                text = ' '.join([p.get_text() for p in paragraphs[:3]])
                return text[:500]  # Limit to 500 chars
        except:
            pass
        return None
    
    def get_recent_news(self, company_name):
        """Get recent news using Google News RSS (free)"""
        try:
            query = company_name.replace(' ', '+')
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            response = requests.get(rss_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item', limit=3)
                news = [item.find('title').text for item in items if item.find('title')]
                return news
        except:
            pass
        return []
    
    def research_company(self, job_url):
        """Main research function"""
        domain = self.extract_company_domain(job_url)
        company_name = domain.split('.')[0].title()
        
        # Get company info
        about_text = self.get_company_info(domain)
        
        # Get recent news
        news = self.get_recent_news(company_name)
        
        # Generate insights using LLM
        research_data = {
            'company_name': company_name,
            'domain': domain,
            'about': about_text,
            'recent_news': news
        }
        
        if about_text or news:
            insights = self.generate_insights(research_data)
            return insights
        
        return None
    
    def generate_insights(self, research_data):
        """Use LLM to generate personalized insights"""
        prompt = f"""
        Based on this company research, generate 2-3 brief, specific points that could personalize a cold email:
        
        Company: {research_data['company_name']}
        About: {research_data['about'] or 'Not available'}
        Recent News: {', '.join(research_data['recent_news']) if research_data['recent_news'] else 'Not available'}
        
        Return only the key points as a brief paragraph (max 100 words). Focus on recent achievements, growth, or relevant context.
        """
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except:
            return None
