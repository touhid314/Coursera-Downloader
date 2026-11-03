"""Regression tests for problems reported in the GitHub issues."""

import json
from unittest import TestCase, mock

import requests

from src.core import extractors
from src.services import general


class PanicException(BaseException):
    """Stands in for pyo3_runtime.PanicException, raised by Rust panics."""


class BrowserCookieTests(TestCase):
    """Issue #13: a Rust panic while reading browser cookies crashed the app."""

    def test_rust_panic_becomes_a_login_error(self):
        reader = mock.Mock(side_effect=PanicException(
            "internal error: entered unreachable code: Got a binrw error"))
        with mock.patch.object(general.rookiepy, "brave", reader, create=True):
            cauth, error = general.loadcauth_with_error("coursera.org", "brave")

        self.assertEqual(cauth, "")
        self.assertIn("Brave", error)
        self.assertIn("embedded browser", error)

    def test_stop_requests_are_not_swallowed(self):
        reader = mock.Mock(side_effect=KeyboardInterrupt)
        with mock.patch.object(general.rookiepy, "firefox", reader, create=True):
            with self.assertRaises(KeyboardInterrupt):
                general.loadcauth_with_error("coursera.org", "firefox")


class PastedCookieTests(TestCase):
    """Issue #14: log in by pasting the CAUTH cookie."""

    def test_accepts_the_usual_ways_of_copying_the_cookie(self):
        for text in ("abc-123_x.y", "  abc-123_x.y\n", '"abc-123_x.y"',
                     "CAUTH=abc-123_x.y", "a=1; CAUTH=abc-123_x.y; b=2"):
            with self.subTest(text=text):
                self.assertEqual(general.normalize_pasted_cauth(text), "abc-123_x.y")

    def test_keeps_base64_padding(self):
        self.assertEqual(general.normalize_pasted_cauth("abc12=="), "abc12==")

    def test_rejects_text_that_is_not_the_cookie(self):
        for text in ("", "   ", "CSRF3-Token=abc", "a=1; b=2", "two words"):
            with self.subTest(text=text):
                self.assertEqual(general.normalize_pasted_cauth(text), "")

    def test_manual_login_is_offered_and_saved_separately(self):
        self.assertIn(general.MANUAL_LOGIN, general.LOGIN_METHODS)
        self.assertNotEqual(general.SAVED_AUTH_ACCOUNTS[general.MANUAL_LOGIN],
                            general.SAVED_AUTH_ACCOUNTS[general.EMBEDDED_LOGIN])

        vault = {}
        with mock.patch.object(general.keyring, "set_password",
                               lambda service, account, value: vault.__setitem__(account, value)), \
             mock.patch.object(general.keyring, "get_password",
                               lambda service, account: vault.get(account)), \
             mock.patch.object(general.keyring, "delete_password",
                               lambda service, account: vault.pop(account)):
            self.assertTrue(general.save_auth(general.MANUAL_LOGIN, "pasted"))
            self.assertTrue(general.save_embedded_auth("embedded"))
            self.assertEqual(general.load_saved_auth(general.MANUAL_LOGIN), "pasted")
            self.assertEqual(general.load_embedded_auth(), "embedded")

            general.clear_saved_auth(general.MANUAL_LOGIN)
            self.assertEqual(general.load_saved_auth(general.MANUAL_LOGIN), "")
            self.assertEqual(general.load_embedded_auth(), "embedded")


class SubtitleLanguageTests(TestCase):
    """Issue #16: the saved subtitle language must come back as the same choice."""

    def test_every_language_round_trips_through_its_saved_code(self):
        mapping = general.LANG_NAME_TO_CODE_MAPPING
        for name, code in mapping.items():
            with self.subTest(name=name):
                # main_window saves the code and shows the name for the saved code.
                restored = next(k for k, v in mapping.items() if v == code)
                self.assertEqual(restored, name)

    def test_codes(self):
        mapping = general.LANG_NAME_TO_CODE_MAPPING
        self.assertEqual(mapping["English"], "en")
        self.assertEqual(mapping["Malay"], "ms")
        self.assertEqual(mapping["Malayalam"], "ml")


def syllabus(*items):
    """A course syllabus with one module and one section holding the items."""
    return json.dumps({
        "elements": [{"id": "course-id"}],
        "linked": {
            "onDemandCourseMaterialModules.v1": [
                {"id": "m1", "name": "Week 1", "slug": "week-1", "lessonIds": ["l1"]}],
            "onDemandCourseMaterialLessons.v1": [
                {"id": "l1", "name": "Section", "slug": "section",
                 "itemIds": [item_id for item_id, _ in items]}],
            "onDemandCourseMaterialItems.v2": [
                {"id": item_id, "name": item_id, "slug": item_id,
                 "contentSummary": {"typeName": type_name},
                 "lessonId": "l1", "moduleId": "m1"}
                for item_id, type_name in items],
        },
    })


