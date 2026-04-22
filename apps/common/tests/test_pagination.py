from unittest.mock import MagicMock

from django.test import TestCase

from apps.common.pagination import StandardPagination


class StandardPaginationTests(TestCase):
    def _build_paginator(self, count=42, number=2, per_page=20):
        pag = StandardPagination()
        pag.page = MagicMock()
        pag.page.paginator.count = count
        pag.page.number = number
        pag.page.paginator.per_page = per_page
        pag.get_next_link = lambda: "http://next"
        pag.get_previous_link = lambda: "http://prev"
        return pag

    def test_response_uses_key_result_not_results(self):
        pag = self._build_paginator()
        response = pag.get_paginated_response([{"id": 1}])
        self.assertIn("result", response.data)
        self.assertNotIn("results", response.data)

    def test_response_contains_all_required_fields(self):
        pag = self._build_paginator(count=42, number=2, per_page=20)
        response = pag.get_paginated_response([{"id": 1}])
        self.assertEqual(response.data["count"], 42)
        self.assertEqual(response.data["page"], 2)
        self.assertEqual(response.data["page_size"], 20)
        self.assertEqual(response.data["next"], "http://next")
        self.assertEqual(response.data["previous"], "http://prev")
        self.assertEqual(response.data["result"], [{"id": 1}])

    def test_default_page_size_is_20(self):
        self.assertEqual(StandardPagination.page_size, 20)

    def test_max_page_size_is_100(self):
        self.assertEqual(StandardPagination.max_page_size, 100)
