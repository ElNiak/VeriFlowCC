"""Git integration for VeriFlowCC checkpointing."""

import subprocess
from datetime import datetime
from pathlib import Path


class GitIntegration:
    """Handles git operations for checkpointing and state management."""

    def __init__(self, repo_path: Path | None = None):
        """Initialize git integration.

        Args:
            repo_path: Path to git repository
        """
        self.repo_path = repo_path or Path.cwd()

    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository.

        Returns:
            True if git repository exists
        """
        git_dir = self.repo_path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def get_current_branch(self) -> str:
        """Get current git branch name.

        Returns:
            Current branch name
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "main"

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes.

        Returns:
            True if uncommitted changes exist
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def create_checkpoint_commit(self, checkpoint_name: str, message: str) -> tuple[bool, str]:
        """Create a git commit for checkpoint.

        Args:
            checkpoint_name: Name of the checkpoint
            message: Commit message

        Returns:
            Tuple of (success, commit_hash or error_message)
        """
        if not self.is_git_repo():
            return False, "Not a git repository"

        try:
            # Stage .agilevv directory
            subprocess.run(
                ["git", "add", ".agilevv/"], cwd=self.repo_path, check=True, capture_output=True
            )

            # Create commit
            commit_message = f"checkpoint: {checkpoint_name}\n\n{message}"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            return True, hash_result.stdout.strip()[:8]

        except subprocess.CalledProcessError as e:
            return False, str(e)

    def create_checkpoint_tag(
        self, checkpoint_name: str, commit_hash: str = "HEAD"
    ) -> tuple[bool, str]:
        """Create a git tag for checkpoint.

        Args:
            checkpoint_name: Name for the tag
            commit_hash: Commit to tag (default HEAD)

        Returns:
            Tuple of (success, tag_name or error_message)
        """
        if not self.is_git_repo():
            return False, "Not a git repository"

        tag_name = f"checkpoint/{checkpoint_name}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag_message = f"Checkpoint created at {timestamp}"

        try:
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", tag_message, commit_hash],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            return True, tag_name

        except subprocess.CalledProcessError as e:
            return False, str(e)

    def list_checkpoint_tags(self) -> list[dict[str, str]]:
        """List all checkpoint tags.

        Returns:
            List of checkpoint tag information
        """
        if not self.is_git_repo():
            return []

        try:
            result = subprocess.run(
                [
                    "git",
                    "tag",
                    "-l",
                    "checkpoint/*",
                    "--format=%(refname:short)|%(subject)|%(creatordate:short)",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            checkpoints = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        tag_name = parts[0].replace("checkpoint/", "")
                        message = parts[1] if len(parts) > 1 else ""
                        date = parts[2] if len(parts) > 2 else ""
                        checkpoints.append({"name": tag_name, "message": message, "date": date})

            return checkpoints

        except subprocess.CalledProcessError:
            return []

    def restore_checkpoint(self, checkpoint_name: str, force: bool = False) -> tuple[bool, str]:
        """Restore to a checkpoint using git.

        Args:
            checkpoint_name: Name of checkpoint to restore
            force: Force restore even with uncommitted changes

        Returns:
            Tuple of (success, message)
        """
        if not self.is_git_repo():
            return False, "Not a git repository"

        if not force and self.has_uncommitted_changes():
            return (
                False,
                "Uncommitted changes exist. Use --force to override or commit changes first.",
            )

        tag_name = f"checkpoint/{checkpoint_name}"

        try:
            # Check if tag exists
            subprocess.run(
                ["git", "rev-parse", tag_name], cwd=self.repo_path, check=True, capture_output=True
            )

            # Checkout the tag
            subprocess.run(
                ["git", "checkout", tag_name, "--", ".agilevv/"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            return True, f"Restored to checkpoint: {checkpoint_name}"

        except subprocess.CalledProcessError as e:
            return False, f"Failed to restore checkpoint: {e!s}"

    def get_checkpoint_diff(self, checkpoint_name: str) -> str | None:
        """Get diff between current state and checkpoint.

        Args:
            checkpoint_name: Name of checkpoint

        Returns:
            Diff output or None if error
        """
        if not self.is_git_repo():
            return None

        tag_name = f"checkpoint/{checkpoint_name}"

        try:
            result = subprocess.run(
                ["git", "diff", tag_name, "HEAD", "--", ".agilevv/"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout

        except subprocess.CalledProcessError:
            return None

    def auto_checkpoint_on_stage_complete(self, stage_name: str) -> tuple[bool, str]:
        """Automatically create checkpoint when stage completes.

        Args:
            stage_name: Name of completed stage

        Returns:
            Tuple of (success, checkpoint_name or error)
        """
        checkpoint_name = f"{stage_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        message = f"Auto-checkpoint after {stage_name} stage completion"

        success, commit_result = self.create_checkpoint_commit(checkpoint_name, message)
        if success:
            tag_success, tag_result = self.create_checkpoint_tag(checkpoint_name)
            if tag_success:
                return True, checkpoint_name
            return False, tag_result
        return False, commit_result
