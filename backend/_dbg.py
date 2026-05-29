[print(l.attrib.get("href",""), (l.text[:30] if l.text else "empty")) for l in (links[:15] if links else [])])  
