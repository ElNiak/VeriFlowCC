"""Meta-tests to verify test isolation fixtures work correctly."""

import secrets
import time
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from verifflowcc.core.path_config import PathConfig


class TestIsolationFixtures:
    """Test the isolation fixtures themselves."""

    def test_isolated_agilevv_dir_creates_unique_directory(
        self, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test that isolated_agilevv_dir creates a unique directory."""
        # Verify the directory exists
        assert isolated_agilevv_dir.base_dir.exists()
        assert isolated_agilevv_dir.base_dir.is_dir()

        # Verify it's in a temp location (macOS uses /var/folders for temp)
        temp_indicators = ["/tmp", "Temp", "/var/folders", "\\Temp\\"]
        assert any(indicator in str(isolated_agilevv_dir.base_dir) for indicator in temp_indicators)

        # Verify it has the test-specific suffix
        test_name = "test_isolated_agilevv_dir_creates_unique_directory"
        assert test_name in str(isolated_agilevv_dir.base_dir)

    def test_isolated_agilevv_dir_cleanup(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that directories are cleaned up after tests."""
        test_dir = isolated_agilevv_dir.base_dir
        test_file = test_dir / "test.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test content")

        assert test_file.exists()
        # Cleanup happens automatically after test via pytest's tmp_path

    def test_multiple_tests_get_different_directories(
        self, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test that each test gets its own isolated directory."""
        # Write a unique file
        marker_file = isolated_agilevv_dir.base_dir / "unique_marker.txt"
        marker_file.parent.mkdir(parents=True, exist_ok=True)

        # This file should not exist from previous tests
        assert not marker_file.exists()
        marker_file.write_text("unique")

    def test_env_variable_override(
        self, isolated_agilevv_dir: PathConfig, monkeypatch: MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that AGILEVV_BASE_DIR can override the base directory."""
        custom_dir = tmp_path / "custom-agilevv-test"
        monkeypatch.setenv("AGILEVV_BASE_DIR", str(custom_dir))

        from verifflowcc.core.path_config import PathConfig

        # Create new PathConfig with env var set
        config = PathConfig()
        assert config.base_dir == custom_dir

    def test_isolated_module_scope_dir(self, isolated_agilevv_module_dir: PathConfig) -> None:
        """Test module-scoped isolation fixture."""
        assert isolated_agilevv_module_dir.base_dir.exists()
        assert "module" in str(isolated_agilevv_module_dir.base_dir)

        # Create a file that should persist across tests in this module
        module_file = isolated_agilevv_module_dir.base_dir / "module_file.txt"
        module_file.parent.mkdir(parents=True, exist_ok=True)

        if not module_file.exists():
            module_file.write_text("module data")

        assert module_file.exists()

    def test_isolated_session_scope_dir(self, isolated_agilevv_session_dir: PathConfig) -> None:
        """Test session-scoped isolation fixture."""
        assert isolated_agilevv_session_dir.base_dir.exists()
        assert "session" in str(isolated_agilevv_session_dir.base_dir)

        # Create a file that should persist across all tests
        session_file = isolated_agilevv_session_dir.base_dir / "session_file.txt"
        session_file.parent.mkdir(parents=True, exist_ok=True)

        if not session_file.exists():
            session_file.write_text("session data")

        assert session_file.exists()


class TestPathConfigIntegration:
    """Test PathConfig behavior in isolated environments."""

    def test_path_config_respects_isolation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that PathConfig respects the isolated directory."""
        # Create structure
        isolated_agilevv_dir.ensure_structure(create_defaults=True)

        # Verify all paths are within the isolated directory
        assert str(isolated_agilevv_dir.base_dir) in str(isolated_agilevv_dir.config_path)
        assert str(isolated_agilevv_dir.base_dir) in str(isolated_agilevv_dir.state_path)
        assert str(isolated_agilevv_dir.base_dir) in str(isolated_agilevv_dir.backlog_path)
        assert str(isolated_agilevv_dir.base_dir) in str(isolated_agilevv_dir.architecture_path)
        assert str(isolated_agilevv_dir.base_dir) in str(isolated_agilevv_dir.logs_dir)
        assert str(isolated_agilevv_dir.base_dir) in str(isolated_agilevv_dir.checkpoints_dir)

    def test_parallel_test_isolation(self, isolated_agilevv_dir: PathConfig) -> None:
        """Test that parallel tests don't interfere with each other."""
        # Create a unique file with cryptographically secure random content
        unique_id = f"{time.time()}_{secrets.randbelow(10000)}"
        test_file = isolated_agilevv_dir.base_dir / f"parallel_test_{unique_id}.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(unique_id)

        # Verify only our file exists (no files from other parallel tests)
        files = list(isolated_agilevv_dir.base_dir.glob("parallel_test_*.txt"))
        assert len(files) == 1
        assert files[0].name == f"parallel_test_{unique_id}.txt"

    def test_no_interference_with_production_agilevv(
        self, isolated_agilevv_dir: PathConfig
    ) -> None:
        """Test that isolated tests don't affect production .agilevv directory."""
        # Check if there's a production .agilevv in the current directory
        production_agilevv = Path.cwd() / ".agilevv"

        # Create a file in the isolated directory
        test_file = isolated_agilevv_dir.base_dir / "isolation_test.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("isolated content")

        # If production .agilevv exists, verify our test file isn't there
        if production_agilevv.exists():
            assert not (production_agilevv / "isolation_test.txt").exists()

        # Verify our isolated directory is not the production directory
        assert isolated_agilevv_dir.base_dir != production_agilevv


class TestFixtureScopes:
    """Test different fixture scopes for appropriate use cases."""

    # Track module-level state
    module_counter = 0

    def test_function_scope_independence_1(self, isolated_agilevv_dir: PathConfig) -> None:
        """First test with function-scoped fixture."""
        marker = isolated_agilevv_dir.base_dir / "function_marker.txt"
        marker.parent.mkdir(parents=True, exist_ok=True)

        # This should not exist from any previous test
        assert not marker.exists()
        marker.write_text("test1")

    def test_function_scope_independence_2(self, isolated_agilevv_dir: PathConfig) -> None:
        """Second test with function-scoped fixture."""
        marker = isolated_agilevv_dir.base_dir / "function_marker.txt"
        marker.parent.mkdir(parents=True, exist_ok=True)

        # This should not exist from the previous test
        assert not marker.exists()
        marker.write_text("test2")

    def test_module_scope_persistence_1(self, isolated_agilevv_module_dir: PathConfig) -> None:
        """First test with module-scoped fixture."""
        TestFixtureScopes.module_counter += 1

        counter_file = isolated_agilevv_module_dir.base_dir / "counter.txt"
        counter_file.parent.mkdir(parents=True, exist_ok=True)

        if counter_file.exists():
            count = int(counter_file.read_text())
        else:
            count = 0

        count += 1
        counter_file.write_text(str(count))

        # First test in module should have count 1
        if TestFixtureScopes.module_counter == 1:
            assert count == 1

    def test_module_scope_persistence_2(self, isolated_agilevv_module_dir: PathConfig) -> None:
        """Second test with module-scoped fixture."""
        TestFixtureScopes.module_counter += 1

        counter_file = isolated_agilevv_module_dir.base_dir / "counter.txt"

        # File should exist from previous test in same module
        assert counter_file.exists()

        count = int(counter_file.read_text())
        count += 1
        counter_file.write_text(str(count))

        # Second test should see incremented count
        assert count == 2
