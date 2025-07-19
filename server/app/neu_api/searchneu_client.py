import httpx
import os
from typing import List, Dict, Any, Optional
import redis
import json
from app.config import settings


class SearchNEUClient:
    def __init__(self):
        self.base_url = settings.nu_banner_base_url
        self.redis_client = redis.Redis.from_url(settings.redis_url)
        self.session_cookies = {}

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        cookies: Dict[str, str] = None,
    ) -> Any:
        """Make HTTP request with error handling"""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                url = f"{self.base_url}{endpoint}"

                # Set default headers
                default_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                if headers:
                    default_headers.update(headers)

                if method.upper() == "GET":
                    response = await client.get(
                        url, params=params, headers=default_headers, cookies=cookies
                    )
                elif method.upper() == "POST":
                    if data:
                        # For form data
                        response = await client.post(
                            url,
                            data=data,
                            headers={
                                **default_headers,
                                "Content-Type": "application/x-www-form-urlencoded",
                            },
                            cookies=cookies,
                        )
                    else:
                        response = await client.post(
                            url, headers=default_headers, cookies=cookies
                        )

                response.raise_for_status()

                # Store session cookies for future requests
                if response.cookies:
                    self.session_cookies.update(dict(response.cookies))

                # Try to parse as JSON, otherwise return text
                try:
                    return response.json()
                except:
                    return response.text

            except httpx.HTTPStatusError as e:
                raise Exception(
                    f"NU Banner API error: {e.response.status_code} - {e.response.text}"
                )
            except Exception as e:
                raise Exception(f"NU Banner API request failed: {str(e)}")

    async def _get_cached_or_fetch(
        self, cache_key: str, fetch_func, cache_ttl: int = 3600
    ):
        """Get data from cache or fetch from API"""
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            try:
                return json.loads(cached_data)
            except:
                # If cached data is not JSON, return as string
                return cached_data.decode("utf-8")

        data = await fetch_func()

        # Cache the data (handle both JSON and string responses)
        if isinstance(data, (dict, list)):
            self.redis_client.setex(cache_key, cache_ttl, json.dumps(data))
        else:
            self.redis_client.setex(cache_key, cache_ttl, str(data))

        return data

    async def get_terms(
        self, offset: int = 1, max_results: int = 20, search_term: str = ""
    ) -> List[Dict[str, Any]]:
        """Get available terms/semesters"""
        cache_key = f"terms:{offset}:{max_results}:{search_term}"

        async def fetch_terms():
            params = {"offset": offset, "max": max_results}
            if search_term:
                params["searchTerm"] = search_term

            return await self._make_request(
                "GET", "/classSearch/getTerms", params=params
            )

        return await self._get_cached_or_fetch(cache_key, fetch_terms, cache_ttl=7200)

    async def get_subjects(
        self, term: str, offset: int = 1, max_results: int = 100, search_term: str = ""
    ) -> List[Dict[str, Any]]:
        """Get subjects for a specific term"""
        cache_key = f"subjects:{term}:{offset}:{max_results}:{search_term}"

        async def fetch_subjects():
            params = {"term": term, "offset": offset, "max": max_results}
            if search_term:
                params["searchTerm"] = search_term

            return await self._make_request(
                "GET", "/classSearch/get_subject", params=params
            )

        return await self._get_cached_or_fetch(cache_key, fetch_subjects)

    async def declare_term(self, term: str) -> Dict[str, Any]:
        """Declare which term we're interested in (required before searching)"""
        data = {
            "term": term,
            "studyPath": "",
            "studyPathText": "",
            "startDatepicker": "",
            "endDatepicker": "",
        }

        return await self._make_request("POST", "/term/search", data=data)

    async def search_courses(
        self,
        term: str,
        subject: str = "",
        course_number: str = "",
        page_offset: int = 0,
        page_max_size: int = 20,
        sort_column: str = "subjectDescription",
        sort_direction: str = "asc",
    ) -> Dict[str, Any]:
        """Search for courses (requires declaring term first)"""
        cache_key = (
            f"courses:{term}:{subject}:{course_number}:{page_offset}:{page_max_size}"
        )

        async def fetch_courses():
            # First declare the term
            await self.declare_term(term)

            # Then search for courses
            params = {
                "txt_term": term,
                "pageOffset": page_offset,
                "pageMaxSize": page_max_size,
                "sortColumn": sort_column,
                "sortDirection": sort_direction,
            }

            if subject:
                params["txt_subject"] = subject
            if course_number:
                params["txt_courseNumber"] = course_number

            return await self._make_request(
                "GET",
                "/searchResults/searchResults",
                params=params,
                cookies=self.session_cookies,
            )

        return await self._get_cached_or_fetch(cache_key, fetch_courses)

    async def get_faculty_meeting_times(self, term: str, crn: str) -> Dict[str, Any]:
        """Get faculty and meeting times for a specific course section"""
        cache_key = f"meeting_times:{term}:{crn}"

        async def fetch_meeting_times():
            params = {"term": term, "courseReferenceNumber": crn}

            return await self._make_request(
                "GET",
                "/searchResults/getFacultyMeetingTimes",
                params=params,
                cookies=self.session_cookies,
            )

        return await self._get_cached_or_fetch(cache_key, fetch_meeting_times)

    async def get_class_details(self, term: str, crn: str) -> str:
        """Get detailed class information (HTML response)"""
        cache_key = f"class_details:{term}:{crn}"

        async def fetch_details():
            data = {"term": term, "courseReferenceNumber": crn}

            return await self._make_request(
                "POST",
                "/searchResults/getClassDetails",
                data=data,
                cookies=self.session_cookies,
            )

        return await self._get_cached_or_fetch(cache_key, fetch_details)

    async def get_course_description(self, term: str, crn: str) -> str:
        """Get course description (HTML response)"""
        cache_key = f"course_description:{term}:{crn}"

        async def fetch_description():
            data = {"term": term, "courseReferenceNumber": crn}

            return await self._make_request(
                "POST",
                "/searchResults/getCourseDescription",
                data=data,
                cookies=self.session_cookies,
            )

        return await self._get_cached_or_fetch(cache_key, fetch_description)

    async def get_prerequisites(self, term: str, crn: str) -> str:
        """Get prerequisites information (HTML response)"""
        cache_key = f"prerequisites:{term}:{crn}"

        async def fetch_prerequisites():
            data = {"term": term, "courseReferenceNumber": crn}

            return await self._make_request(
                "POST",
                "/searchResults/getSectionPrerequisites",
                data=data,
                cookies=self.session_cookies,
            )

        return await self._get_cached_or_fetch(cache_key, fetch_prerequisites)

    async def get_corequisites(self, term: str, crn: str) -> str:
        """Get corequisites information (HTML response)"""
        cache_key = f"corequisites:{term}:{crn}"

        async def fetch_corequisites():
            data = {"term": term, "courseReferenceNumber": crn}

            return await self._make_request(
                "POST",
                "/searchResults/getCorequisites",
                data=data,
                cookies=self.session_cookies,
            )

        return await self._get_cached_or_fetch(cache_key, fetch_corequisites)

    async def reset_form(self) -> str:
        """Reset the search form to search for different courses"""
        return await self._make_request(
            "POST", "/classSearch/resetDataForm", cookies=self.session_cookies
        )
