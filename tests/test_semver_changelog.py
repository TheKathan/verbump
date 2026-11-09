import unittest

from verbump import changelog, semver


class SemverTest(unittest.TestCase):
    def test_bump(self):
        self.assertEqual(semver.bump("1.2.3", "patch"), "1.2.4")
        self.assertEqual(semver.bump("v1.2.3", "Minor"), "1.3.0")
        self.assertEqual(semver.bump("1.2.3", "major"), "2.0.0")
        with self.assertRaises(semver.VersionError):
            semver.bump("1.2", "patch")

    def test_bump_between_reads_trunk_semver_outputs(self):
        self.assertEqual(semver.bump_between("v1.0.0", "v1.1.0"), "minor")
        self.assertEqual(semver.bump_between("v1.4.2", "v1.4.3"), "patch")
        self.assertEqual(semver.bump_between("v1.4.2", "v2.0.0"), "major")
        with self.assertRaises(semver.VersionError):
            semver.bump_between("v1.1.0", "v1.1.0")

    def test_branch_rule(self):
        self.assertEqual(semver.bump_for_branch("feature/x"), "minor")
        self.assertEqual(semver.bump_for_branch("feat/x"), "minor")
        self.assertEqual(semver.bump_for_branch("fix/x"), "patch")


class ChangelogTest(unittest.TestCase):
    def test_unreleased_notes_become_the_release(self):
        text = "# Changelog\n\n## [Unreleased]\n\n### Fixed\n- A bug.\n\n## [1.0.0] - 2026-01-01\n\n- First.\n"
        out = changelog.release(text, "1.0.1", "2026-02-02", [("abc1234", "fix: other")])
        self.assertIn("## [Unreleased]\n\n## [1.0.1] - 2026-02-02\n\n### Fixed\n- A bug.\n\n## [1.0.0]", out)
        self.assertNotIn("fix: other", out)
        self.assertEqual(changelog.notes(out, "1.0.1"), "### Fixed\n- A bug.")
        self.assertEqual(changelog.notes(out, "1.0.0"), "- First.")

    def test_empty_unreleased_lists_commits_without_release_commits(self):
        text = "# Changelog\n\n## [Unreleased]\n"
        commits = [("aaa1111", "fix: thing"), ("bbb2222", "chore(release): api 1.0.0"), ("ccc3333", "feat: more")]
        out = changelog.release(text, "1.1.0", "2026-02-02", commits)
        self.assertEqual(changelog.notes(out, "1.1.0"), "### Changes\n- fix: thing (aaa1111)\n- feat: more (ccc3333)")

    def test_missing_file_is_created_and_rerun_is_a_no_op(self):
        out = changelog.release(None, "0.1.0", "2026-02-02", [])
        self.assertTrue(out.startswith("# Changelog"))
        self.assertIn("## [Unreleased]\n\n## [0.1.0] - 2026-02-02\n\nNo notable changes.\n", out)
        self.assertEqual(changelog.release(out, "0.1.0", "2026-03-03", []), out)

    def test_no_unreleased_heading_adds_one(self):
        text = "# Changelog\n\n## [1.0.0] - 2026-01-01\n\n- First.\n"
        out = changelog.release(text, "1.0.1", "2026-02-02", [("aaa1111", "fix: x")])
        self.assertIn("## [Unreleased]\n\n## [1.0.1] - 2026-02-02\n\n### Changes\n- fix: x (aaa1111)\n\n## [1.0.0]", out)

    def test_notes_fallback(self):
        self.assertEqual(changelog.notes("", "2.0.0"), "Release 2.0.0.")


if __name__ == "__main__":
    unittest.main()
