import tempfile
import unittest
from pathlib import Path

from verbump.config import ConfigError, parse
from verbump.files import KINDS, VersionFileError, version_file

SAMPLES = {
    "pyproject.toml": ('[project]\nname = "a"\nversion = "1.2.3"\n', '[project]\nname = "a"\nversion = "1.3.0"\n'),
    "Cargo.toml": ('[package]\nname = "a"\nversion = "1.2.3"\n\n[dependencies]\nserde = { version = "1.0.0" }\n',
                   '[package]\nname = "a"\nversion = "1.3.0"\n\n[dependencies]\nserde = { version = "1.0.0" }\n'),
    "package.json": ('{\n  "name": "a",\n  "version": "1.2.3",\n  "dependencies": {"x": "1.0.0"}\n}\n',
                     '{\n  "name": "a",\n  "version": "1.3.0",\n  "dependencies": {"x": "1.0.0"}\n}\n'),
    "composer.json": ('{"name": "a/b", "version": "1.2.3"}\n', '{"name": "a/b", "version": "1.3.0"}\n'),
    "Chart.yaml": ("apiVersion: v2\nname: a\nversion: 1.2.3\nappVersion: \"9.9.9\"\n",
                   "apiVersion: v2\nname: a\nversion: 1.3.0\nappVersion: \"9.9.9\"\n"),
    "pubspec.yaml": ("name: a\nversion: 1.2.3+7\n", "name: a\nversion: 1.3.0+7\n"),
    "VERSION": ("1.2.3\n", "1.3.0\n"),
    "src/a/__init__.py": ('__version__ = "1.2.3"\n', '__version__ = "1.3.0"\n'),
    "A.csproj": ("<Project>\n  <PropertyGroup>\n    <Version>1.2.3</Version>\n  </PropertyGroup>\n</Project>\n",
                 "<Project>\n  <PropertyGroup>\n    <Version>1.3.0</Version>\n  </PropertyGroup>\n</Project>\n"),
    "Directory.Build.props": ("<Project><PropertyGroup><VersionPrefix>1.2.3</VersionPrefix></PropertyGroup></Project>\n",
                              "<Project><PropertyGroup><VersionPrefix>1.3.0</VersionPrefix></PropertyGroup></Project>\n"),
    "Properties/AssemblyInfo.cs": ('[assembly: AssemblyVersion("1.2.3.0")]\n[assembly: AssemblyFileVersion("1.2.3.0")]\n',
                                   '[assembly: AssemblyVersion("1.3.0.0")]\n[assembly: AssemblyFileVersion("1.3.0.0")]\n'),
    "pom.xml": (("<project>\n  <parent>\n    <artifactId>base</artifactId>\n    <version>7.0.0</version>\n  </parent>\n"
                "  <artifactId>a</artifactId>\n  <version>1.2.3</version>\n  <dependencies><dependency>"
                "<version>2.0.0</version></dependency></dependencies>\n</project>\n"),
                ("<project>\n  <parent>\n    <artifactId>base</artifactId>\n    <version>7.0.0</version>\n  </parent>\n"
                "  <artifactId>a</artifactId>\n  <version>1.3.0</version>\n  <dependencies><dependency>"
                "<version>2.0.0</version></dependency></dependencies>\n</project>\n")),
    "gradle.properties": ("org.gradle.jvmargs=-Xmx2g\nversion=1.2.3\n", "org.gradle.jvmargs=-Xmx2g\nversion=1.3.0\n"),
    "build.gradle.kts": ('plugins { id("x") version "8.0.0" }\ngroup = "a"\nversion = "1.2.3"\n',
                         'plugins { id("x") version "8.0.0" }\ngroup = "a"\nversion = "1.3.0"\n'),
    "build.gradle": ("group 'a'\nversion '1.2.3'\n", "group 'a'\nversion '1.3.0'\n"),
    "lib/a/version.rb": ('module A\n  VERSION = "1.2.3"\nend\n', 'module A\n  VERSION = "1.3.0"\nend\n'),
    "a.gemspec": ("Gem::Specification.new do |s|\n  s.version = '1.2.3'\nend\n",
                  "Gem::Specification.new do |s|\n  s.version = '1.3.0'\nend\n"),
    "mix.exs": ('def project do\n    [app: :a, version: "1.2.3", elixir: "~> 1.15"]\n',
                'def project do\n    [app: :a, version: "1.3.0", elixir: "~> 1.15"]\n'),
    "Dockerfile": ('FROM alpine:3.20\nLABEL org.opencontainers.image.version="1.2.3"\n',
                   'FROM alpine:3.20\nLABEL org.opencontainers.image.version="1.3.0"\n'),
}


class StackFilesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def put(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def test_every_known_file(self):
        for path, (before, after) in SAMPLES.items():
            with self.subTest(path=path):
                self.put(path, before)
                f = version_file(path)
                self.assertEqual(f.read(self.root), "1.2.3")
                self.assertTrue(f.write(self.root, "1.3.0"))
                self.assertEqual((self.root / path).read_text(), after)
                self.assertFalse(f.write(self.root, "1.3.0"))

    def test_kind_for_any_file_name(self):
        self.put("deploy/chart/Chart.yaml", "version: 1.2.3\nappVersion: 1.2.3\n")
        f = version_file("deploy/chart/Chart.yaml", kind="helm")
        f.write(self.root, "2.0.0")
        self.assertEqual((self.root / "deploy/chart/Chart.yaml").read_text(), "version: 2.0.0\nappVersion: 2.0.0\n")
        self.put("release.json", '{"version": "0.4.0"}')
        self.assertEqual(version_file("release.json", kind="json").read(self.root), "0.4.0")

    def test_pattern_after_and_replace_all(self):
        self.put("values.yaml", 'old:\n  tag: "0.0.1"\nimage:\n  tag: "1.2.3"\nsidecar:\n  tag: "1.2.3"\n')
        f = version_file("values.yaml", pattern=r'tag: "(?P<version>[0-9.]+)"', after="image:", replace_all=True)
        self.assertEqual(f.read(self.root), "1.2.3")
        f.write(self.root, "1.2.4")
        self.assertEqual((self.root / "values.yaml").read_text(),
                         'old:\n  tag: "0.0.1"\nimage:\n  tag: "1.2.4"\nsidecar:\n  tag: "1.2.4"\n')

    def test_errors(self):
        with self.assertRaises(VersionFileError):
            version_file("notes.txt")
        with self.assertRaises(VersionFileError):
            version_file("x.json", kind="nope")
        self.put("package.json", '{"name": "a"}')
        with self.assertRaises(VersionFileError):
            version_file("package.json").read(self.root)

    def test_every_kind_has_a_version_group(self):
        for name in KINDS:
            with self.subTest(kind=name):
                version_file("x", kind=name).regex()


class TagFormatTest(unittest.TestCase):
    def test_go_style_path_tags(self):
        cfg = parse({"tag_format": "{path}/v{version}", "packages": {"api": {"path": "services/api"}}})
        api = cfg.get("api")
        self.assertEqual(api.tag("1.2.3"), "services/api/v1.2.3")
        self.assertTrue(api.tag_regex().match("services/api/v1.2.3"))
        self.assertEqual(api.major_tag_name("1.2.3"), "services/api/v1")

    def test_bad_tag_formats(self):
        for data in ({"packages": {"a": {"tag_format": "{nope}/v{version}"}}},
                     {"packages": {"a": {"path": ".", "tag_format": "{path}/v{version}"}}},
                     {"packages": {"a": {"files": [{"path": "x.json", "kinds": "json"}]}}}):
            with self.subTest(data=data), self.assertRaises(ConfigError):
                parse(data)


if __name__ == "__main__":
    unittest.main()
