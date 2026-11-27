import re

with open(r'C:\Proyectos\inmo_leadflow\app\original_site.html', encoding='utf-8') as f:
    text = f.read()

clean = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.I)
clean = re.sub(r'<style.*?</style>', '', clean, flags=re.DOTALL | re.I)
clean = re.sub(r'<[^>]+>', ' ', clean)
lines = [l.strip() for l in clean.splitlines() if l.strip()]

for l in lines:
    if any(k in l.lower() for k in ['calle', 'avda', 'avenida', 'plaza', 'tel', 'contacto', 'villaviciosa', 'somos', 'experiencia']):
        print(l)
