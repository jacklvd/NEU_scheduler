from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any, Optional


class HTMLParser:
    """Parser for NU Banner HTML responses"""

    @staticmethod
    def parse_course_description(html: str) -> str:
        """Extract course description from HTML"""
        if not html or "No" in html and "available" in html:
            return ""

        # Remove HTML tags and clean up
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text().strip()
        return text

    @staticmethod
    def parse_prerequisites(html: str) -> List[Dict[str, Any]]:
        """Parse prerequisites table from HTML"""
        if not html or "No" in html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        prereqs = []

        # Find the prerequisites table
        table = soup.find("table", class_="basePreqTable")
        if not table:
            return []

        rows = table.find("tbody").find_all("tr") if table.find("tbody") else []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 6:
                prereq = {
                    "connector": cells[0].get_text().strip(),  # And/Or
                    "subject": cells[4].get_text().strip(),
                    "course_number": cells[5].get_text().strip(),
                    "level": cells[6].get_text().strip() if len(cells) > 6 else "",
                    "grade": cells[7].get_text().strip() if len(cells) > 7 else "",
                }
                if prereq["subject"] and prereq["course_number"]:
                    prereqs.append(prereq)

        return prereqs

    @staticmethod
    def parse_corequisites(html: str) -> List[Dict[str, Any]]:
        """Parse corequisites table from HTML"""
        if not html or "No" in html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        coreqs = []

        table = soup.find("table")
        if not table:
            return []

        rows = table.find("tbody").find_all("tr") if table.find("tbody") else []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                coreq = {
                    "subject": cells[0].get_text().strip() if len(cells) > 0 else "",
                    "course_number": (
                        cells[1].get_text().strip() if len(cells) > 1 else ""
                    ),
                    "title": cells[2].get_text().strip() if len(cells) > 2 else "",
                    "crn": (
                        cells[0].get_text().strip() if len(cells) == 5 else ""
                    ),  # 5 column format
                }
                if coreq["subject"] and coreq["course_number"]:
                    coreqs.append(coreq)

        return coreqs

    @staticmethod
    def parse_class_details(html: str) -> Dict[str, Any]:
        """Parse class details from HTML"""
        if not html:
            return {}

        soup = BeautifulSoup(html, "html.parser")
        details = {}

        # Extract key-value pairs
        spans = soup.find_all("span", class_="status-bold")
        for span in spans:
            key = span.get_text().replace(":", "").strip()
            next_sibling = span.next_sibling

            if next_sibling:
                if hasattr(next_sibling, "get_text"):
                    value = next_sibling.get_text().strip()
                else:
                    value = str(next_sibling).strip()
                details[key.lower().replace(" ", "_")] = value

        return details
