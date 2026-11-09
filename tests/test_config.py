import unittest

from verbump.config import ConfigError, parse


class ConfigTest(unittest.TestCase):
    def test_defaults_and_paths(self):
        cfg = parse({"packages": {"api": {"path": "services/api", "files": ["pyproject.toml"]}}})
        api = cfg.get("api")
        self.assertEqual(api.files[0].path, "services/api/pyproject.toml")
        self.assertEqual(api.changelog_path, "services/api/CHANGELOG.md")
        self.assertEqual(api.tag("1.2.3"), "api/v1.2.3")
        self.assertEqual(api.major_tag_name("1.2.3"), "api/v1")
        self.assertTrue(api.tag_regex().match("api/v1.2.3"))
        self.assertFalse(api.tag_regex().match("apix/v1.2.3"))

    def test_single_package_tags(self):
        cfg = parse({"tag_format": "v{version}", "major_tag": True, "packages": {"tool": {"files": ["VERSION"]}}})
        tool = cfg.get("tool")
        self.assertEqual(tool.tag("0.2.0"), "v0.2.0")
        self.assertEqual(tool.major_tag_name("0.2.0"), "v0")
        self.assertTrue(tool.major_tag)

    def test_errors(self):
        cases = [
            {},
            {"packages": {"a": {"bogus": 1}}},
            {"packages": {"a": {"files": ["weird.txt"]}}},
            {"packages": {"a": {"files": [{"path": "x.txt", "pattern": "nogroup"}]}}},
            {"packages": {"a": {"path": "../out"}}},
            {"packages": {"a": {"tag_format": "v{version}"}, "b": {"tag_format": "v{version}"}}},
            {"packages": {"a b": {}}},
        ]
        for data in cases:
            with self.subTest(data=data), self.assertRaises((ConfigError, ValueError)):
                cfg = parse(data)
                for p in cfg.packages:
                    for f in p.files:
                        f.regex()


if __name__ == "__main__":
    unittest.main()
