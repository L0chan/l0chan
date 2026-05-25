import re
import os

base_dir = r"d:\NearbyPriceFinder"
customer_html_path = os.path.join(base_dir, "frontend", "templates", "customer.html")
global_css_path = os.path.join(base_dir, "frontend", "static", "global.css")

with open(customer_html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the first style block (which is the massive one)
style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)

if style_match:
    css_content = style_match.group(1).strip()
    
    # Save to global.css
    with open(global_css_path, "w", encoding="utf-8") as f:
        f.write(css_content)
    
    # Remove from customer.html and add link tag
    link_tag = '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'global.css\') }}">'
    new_content = content[:style_match.start()] + link_tag + content[style_match.end():]
    
    with open(customer_html_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Extracted {len(css_content)} bytes to global.css")
else:
    print("No <style> block found!")
