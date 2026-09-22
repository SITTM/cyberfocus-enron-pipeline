"""Unit tests for the pure logic in scripts/bootstrap-v2.py.

Only the side-effect-free parts are tested here: version checks, nvidia-smi
parsing, GPU verdicts and failure classification. The install/corpus/pipeclean
parts are proved by actually running the script on a clean machine (a Docker
container and a clean Windows VM), not by mocking them.

The script is named with a hyphen so it cannot be imported normally; load it
by path.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "bootstrap_v2", ROOT / "scripts" / "bootstrap-v2.py"
)
bs = importlib.util.module_from_spec(_spec)
sys.modules["bootstrap_v2"] = bs
_spec.loader.exec_module(bs)


class TestPythonWindow(unittest.TestCase):
    """The supported window is 3.12-3.14. It is NOT 3.8 -- see classify docs."""

    def test_supported_versions(self) -> None:
        for v in [(3, 12), (3, 13), (3, 14)]:
            self.assertEqual(bs.classify_python(v), "ok", f"{v} should be ok")

    def test_too_old(self) -> None:
        for v in [(3, 8), (3, 9), (3, 11)]:
            self.assertEqual(bs.classify_python(v), "too-old", f"{v}")

    def test_too_new(self) -> None:
        self.assertEqual(bs.classify_python((3, 15)), "too-new")


class TestNvidiaSmiParsing(unittest.TestCase):
    QUERY_OUTPUT = "NVIDIA RTX 3500 Ada Generation Laptop GPU, 581.42, 12282\n"

    def test_parses_query_csv_output(self) -> None:
        got = bs.parse_nvidia_smi(self.QUERY_OUTPUT, "12.8")
        self.assertEqual(got["name"], "NVIDIA RTX 3500 Ada Generation Laptop GPU")
        self.assertEqual(got["driver"], "581.42")
        self.assertEqual(got["memory_mib"], 12282)
        self.assertEqual(got["cuda"], "12.8")

    def test_returns_none_on_empty_output(self) -> None:
        self.assertIsNone(bs.parse_nvidia_smi("", None))

    def test_returns_none_on_garbage(self) -> None:
        self.assertIsNone(bs.parse_nvidia_smi("command not found", None))

    def test_tolerates_missing_memory_field(self) -> None:
        got = bs.parse_nvidia_smi("Some GPU, 581.42\n", "12.8")
        self.assertEqual(got["name"], "Some GPU")
        self.assertIsNone(got["memory_mib"])


class TestCudaVersionExtraction(unittest.TestCase):
    def test_extracts_from_nvidia_smi_banner(self) -> None:
        banner = (
            "| NVIDIA-SMI 581.42   Driver Version: 581.42   CUDA Version: 12.8  |"
        )
        self.assertEqual(bs.parse_cuda_version(banner), "12.8")

    def test_extracts_from_umd_banner_used_by_6xx_drivers(self) -> None:
        """Real output from driver 610.43.02 -- note the 'UMD'. (buglog bug-004)"""
        banner = (
            "| NVIDIA-SMI 610.43.02   KMD Version: 610.43.02   "
            "CUDA UMD Version: 13.3  |"
        )
        self.assertEqual(bs.parse_cuda_version(banner), "13.3")

    def test_none_when_absent(self) -> None:
        self.assertIsNone(bs.parse_cuda_version("no cuda here"))


class TestGpuVerdict(unittest.TestCase):
    """cupy-cuda12x needs a driver supporting CUDA 12.x OR NEWER (NVIDIA drivers
    are backward compatible), and has no macOS wheels at all. Anything else must
    fall back to CPU, not fail."""

    def test_cuda_12_is_supported(self) -> None:
        ok, _ = bs.gpu_verdict({"cuda": "12.8"}, "win32")
        self.assertTrue(ok)

    def test_cuda_13_driver_runs_cuda_12_binaries(self) -> None:
        """A CUDA 13 driver is backward compatible, so cupy-cuda12x still works."""
        ok, _ = bs.gpu_verdict({"cuda": "13.3"}, "linux")
        self.assertTrue(ok)

    def test_cuda_11_too_old(self) -> None:
        ok, reason = bs.gpu_verdict({"cuda": "11.8"}, "linux")
        self.assertFalse(ok)
        self.assertIn("12.x", reason)

    def test_unreadable_cuda_version_falls_back_to_cpu(self) -> None:
        ok, _ = bs.gpu_verdict({"cuda": "unknown"}, "linux")
        self.assertFalse(ok)

    def test_no_gpu_means_cpu(self) -> None:
        ok, reason = bs.gpu_verdict(None, "win32")
        self.assertFalse(ok)
        self.assertIn("no NVIDIA GPU", reason)

    def test_macos_never_supported(self) -> None:
        ok, reason = bs.gpu_verdict({"cuda": "12.8"}, "darwin")
        self.assertFalse(ok)
        self.assertIn("macOS", reason)


class TestFailureClassification(unittest.TestCase):
    """Turns raw failure output into an actionable hint, so a collaborator can
    send one report file rather than a screenshot of a traceback."""

    def hint_for(self, text: str) -> str:
        found = bs.classify_failure(text)
        self.assertTrue(found, f"no classification for: {text!r}")
        return found[0]["id"]

    def test_missing_compiler(self) -> None:
        self.assertEqual(
            self.hint_for("error: Microsoft Visual C++ 14.0 or greater is required."),
            "needs-compiler",
        )

    def test_no_matching_distribution(self) -> None:
        self.assertEqual(
            self.hint_for("ERROR: No matching distribution found for spacy==3.8.16"),
            "no-matching-wheel",
        )

    def test_windows_path_limit(self) -> None:
        self.assertEqual(
            self.hint_for("Extraction produced only 63 custodian directories, expected 150."),
            "corpus-incomplete",
        )

    def test_row_count_mismatch(self) -> None:
        self.assertEqual(
            self.hint_for("email row count differs from the known-good run."),
            "corpus-incomplete",
        )

    def test_tls_interception(self) -> None:
        self.assertEqual(
            self.hint_for("SSLError: CERTIFICATE_VERIFY_FAILED unable to get local issuer"),
            "tls-intercepted",
        )

    def test_disk_full(self) -> None:
        self.assertEqual(
            self.hint_for("OSError: [Errno 28] No space left on device"),
            "disk-full",
        )

    def test_out_of_memory(self) -> None:
        self.assertEqual(self.hint_for("MemoryError"), "out-of-memory")

    def test_cuda_driver_too_old(self) -> None:
        self.assertEqual(
            self.hint_for("cupy_backends.cuda.api.driver.CUDADriverError: "
                          "CUDA_ERROR_SYSTEM_DRIVER_MISMATCH"),
            "gpu-driver",
        )

    def test_unknown_text_classifies_as_nothing(self) -> None:
        self.assertEqual(bs.classify_failure("something entirely novel"), [])

    def test_multiple_signatures_all_reported(self) -> None:
        text = "MemoryError\nERROR: No matching distribution found for spacy"
        ids = {f["id"] for f in bs.classify_failure(text)}
        self.assertEqual(ids, {"out-of-memory", "no-matching-wheel"})

    def test_every_hint_has_a_remedy(self) -> None:
        for sig in bs.FAILURE_SIGNATURES:
            self.assertTrue(sig["remedy"].strip(), f"{sig['id']} has no remedy")


class TestExtractCorpus(unittest.TestCase):
    """Extraction takes 30-60 minutes on Windows and tarfile.extractall() is
    silent for all of it, which is indistinguishable from a hang."""

    def make_tarball(self, tmp: Path, custodians: int, per: int) -> Path:
        import tarfile
        tree = tmp / "src"
        for c in range(custodians):
            d = tree / "maildir" / ("person-%d" % c) / "inbox"
            d.mkdir(parents=True)
            for f in range(per):
                (d / str(f)).write_text("message %d" % f, encoding="utf-8")
        tgz = tmp / "corpus.tar.gz"
        with tarfile.open(tgz, "w:gz") as tf:
            tf.add(tree / "maildir", arcname="maildir")
        return tgz

    def test_extracts_everything_and_counts_custodians(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            tgz = self.make_tarball(tmp, custodians=4, per=3)
            dest = tmp / "out"
            dest.mkdir()
            result = bs.extract_corpus(tgz, dest)
            self.assertEqual(result.custodians, 4)
            self.assertEqual(bs.custodian_count(dest / "maildir"), 4)
            self.assertGreaterEqual(result.extracted, 12)
            self.assertEqual(
                (dest / "maildir" / "person-0" / "inbox" / "0").read_text(),
                "message 0")

    def test_reports_progress_on_the_configured_interval(self) -> None:
        """With the interval set to 0 every member should produce a line."""
        import tempfile, io, contextlib
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            tgz = self.make_tarball(tmp, custodians=2, per=2)
            dest = tmp / "out"
            dest.mkdir()
            buf = io.StringIO()
            original = bs.PROGRESS_EVERY
            bs.PROGRESS_EVERY = 0
            try:
                with contextlib.redirect_stdout(buf):
                    bs.extract_corpus(tgz, dest)
            finally:
                bs.PROGRESS_EVERY = original
            out = buf.getvalue()
            self.assertIn("custodian", out.lower())
            self.assertGreater(len(out.strip().splitlines()), 1)

    def test_resumes_instead_of_re_extracting_everything(self) -> None:
        """A 1-3 hour extraction must not start over if it is interrupted."""
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            tgz = self.make_tarball(tmp, custodians=4, per=3)
            dest = tmp / "out"
            dest.mkdir()
            first = bs.extract_corpus(tgz, dest)
            self.assertEqual(first.skipped, 0)

            # Simulate an interrupt: lose one whole custodian.
            import shutil
            shutil.rmtree(dest / "maildir" / "person-2")

            second = bs.extract_corpus(tgz, dest)
            self.assertGreater(second.skipped, 0, "should skip existing files")
            self.assertGreater(second.extracted, 0, "should restore the missing one")
            self.assertLess(second.extracted, first.extracted,
                            "should do less work than the first run")
            self.assertEqual(bs.custodian_count(dest / "maildir"), 4)
            self.assertEqual(
                (dest / "maildir" / "person-2" / "inbox" / "1").read_text(),
                "message 1")

    def test_a_half_written_file_is_re_extracted_not_kept(self) -> None:
        """The file being written when the interrupt hit is truncated."""
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            tgz = self.make_tarball(tmp, custodians=2, per=2)
            dest = tmp / "out"
            dest.mkdir()
            bs.extract_corpus(tgz, dest)
            victim = dest / "maildir" / "person-1" / "inbox" / "0"
            victim.write_text("tru", encoding="utf-8")   # short read

            result = bs.extract_corpus(tgz, dest)
            self.assertEqual(victim.read_text(), "message 0")
            self.assertGreaterEqual(result.extracted, 1)

    def test_resume_can_be_turned_off(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            tgz = self.make_tarball(tmp, custodians=2, per=2)
            dest = tmp / "out"
            dest.mkdir()
            bs.extract_corpus(tgz, dest)
            again = bs.extract_corpus(tgz, dest, resume=False)
            self.assertEqual(again.skipped, 0)

    def test_estimates_time_remaining_once_there_is_enough_to_go_on(self) -> None:
        """The ETA branch only fires after 30s, so fake the clock to reach it."""
        import tempfile, io, contextlib
        from unittest import mock
        clock = [1000.0]

        def fake_time():
            clock[0] += 20.0   # 20s per member: past the 30s guard quickly
            return clock[0]

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            tgz = self.make_tarball(tmp, custodians=3, per=2)
            dest = tmp / "out"
            dest.mkdir()
            buf = io.StringIO()
            with mock.patch.object(bs.time, "time", fake_time):
                with contextlib.redirect_stdout(buf):
                    bs.extract_corpus(tgz, dest)
            out = buf.getvalue()
            self.assertIn("min left", out)
            # and it must never claim zero minutes remaining
            self.assertNotIn("about 0 min left", out)

    def test_is_silent_when_interval_not_reached(self) -> None:
        import tempfile, io, contextlib
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            tgz = self.make_tarball(tmp, custodians=2, per=2)
            dest = tmp / "out"
            dest.mkdir()
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                bs.extract_corpus(tgz, dest)
            self.assertEqual(buf.getvalue().strip(), "")


class TestDownloadRetries(unittest.TestCase):
    """Unattended runs must survive a dropped connection mid-download. Each
    retry resumes from the .part file, so a drop costs the remaining bytes and
    not the whole 423MB."""

    def setUp(self) -> None:
        from unittest import mock
        self.slept = []
        self._sleep = mock.patch.object(bs.time, "sleep", self.slept.append)
        self._sleep.start()
        self.addCleanup(self._sleep.stop)

    def test_retries_until_it_succeeds(self) -> None:
        from unittest import mock
        calls = []

        def flaky(url, dest, context=None):
            calls.append(1)
            if len(calls) < 3:
                raise OSError("connection reset")

        with mock.patch.object(bs, "download", flaky):
            bs.download_with_retries("http://x", Path("d"))
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(self.slept), 2, "should back off between attempts")

    def test_does_not_retry_when_the_first_attempt_works(self) -> None:
        from unittest import mock
        calls = []
        with mock.patch.object(bs, "download",
                               lambda u, d, context=None: calls.append(1)):
            bs.download_with_retries("http://x", Path("d"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.slept, [])

    def test_gives_up_and_reraises_after_the_last_attempt(self) -> None:
        from unittest import mock
        calls = []

        def always_fails(url, dest, context=None):
            calls.append(1)
            raise OSError("no route to host")

        with mock.patch.object(bs, "download", always_fails):
            with self.assertRaises(OSError):
                bs.download_with_retries("http://x", Path("d"), attempts=3)
        self.assertEqual(len(calls), 3)


class TestCorpusSslContext(unittest.TestCase):
    """uv's managed CPython has no CA bundle on Windows, so the corpus download
    must borrow certifi from the venv. (buglog bug-006)"""

    def test_uses_certifi_bundle_when_available(self) -> None:
        ctx = bs.corpus_ssl_context(Path(sys.executable))
        # This interpreter may or may not have certifi; either way we must get
        # back a usable, verifying context rather than an exception.
        self.assertTrue(ctx.verify_mode)

    def test_falls_back_when_no_interpreter_given(self) -> None:
        ctx = bs.corpus_ssl_context(None)
        self.assertTrue(ctx.verify_mode)

    def test_falls_back_when_certifi_missing(self) -> None:
        ctx = bs.corpus_ssl_context(Path("definitely-not-a-real-binary-xyz"))
        self.assertTrue(ctx.verify_mode)


class TestRunStreaming(unittest.TestCase):
    """Long phases tee their output so a slow download does not look like a hang."""

    def test_returns_captured_output_and_code(self) -> None:
        r = bs.run_streaming([sys.executable, "-c", "print('alpha'); print('beta')"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("alpha", r.stdout)
        self.assertIn("beta", r.stdout)

    def test_nonzero_exit_is_reported(self) -> None:
        r = bs.run_streaming([sys.executable, "-c", "import sys; sys.exit(3)"])
        self.assertEqual(r.returncode, 3)

    def test_stderr_is_merged_into_stdout(self) -> None:
        r = bs.run_streaming(
            [sys.executable, "-c", "import sys; sys.stderr.write('oops')"])
        # Assert a clean exit FIRST. Without it this passed for the wrong
        # reason: an earlier version embedded a real newline in the -c argument,
        # the child died with SyntaxError, and "oops" matched only because the
        # traceback echoed the offending source line.
        self.assertEqual(r.returncode, 0, "child crashed: %r" % r.stdout)
        self.assertIn("oops", r.stdout)

    def test_missing_binary_does_not_raise(self) -> None:
        r = bs.run_streaming(["definitely-not-a-real-binary-xyz"])
        self.assertEqual(r.returncode, 127)


class TestHeartbeat(unittest.TestCase):
    """A stage that prints nothing for minutes (spaCy analysis) must still show
    it is alive, or the pipeclean looks hung."""

    def test_silent_process_still_reports_it_is_running(self) -> None:
        import io, contextlib
        original = bs.PROGRESS_EVERY
        bs.PROGRESS_EVERY = 0.3
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                r = bs.run_streaming(
                    [sys.executable, "-c", "import time; time.sleep(1.6)"],
                    heartbeat="pipeclean")
        finally:
            bs.PROGRESS_EVERY = original
        self.assertEqual(r.returncode, 0)
        self.assertIn("still running", buf.getvalue())
        self.assertIn("pipeclean", buf.getvalue())

    def test_does_not_leak_the_output_pipe(self) -> None:
        """A leaked pipe spills ResourceWarnings into the pipeclean output."""
        import warnings, gc, io, contextlib
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            with contextlib.redirect_stdout(io.StringIO()):
                for _ in range(3):
                    bs.run_streaming([sys.executable, "-c", "print('x')"])
            gc.collect()
        leaks = [w for w in caught if issubclass(w.category, ResourceWarning)]
        self.assertEqual([str(w.message) for w in leaks], [])

    def test_no_heartbeat_when_not_requested(self) -> None:
        import io, contextlib
        original = bs.PROGRESS_EVERY
        bs.PROGRESS_EVERY = 0.3
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                bs.run_streaming([sys.executable, "-c", "import time; time.sleep(1.2)"])
        finally:
            bs.PROGRESS_EVERY = original
        self.assertNotIn("still running", buf.getvalue())

    def test_heartbeat_stops_once_the_process_exits(self) -> None:
        """A leaked thread would keep printing over later output."""
        import io, contextlib, time as _t
        original = bs.PROGRESS_EVERY
        bs.PROGRESS_EVERY = 0.3
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                bs.run_streaming([sys.executable, "-c", "pass"], heartbeat="x")
            after = io.StringIO()
            with contextlib.redirect_stdout(after):
                _t.sleep(1.2)
        finally:
            bs.PROGRESS_EVERY = original
        self.assertEqual(after.getvalue(), "")


class TestRunHelper(unittest.TestCase):
    """The clean-container run caught `run()` baking in timeout=, which made
    every slow phase crash with 'multiple values for keyword argument'.
    (buglog bug-005)"""

    def test_caller_may_override_timeout(self) -> None:
        r = bs.run([sys.executable, "-c", "print('hi')"], timeout=600)
        self.assertEqual(r.returncode, 0)
        self.assertIn("hi", r.stdout)

    def test_missing_binary_does_not_raise(self) -> None:
        r = bs.run(["definitely-not-a-real-binary-xyz"])
        self.assertEqual(r.returncode, 127)

    def test_timeout_is_reported_not_raised(self) -> None:
        r = bs.run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=1)
        self.assertEqual(r.returncode, 124)
        self.assertIn("timed out", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
