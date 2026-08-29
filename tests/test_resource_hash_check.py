"""resource_hash_check 单元测试。"""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.core.utils.resource_hash_check import (
    DEFAULT_HASH_KEY,
    begin_github_hash_prefetch,
    clear_github_release_body_cache,
    compare_resource_hash_sources,
    fetch_github_release_body,
    fetch_github_resource_hashes,
    finish_github_hash_prefetch,
    get_cached_github_release_body,
    get_github_resource_hashes_for_run,
    github_tag_candidates,
    github_versions_match,
    parse_github_owner_repo,
    parse_release_body_hashes,
    pick_github_hash,
    refresh_github_hash_cache_for_current_version,
    store_github_release_body,
)

try:
    from app.core.runner.task_flow import TaskFlowRunner
except ImportError:  # pragma: no cover - 本地未安装 PySide6 时跳过 Runner 用例
    TaskFlowRunner = None


class CompareResourceHashSourcesTest(unittest.TestCase):
    def test_no_optional_sources_passes(self) -> None:
        result = compare_resource_hash_sources(actual_hash="abc12345")
        self.assertTrue(result.passed)
        self.assertEqual(result.mismatched_sources, ())

    def test_interface_missing_hash_skipped(self) -> None:
        result = compare_resource_hash_sources(
            actual_hash="abc12345",
            interface_hash="",
            github_hash="",
        )
        self.assertTrue(result.passed)

    def test_interface_mismatch_fails(self) -> None:
        result = compare_resource_hash_sources(
            actual_hash="abc12345",
            interface_hash="deadbeef",
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.mismatched_sources, ("interface",))

    def test_github_mismatch_fails(self) -> None:
        result = compare_resource_hash_sources(
            actual_hash="abc12345",
            github_hash="deadbeef",
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.mismatched_sources, ("github",))

    def test_all_three_match_passes(self) -> None:
        result = compare_resource_hash_sources(
            actual_hash="ABC12345",
            interface_hash="abc12345",
            github_hash="Abc12345",
        )
        self.assertTrue(result.passed)

    def test_interface_and_github_both_mismatch(self) -> None:
        result = compare_resource_hash_sources(
            actual_hash="abc12345",
            interface_hash="11111111",
            github_hash="22222222",
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.mismatched_sources, ("interface", "github"))


class ParseReleaseBodyHashesTest(unittest.TestCase):
    def test_html_comment_named_hashes(self) -> None:
        body = """
        ## Changelog
        <!-- mfw-resource-hash
        Android: abc12345
        通用资源: def67890
        -->
        """
        parsed = parse_release_body_hashes(body)
        self.assertEqual(parsed["Android"], "abc12345")
        self.assertEqual(parsed["通用资源"], "def67890")

    def test_inline_comment_global_hash(self) -> None:
        parsed = parse_release_body_hashes(
            "notes\n<!-- resource-hash: aabbccdd -->\nmore"
        )
        self.assertEqual(parsed[DEFAULT_HASH_KEY], "aabbccdd")

    def test_line_keywords(self) -> None:
        body = """
        hash: 11112222
        hash[Android]: 33334444
        resource-hash[Win32]: 55556666
        哈希[Mac]: 77778888
        """
        parsed = parse_release_body_hashes(body)
        self.assertEqual(parsed[DEFAULT_HASH_KEY], "11112222")
        self.assertEqual(parsed["Android"], "33334444")
        self.assertEqual(parsed["Win32"], "55556666")
        self.assertEqual(parsed["Mac"], "77778888")

    def test_json_object_in_body(self) -> None:
        body = 'release note {"hash": {"Android": "abcd1234"}} thanks'
        parsed = parse_release_body_hashes(body)
        self.assertEqual(parsed["Android"], "abcd1234")

    def test_ignores_non_hash_words(self) -> None:
        parsed = parse_release_body_hashes("hash: improved lookup table")
        self.assertEqual(parsed, {})

    def test_empty_body(self) -> None:
        self.assertEqual(parse_release_body_hashes(""), {})
        self.assertEqual(parse_release_body_hashes(None), {})


class PickGithubHashTest(unittest.TestCase):
    def test_prefers_resource_name(self) -> None:
        value = pick_github_hash(
            {"Android": "abc12345", DEFAULT_HASH_KEY: "99999999"},
            resource_name="Android",
        )
        self.assertEqual(value, "abc12345")

    def test_falls_back_to_label(self) -> None:
        value = pick_github_hash(
            {"通用资源": "abc12345"},
            resource_name="general",
            resource_label="$通用资源",
        )
        self.assertEqual(value, "abc12345")

    def test_falls_back_to_default(self) -> None:
        value = pick_github_hash(
            {DEFAULT_HASH_KEY: "abc12345"},
            resource_name="Android",
        )
        self.assertEqual(value, "abc12345")

    def test_missing_entry_is_empty(self) -> None:
        value = pick_github_hash(
            {"Win32": "abc12345"},
            resource_name="Android",
        )
        self.assertEqual(value, "")


