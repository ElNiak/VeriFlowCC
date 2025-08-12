"""Tests for PathConfig class - configurable base directory for .agilevv folder."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from verifflowcc.core.path_config import PathConfig


class TestPathConfigBasics:
    """Test basic PathConfig functionality."""

    def test_default_base_directory(self) -> None:
        """Test that PathConfig defaults to .agilevv directory."""
        config = PathConfig()
        assert config.base_dir == Path.cwd() / ".agilevv"
        assert config.base_dir.name == ".agilevv"

    def test_custom_base_directory(self, tmp_path: Path) -> None:
        """Test PathConfig with custom base directory."""
        custom_path = tmp_path / "test-agilevv"
        config = PathConfig(base_dir=custom_path)
        assert config.base_dir == custom_path
        assert str(config.base_dir).endswith("test-agilevv")

    def test_base_directory_from_string(self, tmp_path: Path) -> None:
        """Test PathConfig accepts string paths."""
        path_str = str(tmp_path / "custom-agilevv")
        config = PathConfig(base_dir=path_str)
        assert config.base_dir == Path(path_str)
        assert isinstance(config.base_dir, Path)

    def test_relative_base_directory(self) -> None:
        """Test PathConfig handles relative paths correctly."""
        config = PathConfig(base_dir="custom/.agilevv")
        expected = Path.cwd() / "custom" / ".agilevv"
        assert config.base_dir == expected


class TestEnvironmentVariable:
    """Test environment variable support for PathConfig."""

    def test_env_var_override(self, tmp_path: Path) -> None:
        """Test AGILEVV_BASE_DIR environment variable overrides default."""
        env_path = str(tmp_path / "env-agilevv")
        with patch.dict(os.environ, {"AGILEVV_BASE_DIR": env_path}):
            config = PathConfig()
            assert config.base_dir == Path(env_path)

    def test_env_var_with_explicit_base_dir(self, tmp_path: Path) -> None:
        """Test explicit base_dir takes precedence over environment variable."""
        env_path = str(tmp_path / "env-agilevv")
        explicit_path = str(tmp_path / "explicit-agilevv")
        with patch.dict(os.environ, {"AGILEVV_BASE_DIR": env_path}):
            config = PathConfig(base_dir=explicit_path)
            assert config.base_dir == Path(explicit_path)

    def test_env_var_empty_string(self) -> None:
        """Test empty AGILEVV_BASE_DIR falls back to default."""
        with patch.dict(os.environ, {"AGILEVV_BASE_DIR": ""}):
            config = PathConfig()
            assert config.base_dir == Path.cwd() / ".agilevv"

    def test_env_var_with_home_expansion(self) -> None:
        """Test environment variable with ~ expands to home directory."""
        with patch.dict(os.environ, {"AGILEVV_BASE_DIR": "~/.agilevv-test"}):
            config = PathConfig()
            assert config.base_dir == Path.home() / ".agilevv-test"


class TestPathResolution:
    """Test path resolution methods for subdirectories."""

    def test_config_path(self, tmp_path: Path) -> None:
        """Test config.yaml path resolution."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        assert config.config_path == test_dir / "config.yaml"
        assert config.config_path.parent == config.base_dir

    def test_state_path(self, tmp_path: Path) -> None:
        """Test state.json path resolution."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        assert config.state_path == test_dir / "state.json"
        assert config.state_path.parent == config.base_dir

    def test_backlog_path(self, tmp_path: Path) -> None:
        """Test backlog.md path resolution."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        assert config.backlog_path == test_dir / "backlog.md"

    def test_architecture_path(self, tmp_path: Path) -> None:
        """Test architecture.md path resolution."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        assert config.architecture_path == test_dir / "architecture.md"

    def test_requirements_dir(self, tmp_path: Path) -> None:
        """Test requirements directory path resolution."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        assert config.requirements_dir == test_dir / "requirements"
        assert config.requirements_dir.parent == config.base_dir

    def test_c4_diagrams_dir(self, tmp_path: Path) -> None:
        """Test C4 diagrams directory path resolution."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        assert config.c4_diagrams_dir == test_dir / "c4" / "diagrams"
        assert config.c4_diagrams_dir.parts[-2:] == ("c4", "diagrams")

    def test_checkpoints_dir(self, tmp_path: Path) -> None:
        """Test checkpoints directory path resolution."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        assert config.checkpoints_dir == test_dir / "checkpoints"

    def test_logs_dir(self, tmp_path: Path) -> None:
        """Test logs directory path resolution."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        assert config.logs_dir == test_dir / "logs"

    def test_get_artifact_path(self, tmp_path: Path) -> None:
        """Test generic artifact path resolution."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        artifact_path = config.get_artifact_path("custom/artifact.json")
        assert artifact_path == test_dir / "custom" / "artifact.json"
        assert str(test_dir) in str(artifact_path)

    def test_get_artifact_path_absolute_rejected(self, tmp_path: Path) -> None:
        """Test that absolute paths in artifacts are rejected."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        with pytest.raises(ValueError, match="Artifact path cannot be absolute"):
            config.get_artifact_path("/etc/passwd")

    def test_get_artifact_path_parent_traversal_rejected(self, tmp_path: Path) -> None:
        """Test that parent directory traversal in artifacts is rejected."""
        test_dir = tmp_path / "test"
        config = PathConfig(base_dir=test_dir)
        with pytest.raises(
            ValueError, match="Artifact path cannot contain parent directory references"
        ):
            config.get_artifact_path("../../../etc/passwd")


class TestDirectoryCreation:
    """Test directory creation functionality."""

    def test_ensure_base_exists_creates_directory(self, tmp_path: Path) -> None:
        """Test ensure_base_exists creates the base directory."""
        base_dir = tmp_path / "new-agilevv"
        config = PathConfig(base_dir=base_dir)

        assert not base_dir.exists()
        config.ensure_base_exists()
        assert base_dir.exists()
        assert base_dir.is_dir()

    def test_ensure_base_exists_idempotent(self, tmp_path: Path) -> None:
        """Test ensure_base_exists is idempotent."""
        base_dir = tmp_path / "existing-agilevv"
        base_dir.mkdir()

        config = PathConfig(base_dir=base_dir)
        config.ensure_base_exists()  # Should not raise
        assert base_dir.exists()
        assert base_dir.is_dir()

    def test_ensure_structure_creates_all_directories(self, tmp_path: Path) -> None:
        """Test ensure_structure creates all required subdirectories."""
        base_dir = tmp_path / "structured-agilevv"
        config = PathConfig(base_dir=base_dir)

        config.ensure_structure()

        assert base_dir.exists()
        assert config.requirements_dir.exists()
        assert config.c4_diagrams_dir.exists()
        assert config.checkpoints_dir.exists()
        assert config.logs_dir.exists()

    def test_ensure_structure_creates_config_files(self, tmp_path: Path) -> None:
        """Test ensure_structure creates default config files if not present."""
        base_dir = tmp_path / "structured-agilevv"
        config = PathConfig(base_dir=base_dir)

        config.ensure_structure(create_defaults=True)

        assert config.config_path.exists()
        assert config.state_path.exists()

        # Verify default content
        import json

        import yaml

        with config.config_path.open() as f:
            config_data = yaml.safe_load(f)
            assert "version" in config_data

        with config.state_path.open() as f:
            state_data = json.load(f)
            assert "current_sprint" in state_data


class TestPathValidation:
    """Test path validation and error handling."""

    def test_validate_path_exists(self, tmp_path: Path) -> None:
        """Test validate_path for existing paths."""
        existing_file = tmp_path / "test.txt"
        existing_file.write_text("test")

        config = PathConfig(base_dir=tmp_path)
        assert config.validate_path(existing_file) is True

    def test_validate_path_not_exists(self, tmp_path: Path) -> None:
        """Test validate_path for non-existing paths."""
        config = PathConfig(base_dir=tmp_path)
        non_existing = tmp_path / "missing.txt"
        assert config.validate_path(non_existing) is False

    def test_validate_path_outside_base_dir(self, tmp_path: Path) -> None:
        """Test validate_path rejects paths outside base directory."""
        config = PathConfig(base_dir=tmp_path / "agilevv")
        outside_path = tmp_path / "outside.txt"

        with pytest.raises(ValueError, match="is outside base directory"):
            config.validate_path(outside_path, must_be_inside=True)

    def test_is_test_environment(self) -> None:
        """Test detection of test environment."""
        # In pytest environment
        config = PathConfig()
        assert config.is_test_environment() is True

        # Simulate non-test environment
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": ""}):
            config = PathConfig()
            # Still true because we're running under pytest
            assert config.is_test_environment() is True


class TestPathConfigEquality:
    """Test PathConfig equality and hashing."""

    def test_equality_same_base_dir(self, tmp_path: Path) -> None:
        """Test two PathConfig instances with same base_dir are equal."""
        test_dir = tmp_path / "test"
        config1 = PathConfig(base_dir=test_dir)
        config2 = PathConfig(base_dir=test_dir)
        assert config1 == config2

    def test_inequality_different_base_dir(self, tmp_path: Path) -> None:
        """Test two PathConfig instances with different base_dir are not equal."""
        config1 = PathConfig(base_dir=tmp_path / "test1")
        config2 = PathConfig(base_dir=tmp_path / "test2")
        assert config1 != config2

    def test_hash_consistency(self, tmp_path: Path) -> None:
        """Test PathConfig instances can be used in sets/dicts."""
        test_dir = tmp_path / "test"
        other_dir = tmp_path / "other"
        config1 = PathConfig(base_dir=test_dir)
        config2 = PathConfig(base_dir=test_dir)
        config3 = PathConfig(base_dir=other_dir)

        config_set = {config1, config2, config3}
        assert len(config_set) == 2  # config1 and config2 are same


class TestPathConfigString:
    """Test string representations of PathConfig."""

    def test_str_representation(self, tmp_path: Path) -> None:
        """Test __str__ returns readable string."""
        test_dir = tmp_path / "test-agilevv"
        config = PathConfig(base_dir=test_dir)
        assert str(config) == f"PathConfig(base_dir={test_dir})"

    def test_repr_representation(self, tmp_path: Path) -> None:
        """Test __repr__ returns valid Python expression."""
        test_dir = tmp_path / "test-agilevv"
        config = PathConfig(base_dir=test_dir)
        assert "PathConfig(base_dir=" in repr(config)
        assert str(test_dir) in repr(config)


class TestTestIsolation:
    """Test specific test isolation features."""

    def test_create_isolated_instance(self, tmp_path: Path) -> None:
        """Test creating an isolated PathConfig for tests."""
        test_dir = tmp_path / ".agilevv-test"
        config = PathConfig.create_test_instance(test_dir)

        assert config.base_dir == test_dir
        assert ".agilevv-test" in str(config.base_dir)
        assert config.is_test_environment()

    def test_with_test_isolation_context_manager(self, tmp_path: Path) -> None:
        """Test context manager for temporary test isolation."""
        test_dir = tmp_path / ".agilevv-test-context"

        with PathConfig.test_isolation(test_dir) as config:
            assert config.base_dir == test_dir
            assert test_dir.exists()

            # Create some test files
            config.ensure_structure()
            assert config.requirements_dir.exists()

        # Directory still exists after context (cleanup is optional)
        assert test_dir.exists()

    def test_cleanup_test_directory(self, tmp_path: Path) -> None:
        """Test cleanup of test directories."""
        test_dir = tmp_path / ".agilevv-test-cleanup"
        config = PathConfig(base_dir=test_dir)
        config.ensure_structure()

        assert test_dir.exists()
        config.cleanup()
        assert not test_dir.exists()

    def test_cleanup_preserves_non_test_directories(self, tmp_path: Path) -> None:
        """Test cleanup does not remove production directories."""
        prod_dir = tmp_path / ".agilevv"
        config = PathConfig(base_dir=prod_dir)
        config.ensure_structure()

        with pytest.raises(ValueError, match="Cannot cleanup non-test directory"):
            config.cleanup()

        assert prod_dir.exists()  # Should still exist
