import re
from bs4 import BeautifulSoup

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    # Remove HTML tags
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
