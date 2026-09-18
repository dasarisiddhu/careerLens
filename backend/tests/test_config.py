import unittest
from config import settings, Settings


class ConfigTests(unittest.TestCase):
    def test_settings_loads_successfully(self):
        self.assertIsNotNone(settings)
        self.assertIsInstance(settings, Settings)

    def test_supabase_jwt_secret_is_string(self):
        self.assertIsInstance(settings.SUPABASE_JWT_SECRET, str)

    def test_freemium_limits_defined_and_positive(self):
        self.assertGreaterEqual(settings.FREEMIUM_MAX_ANALYSES, 1)
        self.assertGreaterEqual(settings.FREEMIUM_MAX_INTERVIEWS, 1)
        self.assertGreaterEqual(settings.FREEMIUM_MAX_CHATBOT_MSGS, 1)
        self.assertGreaterEqual(settings.FREEMIUM_MAX_PORTFOLIO_GENS, 1)

    def test_environment_setting_exists(self):
        self.assertIn(settings.ENVIRONMENT, ["development", "production", "staging", "test"])


if __name__ == "__main__":
    unittest.main()
