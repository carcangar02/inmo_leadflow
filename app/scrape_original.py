import urllib.request
import ssl
import re
import json

url = "https://www.consultingvillaviciosa.com"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        
    # Extract images
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html, re.I)
    
    # Extract phone numbers, emails, addresses
    phones = re.findall(r'(?:tel:|\+?34\s?)?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}', html)
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
    
    # Save raw html for inspection
    with open(r'C:\Proyectos\inmo_leadflow\app\original_site.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"Scraped {len(html)} bytes")
    print(f"Images found: {len(imgs)}")
    print("Sample images:", imgs[:10])
    print("Sample links:", links[:10])
    print("Phones:", set(phones))
    print("Emails:", set(emails))
except Exception as e:
    print("Error scraping original site:", e)
