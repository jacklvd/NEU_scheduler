import asyncio
import httpx
from typing import List, Dict, Any, Optional
import json
from app.config import settings


class SearchNEUClient:
    def __init__(self):
        self.base_url = settings.nu_banner_base_url
        from app.redis_client import get_redis_client
        self.redis_client = get_redis_client()
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

                # Set default headers to mimic browser
                default_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                }
                if headers:
                    default_headers.update(headers)

                # Debug logging
                print(f"Making {method} request to: {url}")
                if params:
                    print(f"Params: {params}")
                if data:
                    print(f"Data: {data}")

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

                print(f"Response status: {response.status_code}")
                response.raise_for_status()

                # Store session cookies for future requests
                if response.cookies:
                    self.session_cookies.update(dict(response.cookies))

                # Try to parse as JSON, otherwise return text
                try:
                    result = response.json()
                    print(f"JSON Response received: {type(result)}")
                    return result
                except:
                    text_result = response.text
                    print(f"Text Response received: {len(text_result)} characters")
                    return text_result

            except httpx.HTTPStatusError as e:
                print(f"HTTP Status Error: {e.response.status_code}")
                print(f"Response text: {e.response.text[:500]}...")
                raise Exception(
                    f"NU Banner API error: {e.response.status_code} - {e.response.text[:200]}"
                )
            except Exception as e:
                print(f"Request failed: {str(e)}")
                raise Exception(f"NU Banner API request failed: {str(e)}")

    async def _get_cached_or_fetch(
        self, cache_key: str, fetch_func, cache_ttl: int = 3600
    ):
        """Get data from cache or fetch from API"""
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    try:
                        return json.loads(cached_data)
                    except:
                        return cached_data.decode("utf-8")
            except Exception as e:
                print(f"Cache read error: {e}")

        data = await fetch_func()

        # Cache the data if Redis is available
        if self.redis_client:
            try:
                if isinstance(data, (dict, list)):
                    self.redis_client.setex(cache_key, cache_ttl, json.dumps(data))
                else:
                    self.redis_client.setex(cache_key, cache_ttl, str(data))
            except Exception as e:
                print(f"Cache write error: {e}")

        return data

    async def get_terms(
        self, offset: int = 1, max_results: int = 50, search_term: str = ""
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
        self, term: str, offset: int = 1, max_results: int = 500, search_term: str = ""
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

    async def declare_term(self, term: str) -> bool:
        """Declare which term we're interested in (required before searching)"""
        try:
            data = {
                "term": term,
                "studyPath": "",
                "studyPathText": "",
                "startDatepicker": "",
                "endDatepicker": "",
            }

            result = await self._make_request("POST", "/term/search", data=data)
            print(f"Term declaration result: {result}")
            return True
        except Exception as e:
            print(f"Failed to declare term: {e}")
            return False

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
            try:
                # First declare the term
                print(f"Declaring term: {term}")
                declare_success = await self.declare_term(term)
                if not declare_success:
                    return {
                        "success": False,
                        "data": [],
                        "message": "Failed to declare term",
                    }

                # Small delay to ensure session is established
                await asyncio.sleep(0.5)

                # Then search for courses
                params = {
                    "txt_term": term,
                    "pageOffset": page_offset,
                    "pageMaxSize": page_max_size,
                    "sortColumn": sort_column,
                    "sortDirection": sort_direction,
                }

                if subject:
                    params["txt_subject"] = subject.upper()
                if course_number:
                    params["txt_courseNumber"] = course_number

                print(f"Searching with params: {params}")
                result = await self._make_request(
                    "GET",
                    "/searchResults/searchResults",
                    params=params,
                    cookies=self.session_cookies,
                )

                if isinstance(result, dict):
                    return result
                else:
                    print(f"Unexpected result type: {type(result)}")
                    return {
                        "success": False,
                        "data": [],
                        "message": "Unexpected response format",
                    }

            except Exception as e:
                print(f"Course search error: {e}")
                return {"success": False, "data": [], "message": str(e)}

        return await self._get_cached_or_fetch(cache_key, fetch_courses)

    async def reset_form(self) -> str:
        """Reset the search form to search for different courses"""
        try:
            return await self._make_request(
                "POST", "/classSearch/resetDataForm", cookies=self.session_cookies
            )
        except Exception as e:
            print(f"Reset form error: {e}")
            return "failed"
