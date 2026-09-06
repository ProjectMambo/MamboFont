#!/usr/bin/env python3

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPT_DIR / "mambo_font.py"
SPEC = importlib.util.spec_from_file_location("mambo_font", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MAMBO_FONT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MAMBO_FONT)


class CliContractTests(unittest.TestCase):
    def test_compile_preserves_multi_value_flags(self):
        args = MAMBO_FONT.build_parser().parse_args(
            [
                "compile",
                "1.2.3",
                "--filter",
                "icons",
                "symbol",
                "--format",
                "ttf",
                "woff2",
                "--svg-cache",
                "cache",
                "--out",
                "build",
            ]
        )
        self.assertEqual(args.version, "1.2.3")
        self.assertEqual(args.filters, ["icons", "symbol"])
        self.assertEqual(args.types, ["ttf", "woff2"])
        self.assertEqual(args.svg_cache, "cache")
        self.assertEqual(args.out, "build")

    def test_compile_keeps_type_alias(self):
        args = MAMBO_FONT.build_parser().parse_args(
            ["compile", "1.2.3", "--type", "ttf"]
        )
        self.assertEqual(args.types, ["ttf"])

    def test_multi_value_options_require_a_value(self):
        for command in (
            ["export", "--filter"],
            ["compile", "1.2.3", "--filter"],
            ["compile", "1.2.3", "--format"],
        ):
            with self.subTest(command=command):
                with self.assertRaises(SystemExit) as error:
                    MAMBO_FONT.build_parser().parse_args(command)
                self.assertEqual(error.exception.code, 2)

    def test_unknown_filter_option_is_rejected(self):
        with self.assertRaises(SystemExit) as error:
            MAMBO_FONT.build_parser().parse_args(
                ["export", "--filter", "icons", "--unknown"]
            )
        self.assertEqual(error.exception.code, 2)

    def test_unrelease_requires_explicit_confirmation(self):
        with self.assertRaises(SystemExit) as error:
            MAMBO_FONT.build_parser().parse_args(["unrelease", "1.2.3"])
        self.assertEqual(error.exception.code, 2)

        args = MAMBO_FONT.build_parser().parse_args(
            ["unrelease", "1.2.3", "--yes"]
        )
        self.assertTrue(args.yes)

    def test_repository_commands_use_project_root(self):
        completed = subprocess.CompletedProcess(["git", "status"], 0)
        with mock.patch.object(
            MAMBO_FONT.subprocess, "run", return_value=completed
        ) as run:
            MAMBO_FONT._run_project_command(["git", "status"], check=True)
        run.assert_called_once_with(
            ["git", "status"], cwd=MAMBO_FONT.PROJECT_ROOT, check=True
        )

    def test_release_lookup_distinguishes_missing_from_transport_failure(self):
        missing = subprocess.CompletedProcess([], 1, stdout="", stderr="release not found")
        with mock.patch.object(
            MAMBO_FONT, "_run_project_command", return_value=missing
        ):
            self.assertFalse(MAMBO_FONT._release_exists("v1.2.3"))

        failure = subprocess.CompletedProcess([], 1, stdout="", stderr="network failed")
        with (
            mock.patch.object(MAMBO_FONT, "_run_project_command", return_value=failure),
            mock.patch("builtins.print"),
            self.assertRaises(SystemExit) as error,
        ):
            MAMBO_FONT._release_exists("v1.2.3")
        self.assertEqual(error.exception.code, 1)

    def test_unrelease_does_not_require_editor(self):
        completed = subprocess.CompletedProcess(["gh", "auth", "status"], 0)
        with (
            mock.patch.object(MAMBO_FONT, "_check_tool") as check_tool,
            mock.patch.object(
                MAMBO_FONT, "_run_project_command", return_value=completed
            ),
        ):
            MAMBO_FONT._check_git_auth()
        self.assertEqual(
            [call.args[0] for call in check_tool.call_args_list], ["gh", "git"]
        )

    def test_semver_validation(self):
        for version in ("0.0.0", "1.2.3", "12.34.56"):
            with self.subTest(version=version):
                MAMBO_FONT._validate_semver(version)

        for version in ("1.2", "v1.2.3", "01.2.3", "1.2.3-alpha"):
            with self.subTest(version=version):
                with self.assertRaises(SystemExit) as error:
                    MAMBO_FONT._validate_semver(version)
                self.assertEqual(error.exception.code, 2)

    def test_compile_validates_semver_before_font_work(self):
        with (
            mock.patch.object(MAMBO_FONT, "_ff", object()),
            mock.patch.object(MAMBO_FONT, "collect_all_svgs") as collect,
            self.assertRaises(SystemExit) as error,
        ):
            MAMBO_FONT.cmd_compile("../../../escape", [])
        self.assertEqual(error.exception.code, 2)
        collect.assert_not_called()

    def test_compile_requires_every_weight_before_writing(self):
        with (
            mock.patch.object(MAMBO_FONT, "_ff", object()),
            mock.patch.object(
                MAMBO_FONT,
                "collect_all_svgs",
                return_value={"regular/icons/Glyph.svg": b"svg"},
            ),
            mock.patch.object(MAMBO_FONT, "build_weight_from_memory") as build,
            mock.patch("builtins.print"),
            self.assertRaises(SystemExit) as error,
        ):
            MAMBO_FONT.cmd_compile("1.2.3", [])
        self.assertEqual(error.exception.code, 1)
        build.assert_not_called()

    def test_release_context_requires_main_and_clean_worktree(self):
        feature_branch = subprocess.CompletedProcess(
            ["git", "branch", "--show-current"], 0, stdout="feature\n"
        )
        with (
            mock.patch.object(MAMBO_FONT, "_check_tool"),
            mock.patch.object(
                MAMBO_FONT, "_run_project_command", return_value=feature_branch
            ),
            self.assertRaises(SystemExit) as error,
        ):
            MAMBO_FONT._validate_release_context("1.2.3")
        self.assertEqual(error.exception.code, 1)

        main_branch = subprocess.CompletedProcess(
            ["git", "branch", "--show-current"], 0, stdout="main\n"
        )
        dirty_status = subprocess.CompletedProcess(
            ["git", "status", "--porcelain"], 0, stdout=" M README.md\n"
        )
        with (
            mock.patch.object(MAMBO_FONT, "_check_tool"),
            mock.patch.object(
                MAMBO_FONT,
                "_run_project_command",
                side_effect=[main_branch, dirty_status],
            ),
            self.assertRaises(SystemExit) as error,
        ):
            MAMBO_FONT._validate_release_context("1.2.3")
        self.assertEqual(error.exception.code, 1)

    def test_unrelease_validates_semver_before_authentication(self):
        with (
            mock.patch.object(MAMBO_FONT, "_check_git_auth") as check_auth,
            self.assertRaises(SystemExit) as error,
        ):
            MAMBO_FONT.cmd_unrelease("v1.2.3")
        self.assertEqual(error.exception.code, 2)
        check_auth.assert_not_called()

    def test_explicit_export_preserves_unrelated_files(self):
        with tempfile.TemporaryDirectory(prefix="mambofont-export-test.") as directory:
            out_dir = Path(directory)
            unrelated = out_dir / "regular" / "icons" / "notes.txt"
            generated = out_dir / "regular" / "icons" / "Glyph.svg"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("keep\n")
            generated.write_bytes(b"old")

            with (
                mock.patch.object(
                    MAMBO_FONT,
                    "collect_all_svgs",
                    return_value={"regular/icons/Glyph.svg": b"new"},
                ),
                mock.patch("builtins.print"),
            ):
                MAMBO_FONT.cmd_export([], dest_dir=out_dir)

            self.assertEqual(unrelated.read_text(), "keep\n")
            self.assertEqual(generated.read_bytes(), b"new")

    def test_explicit_export_removes_only_stale_managed_files(self):
        with tempfile.TemporaryDirectory(prefix="mambofont-export-test.") as directory:
            out_dir = Path(directory)
            unrelated = out_dir / "regular" / "icons" / "notes.svg"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_bytes(b"keep")

            with (
                mock.patch.object(
                    MAMBO_FONT,
                    "collect_all_svgs",
                    return_value={"regular/icons/Old.svg": b"old"},
                ),
                mock.patch("builtins.print"),
            ):
                MAMBO_FONT.cmd_export([], dest_dir=out_dir)

            with (
                mock.patch.object(
                    MAMBO_FONT,
                    "collect_all_svgs",
                    return_value={"regular/icons/New.svg": b"new"},
                ),
                mock.patch("builtins.print"),
            ):
                MAMBO_FONT.cmd_export([], dest_dir=out_dir)

            self.assertFalse((out_dir / "regular/icons/Old.svg").exists())
            self.assertEqual((out_dir / "regular/icons/New.svg").read_bytes(), b"new")
            self.assertEqual(unrelated.read_bytes(), b"keep")

    def test_export_rejects_paths_outside_destination(self):
        with tempfile.TemporaryDirectory(prefix="mambofont-export-test.") as directory:
            out_dir = Path(directory) / "output"
            escaped = Path(directory) / "escaped.svg"
            with (
                mock.patch.object(
                    MAMBO_FONT,
                    "collect_all_svgs",
                    return_value={"../escaped.svg": b"bad"},
                ),
                mock.patch("builtins.print"),
                self.assertRaises(SystemExit) as error,
            ):
                MAMBO_FONT.cmd_export([], dest_dir=out_dir)
            self.assertEqual(error.exception.code, 1)
            self.assertFalse(escaped.exists())

    def test_export_refuses_symlinked_managed_file(self):
        with tempfile.TemporaryDirectory(prefix="mambofont-export-test.") as directory:
            out_dir = Path(directory)
            old = out_dir / "regular/icons/Old.svg"
            unrelated = out_dir / "regular/icons/notes.svg"

            with (
                mock.patch.object(
                    MAMBO_FONT,
                    "collect_all_svgs",
                    return_value={"regular/icons/Old.svg": b"old"},
                ),
                mock.patch("builtins.print"),
            ):
                MAMBO_FONT.cmd_export([], dest_dir=out_dir)

            unrelated.write_bytes(b"keep")
            old.unlink()
            old.symlink_to(unrelated)
            with (
                mock.patch.object(
                    MAMBO_FONT,
                    "collect_all_svgs",
                    return_value={"regular/icons/New.svg": b"new"},
                ),
                mock.patch("builtins.print"),
                self.assertRaises(SystemExit) as error,
            ):
                MAMBO_FONT.cmd_export([], dest_dir=out_dir)

            self.assertEqual(error.exception.code, 1)
            self.assertTrue(old.is_symlink())
            self.assertEqual(unrelated.read_bytes(), b"keep")

    def test_export_refuses_symlinked_managed_directory(self):
        with tempfile.TemporaryDirectory(prefix="mambofont-export-test.") as directory:
            out_dir = Path(directory)
            old = out_dir / "regular/icons/Old.svg"

            with (
                mock.patch.object(
                    MAMBO_FONT,
                    "collect_all_svgs",
                    return_value={"regular/icons/Old.svg": b"old"},
                ),
                mock.patch("builtins.print"),
            ):
                MAMBO_FONT.cmd_export([], dest_dir=out_dir)

            old.unlink()
            old.parent.rmdir()
            unrelated_dir = out_dir / "unrelated"
            unrelated_dir.mkdir()
            unrelated = unrelated_dir / "Old.svg"
            unrelated.write_bytes(b"keep")
            old.parent.symlink_to(unrelated_dir, target_is_directory=True)

            with (
                mock.patch.object(
                    MAMBO_FONT,
                    "collect_all_svgs",
                    return_value={"regular/icons/New.svg": b"new"},
                ),
                mock.patch("builtins.print"),
                self.assertRaises(SystemExit) as error,
            ):
                MAMBO_FONT.cmd_export([], dest_dir=out_dir)

            self.assertEqual(error.exception.code, 1)
            self.assertEqual(unrelated.read_bytes(), b"keep")

    def test_filtered_export_removes_manifest_paths_when_source_is_now_empty(self):
        with tempfile.TemporaryDirectory(prefix="mambofont-export-test.") as directory:
            out_dir = Path(directory)
            stale = out_dir / "regular/icons/Old.svg"

            with (
                mock.patch.object(
                    MAMBO_FONT,
                    "collect_all_svgs",
                    return_value={"regular/icons/Old.svg": b"old"},
                ),
                mock.patch("builtins.print"),
            ):
                MAMBO_FONT.cmd_export([], dest_dir=out_dir)

            with (
                mock.patch.object(MAMBO_FONT, "collect_all_svgs", return_value={}),
                mock.patch("builtins.print"),
            ):
                MAMBO_FONT.cmd_export(["icons"], dest_dir=out_dir)

            self.assertFalse(stale.exists())

    def test_release_finishes_preflight_before_mutation(self):
        events = []
        svgs = {
            f"{folder}/icons/Glyph.svg": b"svg"
            for folder, _, _ in MAMBO_FONT.WEIGHTS
        }

        def build_weight(_svgs, folder_name, *_args, **_kwargs):
            events.append(("build", folder_name))
            return b"ttf", b"woff2"

        def edit_notes(seed_text=""):
            events.append(("notes", seed_text))
            return "Release notes"

        def run_project_command(args, **_kwargs):
            events.append(("command", *args))
            stdout = "main\n" if args == ["git", "branch", "--show-current"] else ""
            return subprocess.CompletedProcess(args, 0, stdout=stdout)

        with (
            mock.patch.object(MAMBO_FONT, "_ff", object()),
            mock.patch.object(MAMBO_FONT, "_check_git_auth"),
            mock.patch.object(MAMBO_FONT, "_release_exists", return_value=False),
            mock.patch.object(MAMBO_FONT, "collect_all_svgs", return_value=svgs),
            mock.patch.object(
                MAMBO_FONT, "build_weight_from_memory", side_effect=build_weight
            ),
            mock.patch.object(MAMBO_FONT, "_open_notes_in_nvim", side_effect=edit_notes),
            mock.patch.object(
                MAMBO_FONT, "_run_project_command", side_effect=run_project_command
            ),
            mock.patch("builtins.input", return_value="y"),
            mock.patch("builtins.print"),
        ):
            MAMBO_FONT.cmd_release("1.2.3")

        tag_index = next(
            i for i, event in enumerate(events) if event[:3] == ("command", "git", "tag")
        )
        push_index = next(
            i for i, event in enumerate(events) if event[:3] == ("command", "git", "push")
        )
        release_index = next(
            i
            for i, event in enumerate(events)
            if event[:4] == ("command", "gh", "release", "create")
        )
        first_build_index = next(
            i for i, event in enumerate(events) if event[0] == "build"
        )
        branch_index = events.index(("command", "git", "branch", "--show-current"))
        status_index = events.index(("command", "git", "status", "--porcelain"))
        self.assertLess(branch_index, first_build_index)
        self.assertLess(status_index, first_build_index)
        self.assertTrue(
            all(
                events.index(("build", folder)) < tag_index
                for folder, _, _ in MAMBO_FONT.WEIGHTS
            )
        )
        self.assertLess(events.index(("notes", "")), tag_index)
        self.assertLess(tag_index, push_index)
        self.assertLess(push_index, release_index)

    def test_release_defers_amend_deletion_until_after_notes(self):
        events = []
        svgs = {
            f"{folder}/icons/Glyph.svg": b"svg"
            for folder, _, _ in MAMBO_FONT.WEIGHTS
        }

        def edit_notes(seed_text=""):
            events.append(("notes", seed_text))
            return "Updated notes"

        def unrelease(*_args, **_kwargs):
            events.append(("unrelease",))

        with (
            mock.patch.object(MAMBO_FONT, "_ff", object()),
            mock.patch.object(MAMBO_FONT, "_validate_release_context"),
            mock.patch.object(MAMBO_FONT, "_check_git_auth"),
            mock.patch.object(MAMBO_FONT, "_release_exists", return_value=True),
            mock.patch.object(MAMBO_FONT, "_fetch_release_notes", return_value="Old notes"),
            mock.patch.object(MAMBO_FONT, "collect_all_svgs", return_value=svgs),
            mock.patch.object(
                MAMBO_FONT,
                "build_weight_from_memory",
                return_value=(b"ttf", b"woff2"),
            ),
            mock.patch.object(MAMBO_FONT, "_open_notes_in_nvim", side_effect=edit_notes),
            mock.patch.object(MAMBO_FONT, "cmd_unrelease", side_effect=unrelease),
            mock.patch.object(
                MAMBO_FONT,
                "_run_project_command",
                return_value=subprocess.CompletedProcess([], 0),
            ),
            mock.patch("builtins.input", return_value="y"),
            mock.patch("builtins.print"),
        ):
            MAMBO_FONT.cmd_release("1.2.3")

        self.assertLess(events.index(("notes", "Old notes")), events.index(("unrelease",)))

    def test_release_rolls_back_tags_when_publication_fails(self):
        events = []
        svgs = {
            f"{folder}/icons/Glyph.svg": b"svg"
            for folder, _, _ in MAMBO_FONT.WEIGHTS
        }

        def run_project_command(args, **_kwargs):
            events.append(args)
            if args[:3] == ["gh", "release", "create"]:
                raise subprocess.CalledProcessError(1, args)
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        with (
            mock.patch.object(MAMBO_FONT, "_ff", object()),
            mock.patch.object(MAMBO_FONT, "_validate_release_context"),
            mock.patch.object(MAMBO_FONT, "_check_git_auth"),
            mock.patch.object(MAMBO_FONT, "_release_exists", return_value=False),
            mock.patch.object(MAMBO_FONT, "collect_all_svgs", return_value=svgs),
            mock.patch.object(
                MAMBO_FONT,
                "build_weight_from_memory",
                return_value=(b"ttf", b"woff2"),
            ),
            mock.patch.object(MAMBO_FONT, "_open_notes_in_nvim", return_value="notes"),
            mock.patch.object(
                MAMBO_FONT, "_run_project_command", side_effect=run_project_command
            ),
            mock.patch("builtins.input", return_value="y"),
            mock.patch("builtins.print"),
            self.assertRaises(SystemExit) as error,
        ):
            MAMBO_FONT.cmd_release("1.2.3")

        self.assertEqual(error.exception.code, 1)
        self.assertIn(
            ["git", "push", "origin", ":refs/tags/v1.2.3"],
            events,
        )
        self.assertIn(["git", "tag", "-d", "v1.2.3"], events)

    def test_release_decline_does_not_mutate_git_or_github(self):
        events = []
        svgs = {
            f"{folder}/icons/Glyph.svg": b"svg"
            for folder, _, _ in MAMBO_FONT.WEIGHTS
        }

        def run_project_command(args, **_kwargs):
            events.append(args)
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        with (
            mock.patch.object(MAMBO_FONT, "_ff", object()),
            mock.patch.object(MAMBO_FONT, "_validate_release_context"),
            mock.patch.object(MAMBO_FONT, "_check_git_auth"),
            mock.patch.object(MAMBO_FONT, "_release_exists", return_value=False),
            mock.patch.object(MAMBO_FONT, "collect_all_svgs", return_value=svgs),
            mock.patch.object(
                MAMBO_FONT,
                "build_weight_from_memory",
                return_value=(b"ttf", b"woff2"),
            ),
            mock.patch.object(MAMBO_FONT, "_open_notes_in_nvim", return_value="notes"),
            mock.patch.object(
                MAMBO_FONT, "_run_project_command", side_effect=run_project_command
            ),
            mock.patch("builtins.input", return_value="n"),
            mock.patch("builtins.print"),
        ):
            MAMBO_FONT.cmd_release("1.2.3")

        self.assertFalse(any(args[:2] == ["git", "tag"] for args in events))
        self.assertFalse(any(args[:3] == ["gh", "release", "create"] for args in events))

    def test_unrelease_stops_before_local_mutation_when_remote_delete_fails(self):
        calls = []

        def run_project_command(args, **_kwargs):
            calls.append(args)
            if args[:3] == ["gh", "release", "delete"]:
                raise subprocess.CalledProcessError(1, args)
            return subprocess.CompletedProcess(args, 0, stdout="")

        with (
            mock.patch.object(MAMBO_FONT, "_check_git_auth"),
            mock.patch.object(MAMBO_FONT, "_release_exists", return_value=True),
            mock.patch.object(
                MAMBO_FONT, "_run_project_command", side_effect=run_project_command
            ),
            mock.patch("builtins.print"),
            self.assertRaises(SystemExit) as error,
        ):
            MAMBO_FONT.cmd_unrelease("1.2.3")

        self.assertEqual(error.exception.code, 1)
        self.assertEqual(
            calls,
            [["gh", "release", "delete", "v1.2.3", "--cleanup-tag", "--yes"]],
        )

    def test_unrelease_cleans_tag_only_state(self):
        calls = []

        def run_project_command(args, **_kwargs):
            calls.append(args)
            stdout = "v1.2.3\n" if args[:3] == ["git", "tag", "--list"] else ""
            return subprocess.CompletedProcess(args, 0, stdout=stdout)

        with (
            mock.patch.object(MAMBO_FONT, "_check_git_auth"),
            mock.patch.object(MAMBO_FONT, "_release_exists", return_value=False),
            mock.patch.object(
                MAMBO_FONT, "_run_project_command", side_effect=run_project_command
            ),
            mock.patch("builtins.print"),
        ):
            MAMBO_FONT.cmd_unrelease("1.2.3")

        self.assertEqual(
            calls,
            [
                ["git", "push", "origin", ":refs/tags/v1.2.3"],
                ["git", "tag", "--list", "v1.2.3"],
                ["git", "tag", "-d", "v1.2.3"],
            ],
        )

    def test_installer_uses_configured_directory_and_refuses_files(self):
        with tempfile.TemporaryDirectory(prefix="mambofont-test.") as directory:
            root = Path(directory)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            environment = os.environ.copy()
            environment["MAMBOFONT_BIN_DIR"] = str(bin_dir)

            subprocess.run(
                [SCRIPT_DIR / "install.sh"],
                check=True,
                capture_output=True,
                env=environment,
            )
            command = bin_dir / "mbfont"
            self.assertTrue(command.is_symlink())
            self.assertEqual(command.resolve(), MODULE_PATH)
            help_result = subprocess.run(
                [command, "--help"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("export", help_result.stdout)

            conflict_dir = root / "conflict"
            conflict_dir.mkdir()
            conflict = conflict_dir / "mbfont"
            conflict.write_text("keep\n")
            environment["MAMBOFONT_BIN_DIR"] = str(conflict_dir)
            result = subprocess.run(
                [SCRIPT_DIR / "install.sh"],
                capture_output=True,
                env=environment,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(conflict.read_text(), "keep\n")


if __name__ == "__main__":
    unittest.main()
