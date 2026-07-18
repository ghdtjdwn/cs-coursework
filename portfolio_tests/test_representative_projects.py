from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
        **kwargs,
    )


def encode_i(immediate: int, rs1: int, funct3: int, rd: int, opcode: int = 0x13) -> str:
    instruction = (
        ((immediate & 0xFFF) << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | opcode
    )
    return f"{instruction:032b}"


def encode_r(funct7: int, rs2: int, rs1: int, funct3: int, rd: int) -> str:
    instruction = (
        (funct7 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (funct3 << 12)
        | (rd << 7)
        | 0x33
    )
    return f"{instruction:032b}"


class RepresentativeProjectsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.build = Path(cls.tempdir.name)
        cls.c_compiler = shutil.which("cc")
        cls.cpp_compiler = shutil.which("c++")
        if not cls.c_compiler or not cls.cpp_compiler:
            raise unittest.SkipTest("C and C++ compilers are required")

        commands = [
            [
                cls.cpp_compiler,
                "-std=c++20",
                "-O2",
                "-Wall",
                "-Wextra",
                "Programming_Languages/interpreter.cpp",
                "-o",
                str(cls.build / "interpreter_cpp"),
            ],
            [
                cls.c_compiler,
                "-std=c11",
                "-O2",
                "-Wall",
                "-Wextra",
                "Computer_Architecture/src/main.c",
                "-o",
                str(cls.build / "riscv_sim"),
            ],
            [
                cls.cpp_compiler,
                "-std=c++20",
                "-O2",
                "-Wall",
                "-Wextra",
                "-IAlgorithm/src",
                "portfolio_tests/algorithm_harness.cpp",
                "-o",
                str(cls.build / "algorithm_harness"),
            ],
        ]
        for command in commands:
            result = run(command)
            if result.returncode != 0:
                raise AssertionError(f"build failed: {' '.join(command)}\n{result.stderr}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tempdir.cleanup()

    def test_python_and_cpp_interpreters_share_the_same_contract(self) -> None:
        programs = "\n".join(
            [
                "variable a; a = (1 + 2) * 3; print a;",
                (
                    "constant n = 3; variable s; variable i; s = 0; i = 0; "
                    "repeat begin s = s + i; i = i + 1; end until (i > n); print s;"
                ),
                "constant locked = 1; locked = 2;",
                "",
            ]
        )
        expected = "9\n6\nSyntax Error!\n"

        python_result = run(
            [sys.executable, "Programming_Languages/interpreter.py"], input=programs
        )
        cpp_result = run([str(self.build / "interpreter_cpp")], input=programs)

        self.assertEqual(python_result.returncode, 0, python_result.stderr)
        self.assertEqual(cpp_result.returncode, 0, cpp_result.stderr)
        self.assertEqual(python_result.stdout, expected)
        self.assertEqual(cpp_result.stdout, expected)

    def test_riscv_disassembly_and_execution(self) -> None:
        binary = self.build / "sample.bin"
        binary.write_text(
            "\n".join(
                [
                    encode_i(5, rs1=1, funct3=0, rd=1),
                    encode_r(0, rs2=3, rs1=1, funct3=0, rd=2),
                ]
            )
            + "\n",
            encoding="ascii",
        )

        result = run([str(self.build / "riscv_sim")], input=f"{binary}\nterminate\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            ">> Final values in PC, x1, x2, x3, x4, x5 are 1004, 6, 9, 3, 4, 5",
            result.stdout,
        )
        self.assertEqual(
            binary.with_suffix(".s").read_text(encoding="utf-8"),
            "ADDI x1, x1, 5\nADD x2, x1, x3\n",
        )

    def test_riscv_rejects_malformed_instruction(self) -> None:
        malformed = self.build / "malformed.bin"
        malformed.write_text("101\n", encoding="ascii")

        result = run([str(self.build / "riscv_sim")], input=f"{malformed}\nterminate\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(">> Instruction Format Error!", result.stdout)
        self.assertFalse(malformed.with_suffix(".s").exists())

    def test_all_sorting_implementations_are_ordered_and_copy_free(self) -> None:
        result = run([str(self.build / "algorithm_harness")])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "4 sorting algorithms passed with zero copies\n")

    def test_curated_public_surface_has_no_generic_identity_markers(self) -> None:
        result = run([sys.executable, "scripts/audit_public_surface.py"])

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_full_privacy_audit_reports_history_without_disclosing_matches(self) -> None:
        result = run([sys.executable, "scripts/audit_public_surface.py", "--full"])

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["history_review"]["reviewed"])
        self.assertGreater(report["history_review"]["commit_count"], 0)
        self.assertFalse(report["safe_to_claim_repository_wide_privacy"])
        self.assertNotIn("@", result.stdout)


if __name__ == "__main__":
    unittest.main()
