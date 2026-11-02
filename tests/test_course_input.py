from unittest import TestCase

from src.services.general import parse_course_input


class CourseInputTests(TestCase):
    def test_bare_course_slug(self):
        self.assertEqual(parse_course_input("machine-learning"), ("machine-learning", False))

    def test_course_url(self):
        self.assertEqual(
            parse_course_input("https://www.coursera.org/learn/model-thinking/home/week/1"),
            ("model-thinking", False),
        )

    def test_specialization_url(self):
        self.assertEqual(
            parse_course_input("https://www.coursera.org/specializations/deep-learning"),
            ("deep-learning", True),
        )

    def test_invalid_input(self):
        self.assertEqual(parse_course_input("not a Coursera URL"), ("", False))
