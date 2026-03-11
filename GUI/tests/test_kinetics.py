"""Tests for kinetics .hh code generation, parsing, and cross-validation.

Verifies that generated kinetics code is syntactically valid C++,
contains required function signatures, and that the cross-validation
logic correctly catches mismatches between .hh code and project config.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.kinetics_templates import (
    TEMPLATE_KINETICS, KineticsInfo, get_kinetics_info,
    parse_hh_indices, verify_function_signature,
    validate_kinetics_vs_project,
)
from src.core.templates import create_from_template


EXPECTED_KEYS = [
    "flow_only", "diffusion_only", "tracer_transport",
    "abiotic_reaction", "abiotic_equilibrium",
    "biotic_sessile", "biotic_planktonic",
    "biotic_sessile_planktonic", "coupled_biotic_abiotic",
]


class TestKineticsRegistry:
    """All 9 template keys must have kinetics metadata."""

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_key_in_registry(self, key):
        info = get_kinetics_info(key)
        assert info is not None
        assert isinstance(info, KineticsInfo)

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_both_hh_provided(self, key):
        info = get_kinetics_info(key)
        assert info.biotic_hh is not None
        assert len(info.biotic_hh) > 0
        assert info.abiotic_hh is not None
        assert len(info.abiotic_hh) > 0

    def test_unknown_key_returns_none(self):
        assert get_kinetics_info("nonexistent") is None


class TestHHCodeValidity:
    """Every generated .hh must contain required C++ constructs."""

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_biotic_has_define_guard(self, key):
        info = get_kinetics_info(key)
        assert "#ifndef DEFINE_KINETICS_HH" in info.biotic_hh
        assert "#define DEFINE_KINETICS_HH" in info.biotic_hh
        assert "#endif" in info.biotic_hh

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_abiotic_has_define_guard(self, key):
        info = get_kinetics_info(key)
        assert "#ifndef DEFINE_ABIOTIC_KINETICS_HH" in info.abiotic_hh
        assert "#define DEFINE_ABIOTIC_KINETICS_HH" in info.abiotic_hh
        assert "#endif" in info.abiotic_hh

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_biotic_has_function(self, key):
        info = get_kinetics_info(key)
        assert "defineRxnKinetics" in info.biotic_hh

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_abiotic_has_function(self, key):
        info = get_kinetics_info(key)
        assert "defineAbioticRxnKinetics" in info.abiotic_hh

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_biotic_has_kinetics_stats(self, key):
        info = get_kinetics_info(key)
        assert "KineticsStats" in info.biotic_hh

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_includes_vector(self, key):
        info = get_kinetics_info(key)
        assert "#include <vector>" in info.biotic_hh
        assert "#include <vector>" in info.abiotic_hh


class TestFunctionSignatureVerification:

    def test_valid_biotic(self):
        info = get_kinetics_info("biotic_sessile")
        errors = verify_function_signature(info.biotic_hh, "biotic")
        assert len(errors) == 0

    def test_valid_abiotic(self):
        info = get_kinetics_info("abiotic_reaction")
        errors = verify_function_signature(info.abiotic_hh, "abiotic")
        assert len(errors) == 0

    def test_missing_function_detected(self):
        bad_code = "#include <vector>\nvoid wrongName() {}\n"
        errors = verify_function_signature(bad_code, "biotic")
        assert len(errors) > 0
        assert "defineRxnKinetics" in errors[0]

    def test_missing_kinetics_stats_detected(self):
        bad_code = """
        #include <vector>
        void defineRxnKinetics(
            std::vector<double> B,
            std::vector<double> C,
            std::vector<double>& subsR,
            std::vector<double>& bioR,
            plb::plint mask) {}
        """
        errors = verify_function_signature(bad_code, "biotic")
        assert any("KineticsStats" in e for e in errors)

    def test_empty_source_no_errors(self):
        errors = verify_function_signature("", "biotic")
        assert len(errors) == 0


class TestHHIndexParsing:

    def test_simple_indices(self):
        code = "subsR[0] = -rate;\nsubsR[1] = rate;\nC[0] = x;\n"
        idx = parse_hh_indices(code)
        assert idx["subsR"] == [0, 1]
        assert idx["C"] == [0]

    def test_comments_ignored(self):
        code = "// subsR[5] = x;\nsubsR[0] = y;\n"
        idx = parse_hh_indices(code)
        assert idx["subsR"] == [0]

    def test_size_checks_ignored(self):
        # Lines containing .size() are skipped by parse_hh_indices
        code = "if (C.size() > 2) { }\nC[0] = 1;\n"
        idx = parse_hh_indices(code)
        assert idx.get("C", []) == [0]


class TestCrossValidation:
    """Test that kinetics vs project cross-validation catches errors."""

    def test_valid_template_passes(self):
        p = create_from_template("biotic_sessile")
        errors = validate_kinetics_vs_project(
            biotic_source=p.kinetics_source,
            abiotic_source=p.abiotic_kinetics_source,
            num_substrates=len(p.substrates),
            num_microbes=len(p.microbiology.microbes),
            biotic_mode=True, enable_kinetics=True, enable_abiotic=False,
        )
        assert len(errors) == 0

    def test_substrate_index_out_of_bounds(self):
        # Use dual-microbe kinetics but only 0 substrates
        info = get_kinetics_info("biotic_sessile")
        errors = validate_kinetics_vs_project(
            biotic_source=info.biotic_hh,
            abiotic_source=info.abiotic_hh,
            num_substrates=0,
            num_microbes=1,
            biotic_mode=True, enable_kinetics=True, enable_abiotic=False,
        )
        assert any("C[" in e for e in errors)

    def test_microbe_index_out_of_bounds(self):
        # Use dual-microbe kinetics but only 1 microbe
        info = get_kinetics_info("biotic_sessile_planktonic")
        errors = validate_kinetics_vs_project(
            biotic_source=info.biotic_hh,
            abiotic_source=info.abiotic_hh,
            num_substrates=1,
            num_microbes=1,
            biotic_mode=True, enable_kinetics=True, enable_abiotic=False,
        )
        assert any("B[" in e for e in errors)

    def test_empty_biotic_source_flagged(self):
        errors = validate_kinetics_vs_project(
            biotic_source="",
            abiotic_source="",
            num_substrates=1,
            num_microbes=1,
            biotic_mode=True, enable_kinetics=True, enable_abiotic=False,
        )
        assert any("empty" in e.lower() or "missing" in e.lower() for e in errors)

    def test_abiotic_empty_source_flagged(self):
        errors = validate_kinetics_vs_project(
            biotic_source="stub",
            abiotic_source="",
            num_substrates=2,
            num_microbes=0,
            biotic_mode=False, enable_kinetics=False, enable_abiotic=True,
        )
        assert any("empty" in e.lower() or "missing" in e.lower() for e in errors)