class GithubRepoAndTagTest(unittest.TestCase):
    def test_parse_https_repo(self) -> None:
        self.assertEqual(
            parse_github_owner_repo("https://github.com/overflow65537/MAA_Punish"),
            ("overflow65537", "MAA_Punish"),
        )

    def test_parse_git_suffix_and_ssh(self) -> None:
        self.assertEqual(
            parse_github_owner_repo("https://github.com/owner/repo.git"),
            ("owner", "repo"),
        )
        self.assertEqual(
            parse_github_owner_repo("git@github.com:owner/repo.git"),
            ("owner", "repo"),
        )

    def test_non_github_url_is_none(self) -> None:
        self.assertIsNone(parse_github_owner_repo("https://example.com/owner/repo"))
        self.assertIsNone(parse_github_owner_repo(""))

    def test_tag_candidates(self) -> None:
        self.assertEqual(github_tag_candidates("3.10.26"), ["3.10.26", "v3.10.26"])
        self.assertEqual(github_tag_candidates("v3.10.26"), ["v3.10.26", "3.10.26"])
        self.assertEqual(github_tag_candidates(""), [])
        self.assertTrue(github_versions_match("v3.10.26", "3.10.26"))
        self.assertFalse(github_versions_match("v3.10.26", "3.10.27"))
        self.assertFalse(github_versions_match("", "1.0.0"))


class FetchGithubReleaseBodyTest(unittest.TestCase):
    def setUp(self) -> None:
        clear_github_release_body_cache()

    def tearDown(self) -> None:
        clear_github_release_body_cache()

    def test_fetch_parses_body_hashes(self) -> None:
        response = SimpleNamespace(
            status_code=200,
            json=lambda: {"body": "hash[Android]: abc12345\n"},
        )
        parsed = fetch_github_resource_hashes(
            "https://github.com/owner/repo",
            "v1.0.0",
            request_get=lambda *args, **kwargs: response,
        )
        self.assertEqual(parsed["Android"], "abc12345")

    def test_fetch_failure_returns_empty(self) -> None:
        def boom(*args, **kwargs):
            raise RuntimeError("network down")

        parsed = fetch_github_resource_hashes(
            "https://github.com/owner/repo",
            "v1.0.0",
            request_get=boom,
        )
        self.assertEqual(parsed, {})

    def test_missing_github_or_version_skips(self) -> None:
        self.assertEqual(fetch_github_release_body("", "v1.0.0"), "")
        self.assertEqual(
            fetch_github_release_body("https://github.com/owner/repo", ""),
            "",
        )

    def test_fetch_uses_two_second_timeout(self) -> None:
        captured: dict[str, float] = {}

        def getter(url, **kwargs):
            captured["timeout"] = kwargs.get("timeout")
            return SimpleNamespace(
                status_code=200,
                json=lambda: {"body": "hash: abcdef12\n"},
            )

        fetch_github_release_body(
            "https://github.com/owner/repo",
            "v1.0.0",
            request_get=getter,
        )
        timeout = captured.get("timeout")
        self.assertIsNotNone(timeout)
        self.assertLessEqual(float(timeout), 2.0)
        self.assertGreater(float(timeout), 0)

    def test_not_found_tries_next_tag(self) -> None:
        calls: list[str] = []

        def getter(url, **kwargs):
            calls.append(url)
            if url.endswith("/tags/1.0.0"):
                return SimpleNamespace(status_code=404, json=lambda: {"message": "Not Found"})
            return SimpleNamespace(
                status_code=200,
                json=lambda: {"body": "hash: abcdef12\n"},
            )

        body = fetch_github_release_body(
            "https://github.com/owner/repo",
            "1.0.0",
            request_get=getter,
        )
        self.assertEqual(body, "hash: abcdef12\n")
        self.assertEqual(len(calls), 2)


class GithubHashPrefetchCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        clear_github_release_body_cache()
        self._tmp = tempfile.TemporaryDirectory()
        self._disk = Path(self._tmp.name) / "cache.json"
        self._patcher = patch(
            "app.core.utils.resource_hash_check._disk_cache_path",
            return_value=self._disk,
        )
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()
        self._tmp.cleanup()
        clear_github_release_body_cache()

    def test_reuse_github_latest_when_version_matches(self) -> None:
        getter = Mock(side_effect=AssertionError("should reuse latest body"))
        body = refresh_github_hash_cache_for_current_version(
            "https://github.com/owner/repo",
            "v1.0.0",
            source="github",
            latest_version="1.0.0",
            latest_body="hash[Android]: abc12345\n",
            request_get=getter,
        )
        self.assertIn("abc12345", body)
        getter.assert_not_called()
        cached = get_cached_github_release_body(
            "https://github.com/owner/repo",
            "1.0.0",
        )
        self.assertEqual(cached, "hash[Android]: abc12345\n")

    def test_mirror_check_fetches_current_version(self) -> None:
        response = SimpleNamespace(
            status_code=200,
            json=lambda: {"body": "hash: abcdef12\n"},
        )
        getter = Mock(return_value=response)
        body = refresh_github_hash_cache_for_current_version(
            "https://github.com/owner/repo",
            "v1.0.0",
            source="mirror",
            latest_version="v1.0.0",
            latest_body="mirror notes",
            request_get=getter,
        )
        self.assertEqual(body, "hash: abcdef12\n")
        getter.assert_called_once()

    def test_newer_github_latest_does_not_reuse_body(self) -> None:
        response = SimpleNamespace(
            status_code=200,
            json=lambda: {"body": "hash: 11112222\n"},
        )
        getter = Mock(return_value=response)
        body = refresh_github_hash_cache_for_current_version(
            "https://github.com/owner/repo",
            "v1.0.0",
            source="github",
            latest_version="v2.0.0",
            latest_body="hash: deadbeef\n",
            request_get=getter,
        )
        self.assertEqual(body, "hash: 11112222\n")
        getter.assert_called_once()

    def test_disk_cache_skips_network_on_later_refresh(self) -> None:
        store_github_release_body(
            "https://github.com/owner/repo",
            "v1.0.0",
            "hash: abcdef12\n",
            persist=True,
        )
        clear_github_release_body_cache()
        getter = Mock(side_effect=AssertionError("disk cache should be used"))
        body = refresh_github_hash_cache_for_current_version(
            "https://github.com/owner/repo",
            "1.0.0",
            source="mirror",
            request_get=getter,
        )
        self.assertEqual(body, "hash: abcdef12\n")
        getter.assert_not_called()

    def test_run_lookup_waits_for_prefetch(self) -> None:
        begin_github_hash_prefetch()
        github_url = "https://github.com/owner/repo"
        result: dict[str, str] = {}

        def _complete() -> None:
            store_github_release_body(
                github_url,
                "v1.0.0",
                "hash[Android]: abc12345\n",
                persist=False,
            )
            finish_github_hash_prefetch()

        worker = threading.Timer(0.05, _complete)
        worker.start()
        try:
            result = get_github_resource_hashes_for_run(github_url, "v1.0.0")
        finally:
            worker.join()
        self.assertEqual(result["Android"], "abc12345")

    def test_run_lookup_does_not_fetch(self) -> None:
        parsed = get_github_resource_hashes_for_run(
            "https://github.com/owner/repo",
            "v1.0.0",
        )
        self.assertEqual(parsed, {})


@unittest.skipIf(TaskFlowRunner is None, "PySide6 is not installed")
class VerifyResourceHashesRunnerTest(unittest.IsolatedAsyncioTestCase):
    def _runner(self, *, actual: str = "abc12345", github: str = "", version: str = "v1.0.0"):
        runner = SimpleNamespace(
            maafw=SimpleNamespace(resource=SimpleNamespace(hash=actual)),
            _runtime_interface={
                "github": github,
                "version": version,
            },
            log_output=SimpleNamespace(emit=Mock()),
            info_bar_requested=SimpleNamespace(emit=Mock()),
        )
        runner.tr = lambda text: text
        return runner

    async def test_interface_mismatch_blocks_run(self) -> None:
        runner = self._runner()
        ok = await TaskFlowRunner._verify_resource_hashes(
            runner,
            resource_name="Android",
            resource_label="",
            interface_hash="deadbeef",
        )
        self.assertFalse(ok)
        runner.log_output.emit.assert_any_call("ERROR", "Resource error")
        runner.info_bar_requested.emit.assert_called_once_with("error", "Resource error")

    async def test_interface_without_hash_passes(self) -> None:
        runner = self._runner()
        ok = await TaskFlowRunner._verify_resource_hashes(
            runner,
            resource_name="Android",
            resource_label="",
            interface_hash="",
        )
        self.assertTrue(ok)
        runner.log_output.emit.assert_not_called()

    async def test_github_mismatch_blocks_run(self) -> None:
        runner = self._runner(github="https://github.com/owner/repo")
        with patch(
            "app.core.runner.task_flow.get_github_resource_hashes_for_run",
            new=Mock(return_value={"Android": "deadbeef"}),
        ):
            ok = await TaskFlowRunner._verify_resource_hashes(
                runner,
                resource_name="Android",
                resource_label="",
                interface_hash="",
            )
        self.assertFalse(ok)

    async def test_github_without_keywords_passes(self) -> None:
        runner = self._runner(github="https://github.com/owner/repo")
        with patch(
            "app.core.runner.task_flow.get_github_resource_hashes_for_run",
            new=Mock(return_value={}),
        ):
            ok = await TaskFlowRunner._verify_resource_hashes(
                runner,
                resource_name="Android",
                resource_label="",
                interface_hash="",
            )
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
