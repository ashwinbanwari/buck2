# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under both the MIT license found in the
# LICENSE-MIT file in the root directory of this source tree and the Apache
# License, Version 2.0 found in the LICENSE-APACHE file in the root directory
# of this source tree.

# pyre-strict


import json
import re
from pathlib import Path
from typing import List

from buck2.tests.e2e_util.api.buck import Buck
from buck2.tests.e2e_util.buck_workspace import buck_test

from .test_test_coverage_utils import collect_coverage_for


@buck_test(inplace=True)
async def test_rust_test_coverage(buck: Buck, tmp_path: Path) -> None:
    coverage_file = tmp_path / "coverage.txt"
    await buck.test(
        "@fbcode//mode/dbgo-cov",
        "fbcode//buck2/tests/targets/rules/rust:tests_pass",
        "--",
        "--collect-coverage",
        f"--coverage-output={coverage_file}",
    )
    paths = []
    with open(coverage_file) as results:
        for line in results:
            paths.append(json.loads(line)["filepath"])
    assert "fbcode/buck2/tests/targets/rules/rust/tests_pass.rs" in paths, str(paths)


@buck_test(inplace=True)
async def test_rust_test_coverage_filtering_by_path_of_target(
    buck: Buck,
    tmp_path: Path,
) -> None:
    paths = await collect_coverage_for(
        buck,
        tmp_path,
        "fbcode//buck2/tests/targets/rules/rust:tests_pass",
        ["buck2/tests"],
    )

    unexpected_paths = [p for p in paths if not p.startswith("fbcode/buck2/tests")]
    assert len(unexpected_paths) == 0, str(paths)


@buck_test(inplace=True)
async def test_rust_test_coverage_of_rust_library_filtering_by_path_outside_of_target(
    buck: Buck,
    tmp_path: Path,
) -> None:
    paths = await collect_coverage_for(
        buck,
        tmp_path,
        "buck2/tests/targets/rules/rust/coverage/test_with_rust_library_outside_targets_path:test",
        ["testing_frameworks"],
    )

    fbcode_filename = "fbcode/testing_frameworks/code_coverage/adder.rs"
    expected_paths = [p for p in paths if p == fbcode_filename]
    assert len(expected_paths) > 0, str(paths)
    unexpected_paths = [p for p in paths if p != fbcode_filename]
    assert len(unexpected_paths) == 0, str(paths)


@buck_test(inplace=True)
async def test_rust_test_coverage_of_cpp_file_filtering_by_file_with_cxx(
    buck: Buck, tmp_path: Path
) -> None:
    file_to_collect_coverage = "testing_frameworks/code_coverage/rust/Adder.cpp"
    paths = await collect_coverage_for(
        buck,
        tmp_path,
        "testing_frameworks/code_coverage/rust:tests_with_cxx_cpp_dep",
        [file_to_collect_coverage],
    )

    fbcode_filename = f"fbcode/{file_to_collect_coverage}"
    assert paths == [fbcode_filename], str(paths)


@buck_test(inplace=True)
async def test_rust_test_coverage_of_cpp_file_filtering_by_file_with_cxx_through_rust_library(
    buck: Buck, tmp_path: Path
) -> None:
    file_to_collect_coverage = "testing_frameworks/code_coverage/rust/Adder.cpp"
    paths = await collect_coverage_for(
        buck,
        tmp_path,
        "testing_frameworks/code_coverage/rust:tests_with_cxx_rust_library_dep",
        [file_to_collect_coverage],
    )

    fbcode_filename = f"fbcode/{file_to_collect_coverage}"
    assert paths == [fbcode_filename], str(paths)


@buck_test(inplace=True)
async def test_rust_test_coverage_of_cpp_file_filtering_by_file_with_cxx_on_autogenerated_library_unittests(
    buck: Buck, tmp_path: Path
) -> None:
    file_to_collect_coverage = "testing_frameworks/code_coverage/rust/Adder.cpp"
    paths = await collect_coverage_for(
        buck,
        tmp_path,
        "testing_frameworks/code_coverage/rust:tests_in_library-unittest",
        [file_to_collect_coverage],
    )

    fbcode_filename = f"fbcode/{file_to_collect_coverage}"
    assert paths == [fbcode_filename], str(paths)


@buck_test(inplace=True)
async def test_rust_test_coverage_of_cpp_file_filtering_by_file_with_bindgen_rust_library(
    buck: Buck, tmp_path: Path
) -> None:
    file_to_collect_coverage = "testing_frameworks/code_coverage/rust/AdderC.cpp"
    paths = await collect_coverage_for(
        buck,
        tmp_path,
        "testing_frameworks/code_coverage/rust:tests_with_bindgen_rust_library_dep",
        [file_to_collect_coverage],
    )

    fbcode_filename = f"fbcode/{file_to_collect_coverage}"
    assert paths == [fbcode_filename], str(paths)


@buck_test(inplace=True)
async def test_rust_test_coverage_of_cpp_file_filtering_by_file_with_ligen_cpp_dep(
    buck: Buck, tmp_path: Path
) -> None:
    file_to_collect_coverage = "testing_frameworks/code_coverage/rust/AdderLigen.cpp"
    paths = await collect_coverage_for(
        buck,
        tmp_path,
        "testing_frameworks/code_coverage/rust:test_with_ligen_cpp_dep",
        [file_to_collect_coverage],
    )

    fbcode_filename = f"fbcode/{file_to_collect_coverage}"
    assert paths == [fbcode_filename], str(paths)


def any_item_matches(items: List[str], regex: str) -> bool:
    for i in items:
        if re.fullmatch(regex, i):
            return True
    return False


@buck_test(inplace=True)
async def test_rust_test_coverage_of_cpp_file_filtering_by_header_with_cxx(
    buck: Buck, tmp_path: Path
) -> None:
    paths = await collect_coverage_for(
        buck,
        tmp_path,
        "testing_frameworks/code_coverage/rust:tests_with_code_in_cpp_header",
        ["testing_frameworks/code_coverage/rust/AdderWithHeaderCode.h"],
    )

    assert len(paths) == 3, str(paths)
    assert (
        "fbcode/testing_frameworks/code_coverage/rust/AdderWithHeaderCode.cpp" in paths
    ), str(paths)
    assert (
        "fbcode/testing_frameworks/code_coverage/rust/AdderWithHeaderCode.h" in paths
    ), str(paths)
    assert any_item_matches(
        paths,
        r"fbcode/[a-z0-9]+/testing_frameworks/code_coverage/rust/__tests_with_code_in_cpp_header-bridge_generated.cc__/out/generated.cc",
    ), str(paths)