class SyllabusTests(TestCase):
    def parse(self, page, course):
        extractor = extractors.CourseraExtractor(session=None)
        with mock.patch.object(extractors, "CourseraOnDemand", return_value=course), \
             mock.patch.object(extractors.OnDemandCourseMaterialItemsV1, "create"):
            return extractor._parse_on_demand_syllabus(
                "course", page, download_quizzes=True, download_notebooks=True)

    def fake_course(self):
        course = mock.Mock()
        course.extract_references_poll.return_value = []
        return course

    def test_one_failing_item_does_not_stop_the_course(self):
        """Issue #4: an unexpected error in one lecture ended the whole download."""
        course = self.fake_course()

        def lecture_links(course_id, video_id, *args):
            if video_id == "broken":
                raise KeyError("sources")
            return {"mp4": [("https://example.com/%s.mp4" % video_id, "")]}

        course.extract_links_from_lecture.side_effect = lecture_links
        error_occurred, modules = self.parse(
            syllabus(("first", "lecture"), ("broken", "lecture"),
                     ("prompt", "discussionPrompt"), ("last", "lecture")),
            course)

        self.assertTrue(error_occurred)
        lectures = [slug for slug, _ in modules[0][1][0][1]]
        self.assertEqual(lectures, ["first", "last"])

    def test_connection_errors_still_stop_the_course(self):
        course = self.fake_course()
        course.extract_links_from_lecture.side_effect = requests.exceptions.ConnectionError()
        with self.assertRaises(requests.exceptions.ConnectionError):
            self.parse(syllabus(("a", "lecture"), ("b", "lecture")), course)

    def test_skipped_quizzes_are_counted_and_reported(self):
        """Issue #10: quizzes and graded assignments were skipped silently."""
        course = self.fake_course()
        course.extract_links_from_lecture.return_value = {
            "mp4": [("https://example.com/v.mp4", "")]}
        events = []
        with mock.patch.object(extractors.download_progress, "emit",
                               lambda event, **fields: events.append((event, fields))):
            self.parse(syllabus(("video", "lecture"), ("graded", "staffGraded"),
                                ("practice", "ungradedAssignment")), course)

        self.assertIn(("assessments_skipped", {"count": 2}), events)


class VideoResolutionTests(TestCase):
    """Issue #18: 1080p videos."""

    @staticmethod
    def videos(*resolutions):
        from src.core.api import VideosV1
        return VideosV1.from_json({"sources": {"byResolution": {
            r: {"mp4VideoUrl": "https://example.com/%s.mp4" % r} for r in resolutions}}})

    def test_best_is_the_highest_resolution(self):
        # As text, "1080p" sorts below "240p"; the best must still be 1080p.
        videos = self.videos("240p", "360p", "540p", "720p", "1080p")
        self.assertEqual(videos.get_best().resolution, "1080p")

    def test_1080p_falls_back_to_720p_when_missing(self):
        videos = self.videos("240p", "360p", "540p", "720p")
        self.assertNotIn("1080p", videos)
        self.assertEqual(videos.get_best().resolution, "720p")


class LoginCookieScopeTests(TestCase):
    """PR #20: the CAUTH login cookie was sent to every website, not only Coursera."""

    def cookie_sent_to(self, url):
        from types import SimpleNamespace
        from src.core import coursera_dl
        session = coursera_dl.create_session(SimpleNamespace(
            cookies_cauth="SECRET", browser=None, username=None, password=None))
        return session.prepare_request(requests.Request("GET", url)).headers.get("Cookie")

    def test_sent_to_coursera(self):
        for url in ("https://api.coursera.org/api/x", "https://www.coursera.org/learn/x"):
            with self.subTest(url=url):
                self.assertEqual(self.cookie_sent_to(url), "CAUTH=SECRET")

    def test_not_sent_anywhere_else(self):
        for url in ("https://scrumguides.org/guide.pdf",
                    "https://d3c33hcgiwev3.cloudfront.net/video.mp4",
                    "https://evil-coursera.org/",
                    "http://www.coursera.org/learn/x"):   # never unencrypted
            with self.subTest(url=url):
                self.assertIsNone(self.cookie_sent_to(url))
