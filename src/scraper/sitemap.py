import xml.etree.ElementTree as ET

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def sitemap_locs(xml: bytes) -> list[str]:
    root = ET.fromstring(xml)
    return [el.text.strip() for el in root.iterfind(".//sm:loc", NS) if el.text]