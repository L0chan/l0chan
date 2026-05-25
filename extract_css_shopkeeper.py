import re
import os

base_dir = r"d:\NearbyPriceFinder"
shopkeeper_html_path = os.path.join(base_dir, "frontend", "templates", "shopkeeper.html")

with open(shopkeeper_html_path, "r", encoding="utf-8") as f:
    content = f.read()

style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)

if style_match:
    link_tag = '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'global.css\') }}">'
    new_content = content[:style_match.start()] + link_tag + content[style_match.end():]
    
    with open(shopkeeper_html_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Cleaned shopkeeper.html")
else:
    print("No <style> block found in shopkeeper.html!")
