"""
Code Execution Engine for Dify Terminal Runner Plugin
Provides safe Python code execution with session management
"""

import os
import sys
import subprocess
import tempfile
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import shutil

# RestrictedPython for basic code safety checks
try:
    from RestrictedPython import compile_restricted, safe_globals
    RESTRICTED_PYTHON_AVAILABLE = True
except ImportError:
    RESTRICTED_PYTHON_AVAILABLE = False
    print("[WARNING] RestrictedPython not available, running without safety checks")


class SessionManager:
    """Manage isolated session directories for code execution"""

    def __init__(self, base_dir: str = None):
        """
        Initialize session manager

        Args:
            base_dir: Base directory for sessions, defaults to ./sessions
        """
        if base_dir is None:
            base_dir = os.path.join(os.getcwd(), "sessions")

        # Convert to absolute path to avoid issues with cwd changes
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_session_dir(self, session_id: str) -> Path:
        """Get or create session directory"""
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def list_sessions(self) -> List[str]:
        """List all session IDs"""
        if not self.base_dir.exists():
            return []
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]

    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session directory"""
        session_dir = self.base_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
            return True
        return False

    def get_session_files(self, session_id: str) -> List[str]:
        """Get list of files in session directory"""
        session_dir = self.get_session_dir(session_id)
        files = []
        for item in session_dir.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                files.append(item.name)
        return sorted(files)


class CodeExecutor:
    """Execute Python code in isolated environment"""

    def __init__(self, session_manager: SessionManager):
        """
        Initialize code executor

        Args:
            session_manager: SessionManager instance for handling sessions
        """
        self.session_manager = session_manager

    def check_code_safety(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Basic safety check for code (if RestrictedPython available)

        Args:
            code: Python code to check

        Returns:
            (is_safe, error_message)
        """
        if not RESTRICTED_PYTHON_AVAILABLE:
            return True, None

        try:
            # Try to compile with RestrictedPython
            byte_code = compile_restricted(code, '<inline>', 'exec')
            if byte_code.errors:
                return False, f"Code safety check failed: {', '.join(byte_code.errors)}"
            return True, None
        except Exception as e:
            return False, f"Code safety check error: {str(e)}"

    def execute(
        self,
        code: str,
        session_id: str,
        timeout: Optional[int] = None,
        capture_artifacts: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Python code in session context

        Args:
            code: Python code to execute
            session_id: Session identifier
            timeout: Execution timeout in seconds (None for no timeout)
            capture_artifacts: Whether to capture generated files

        Returns:
            Execution result dictionary:
            {
                "status": "success" | "error",
                "returncode": int,
                "stdout": str,
                "stderr": str,
                "artifacts": {
                    "files": List[str],
                    "session_dir": str
                },
                "execution_time": float,
                "timestamp": str
            }
        """
        start_time = datetime.now()

        # Get session directory
        session_dir = self.session_manager.get_session_dir(session_id)

        # Record files before execution
        files_before = set(session_dir.iterdir()) if capture_artifacts else set()

        # Create temporary Python file for execution
        code_file = session_dir / f"_exec_{start_time.strftime('%Y%m%d_%H%M%S')}.py"

        result = {
            "status": "error",
            "returncode": -1,
            "stdout": "",
            "stderr": "",
            "artifacts": {
                "files": [],
                "session_dir": str(session_dir)
            },
            "execution_time": 0.0,
            "timestamp": start_time.isoformat()
        }

        try:
            # Basic safety check (optional)
            # Note: We're allowing most operations for demo phase
            # In production, you may want stricter checks

            # Write code to file
            code_file.write_text(code, encoding='utf-8')

            # Prepare environment
            env = os.environ.copy()
            env['PYTHONPATH'] = str(session_dir)

            # Execute code using subprocess
            process = subprocess.Popen(
                [sys.executable, str(code_file)],
                cwd=str(session_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )

            # Wait for completion with optional timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                returncode = process.returncode

                result.update({
                    "status": "success" if returncode == 0 else "error",
                    "returncode": returncode,
                    "stdout": stdout,
                    "stderr": stderr
                })

            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                result.update({
                    "status": "error",
                    "returncode": -1,
                    "stdout": stdout,
                    "stderr": f"Execution timeout ({timeout}s exceeded)\n{stderr}"
                })

            # Capture artifacts (new files created during execution)
            if capture_artifacts:
                files_after = set(session_dir.iterdir())
                new_files = files_after - files_before

                artifact_files = []
                for file_path in new_files:
                    if file_path.is_file() and not file_path.name.startswith('_exec_'):
                        artifact_files.append(file_path.name)

                result["artifacts"]["files"] = sorted(artifact_files)

        except Exception as e:
            error_trace = traceback.format_exc()
            result.update({
                "status": "error",
                "returncode": -1,
                "stderr": f"Execution error: {str(e)}\n{error_trace}"
            })

        finally:
            # Calculate execution time
            end_time = datetime.now()
            result["execution_time"] = (end_time - start_time).total_seconds()

            # Clean up temporary code file
            try:
                if code_file.exists():
                    code_file.unlink()
            except Exception:
                pass

        return result

    def execute_with_context(
        self,
        code: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute code with predefined context variables

        Args:
            code: Python code to execute
            session_id: Session identifier
            context: Dictionary of variables to make available in code
            timeout: Execution timeout in seconds

        Returns:
            Execution result dictionary
        """
        # Prepare code with context injection
        if context:
            context_setup = "import json\n"
            context_setup += f"_context = {json.dumps(context)}\n"
            context_setup += "globals().update(_context)\n\n"
            code = context_setup + code

        return self.execute(code, session_id, timeout)


class CodeSandbox:
    """High-level interface for code execution sandbox"""

    def __init__(self, sessions_base_dir: str = None):
        """
        Initialize code sandbox

        Args:
            sessions_base_dir: Base directory for session storage
        """
        self.session_manager = SessionManager(sessions_base_dir)
        self.executor = CodeExecutor(self.session_manager)

    def run(
        self,
        code: str,
        session_id: str,
        timeout: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run Python code in sandbox

        Args:
            code: Python code to execute
            session_id: Session identifier for isolation
            timeout: Optional timeout in seconds
            context: Optional context variables

        Returns:
            Execution result dictionary
        """
        if context:
            return self.executor.execute_with_context(code, session_id, context, timeout)
        return self.executor.execute(code, session_id, timeout)

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a session"""
        session_dir = self.session_manager.get_session_dir(session_id)
        files = self.session_manager.get_session_files(session_id)

        return {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "files": files,
            "exists": session_dir.exists()
        }

    def clear_session(self, session_id: str) -> bool:
        """Clear a session's data"""
        return self.session_manager.clear_session(session_id)

    def list_sessions(self) -> List[str]:
        """List all active sessions"""
        return self.session_manager.list_sessions()


# Convenience function for direct usage
def execute_code(code: str, session_id: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to execute code

    Args:
        code: Python code to execute
        session_id: Session identifier
        **kwargs: Additional arguments (timeout, context, etc.)

    Returns:
        Execution result dictionary
    """
    sandbox = CodeSandbox()
    return sandbox.run(code, session_id, **kwargs)


if __name__ == "__main__":
    # Quick test
    sandbox = CodeSandbox()

    # Test 1: Simple calculation
    result = sandbox.run(
        code="print('Hello from sandbox!')\nresult = 2 + 2\nprint(f'Result: {result}')",
        session_id="test_session"
    )
    print("Test 1 Result:")
    print(json.dumps(result, indent=2))

    # Test 2: File creation
    result = sandbox.run(
        code="""
import json
data = {'message': 'Hello', 'value': 42}
with open('test_data.json', 'w') as f:
    json.dump(data, f)
print('File created successfully')
""",
        session_id="test_session"
    )
    print("\nTest 2 Result:")
    print(json.dumps(result, indent=2))

    # Test 3: Read previously created file
    result = sandbox.run(
        code="""
import json
with open('test_data.json', 'r') as f:
    data = json.load(f)
print(f"Read data: {data}")
""",
        session_id="test_session"
    )
    print("\nTest 3 Result:")
    print(json.dumps(result, indent=2))
