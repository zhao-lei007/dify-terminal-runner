"""
Dify Terminal Runner Plugin - Main Entry Point
Executes Python code in isolated sandbox environment

Author: DaddyTech
Version: 0.2.0
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Import our code execution engine
from executor import CodeSandbox

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TerminalRunner:
    """Main plugin class for terminal code execution"""

    def __init__(self, sessions_dir: Optional[str] = None):
        """
        Initialize Terminal Runner

        Args:
            sessions_dir: Custom sessions directory path
        """
        if sessions_dir is None:
            sessions_dir = os.environ.get('SESSIONS_DIR', './sessions')

        self.sandbox = CodeSandbox(sessions_base_dir=sessions_dir)
        logger.info(f"Terminal Runner initialized with sessions directory: {sessions_dir}")

    def validate_inputs(self, code: Any, session_id: Any) -> tuple[bool, Optional[str]]:
        """
        Validate input parameters

        Args:
            code: Code input to validate
            session_id: Session ID to validate

        Returns:
            (is_valid, error_message)
        """
        # Validate code parameter
        if code is None:
            return False, "Code parameter is required"

        if not isinstance(code, str):
            # Try to convert to string
            try:
                code = str(code)
            except Exception as e:
                return False, f"Code must be a string, got {type(code).__name__}: {str(e)}"

        if not code.strip():
            return False, "Code cannot be empty"

        # Validate session_id parameter
        if session_id is None:
            return False, "Session ID parameter is required"

        if not isinstance(session_id, str):
            # Try to convert to string
            try:
                session_id = str(session_id)
            except Exception as e:
                return False, f"Session ID must be a string, got {type(session_id).__name__}: {str(e)}"

        if not session_id.strip():
            return False, "Session ID cannot be empty"

        # Check for potentially dangerous characters in session_id
        # (prevent directory traversal)
        if '..' in session_id or '/' in session_id or '\\' in session_id:
            return False, "Session ID contains invalid characters"

        return True, None

    def format_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format execution result for Dify workflow compatibility

        Args:
            result: Raw execution result from sandbox

        Returns:
            Formatted result for Dify
        """
        # Extract key information
        status = result.get('status', 'error')
        returncode = result.get('returncode', -1)
        stdout = result.get('stdout', '')
        stderr = result.get('stderr', '')
        artifacts = result.get('artifacts', {})
        execution_time = result.get('execution_time', 0.0)
        timestamp = result.get('timestamp', datetime.now().isoformat())

        # Format output for better Dify workflow integration
        formatted = {
            # Primary status indicators
            "success": status == "success" and returncode == 0,
            "status": status,
            "returncode": returncode,

            # Output content
            "output": stdout,  # Main output field for workflow
            "stdout": stdout,  # Detailed stdout
            "stderr": stderr,  # Error messages

            # Metadata
            "execution_time": execution_time,
            "timestamp": timestamp,

            # Artifacts and session info
            "artifacts": artifacts,
            "has_artifacts": len(artifacts.get('files', [])) > 0,
            "artifact_files": artifacts.get('files', []),
            "session_dir": artifacts.get('session_dir', ''),

            # Convenience fields for workflow conditionals
            "has_output": bool(stdout.strip()),
            "has_error": bool(stderr.strip()) or returncode != 0,
            "error_message": stderr if stderr else None,
        }

        return formatted

    def run(self, code: Any, session_id: Any, **kwargs) -> Dict[str, Any]:
        """
        Main execution entry point for Dify plugin

        This function is called by Dify workflow engine

        Args:
            code: Python code to execute
            session_id: Session identifier for isolation
            **kwargs: Additional parameters (timeout, context, etc.)

        Returns:
            Execution result dictionary compatible with Dify
        """
        logger.info(f"Starting code execution for session: {session_id}")

        try:
            # Validate inputs
            is_valid, error_msg = self.validate_inputs(code, session_id)
            if not is_valid:
                logger.error(f"Input validation failed: {error_msg}")
                return {
                    "success": False,
                    "status": "error",
                    "returncode": -1,
                    "output": "",
                    "stdout": "",
                    "stderr": error_msg,
                    "error_message": error_msg,
                    "has_error": True,
                    "has_output": False,
                    "has_artifacts": False,
                    "artifact_files": [],
                    "artifacts": {},
                    "execution_time": 0.0,
                    "timestamp": datetime.now().isoformat()
                }

            # Convert to strings if needed
            code = str(code).strip()
            session_id = str(session_id).strip()

            # Extract optional parameters
            timeout = kwargs.get('timeout', None)
            context = kwargs.get('context', None)

            logger.info(f"Executing code (length: {len(code)} chars)")
            logger.debug(f"Code preview: {code[:100]}...")

            # Execute code in sandbox
            result = self.sandbox.run(
                code=code,
                session_id=session_id,
                timeout=timeout,
                context=context
            )

            # Format output for Dify
            formatted_result = self.format_output(result)

            # Log execution result
            if formatted_result['success']:
                logger.info(f"Code execution completed successfully in {formatted_result['execution_time']:.2f}s")
            else:
                logger.warning(f"Code execution failed with returncode {formatted_result['returncode']}")
                if formatted_result['error_message']:
                    logger.error(f"Error: {formatted_result['error_message'][:200]}")

            return formatted_result

        except Exception as e:
            logger.error(f"Unexpected error during execution: {str(e)}", exc_info=True)
            return {
                "success": False,
                "status": "error",
                "returncode": -1,
                "output": "",
                "stdout": "",
                "stderr": f"Plugin error: {str(e)}",
                "error_message": f"Plugin error: {str(e)}",
                "has_error": True,
                "has_output": False,
                "has_artifacts": False,
                "artifact_files": [],
                "artifacts": {},
                "execution_time": 0.0,
                "timestamp": datetime.now().isoformat()
            }

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a session

        Args:
            session_id: Session identifier

        Returns:
            Session information
        """
        return self.sandbox.get_session_info(session_id)

    def clear_session(self, session_id: str) -> bool:
        """
        Clear a session's data

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        return self.sandbox.clear_session(session_id)

    def list_sessions(self) -> list:
        """
        List all active sessions

        Returns:
            List of session IDs
        """
        return self.sandbox.list_sessions()


# Global plugin instance
_plugin_instance = None


def get_plugin_instance() -> TerminalRunner:
    """Get or create global plugin instance"""
    global _plugin_instance
    if _plugin_instance is None:
        _plugin_instance = TerminalRunner()
    return _plugin_instance


# Main entry point for Dify (as specified in manifest.json)
def run(code: Any, session_id: Any, **kwargs) -> Dict[str, Any]:
    """
    Main entry point called by Dify workflow engine

    Args:
        code: Python code to execute
        session_id: Session identifier
        **kwargs: Additional parameters

    Returns:
        Execution result dictionary
    """
    plugin = get_plugin_instance()
    return plugin.run(code, session_id, **kwargs)


# Additional utility functions that can be called by Dify

def get_session_info(session_id: str) -> Dict[str, Any]:
    """Get session information (can be exposed as separate tool)"""
    plugin = get_plugin_instance()
    return plugin.get_session_info(session_id)


def clear_session(session_id: str) -> Dict[str, Any]:
    """Clear session data (can be exposed as separate tool)"""
    plugin = get_plugin_instance()
    success = plugin.clear_session(session_id)
    return {
        "success": success,
        "message": f"Session '{session_id}' cleared successfully" if success else f"Session '{session_id}' not found"
    }


def list_sessions() -> Dict[str, Any]:
    """List all sessions (can be exposed as separate tool)"""
    plugin = get_plugin_instance()
    sessions = plugin.list_sessions()
    return {
        "success": True,
        "sessions": sessions,
        "count": len(sessions)
    }


# CLI interface for testing
if __name__ == "__main__":
    print("=" * 60)
    print("Dify Terminal Runner Plugin - Test Mode")
    print("=" * 60)

    # Test 1: Simple code execution
    print("\n[Test 1] Simple Calculation:")
    result = run(
        code="result = 10 + 20\nprint(f'The answer is: {result}')",
        session_id="test_session_1"
    )
    print(json.dumps(result, indent=2))

    # Test 2: Data science example
    print("\n[Test 2] Data Science with Pandas:")
    result = run(
        code="""
import pandas as pd
import numpy as np

# Create sample data
data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'score': [85, 90, 95]
}

df = pd.DataFrame(data)
print("DataFrame created:")
print(df)
print(f"\\nMean score: {df['score'].mean()}")
""",
        session_id="test_session_2"
    )
    print(json.dumps(result, indent=2))

    # Test 3: File persistence across sessions
    print("\n[Test 3] File Persistence - Write:")
    result = run(
        code="""
import json

data = {
    'counter': 1,
    'message': 'Hello from session!'
}

with open('persistent_data.json', 'w') as f:
    json.dump(data, f, indent=2)

print('Data saved to persistent_data.json')
""",
        session_id="test_session_3"
    )
    print(json.dumps(result, indent=2))

    print("\n[Test 3] File Persistence - Read:")
    result = run(
        code="""
import json

with open('persistent_data.json', 'r') as f:
    data = json.load(f)

print(f"Read data: {data}")
data['counter'] += 1
print(f"Updated counter to: {data['counter']}")
""",
        session_id="test_session_3"  # Same session ID
    )
    print(json.dumps(result, indent=2))

    # Test 4: Error handling
    print("\n[Test 4] Error Handling:")
    result = run(
        code="x = 1 / 0  # This will cause an error",
        session_id="test_session_4"
    )
    print(json.dumps(result, indent=2))

    # Test 5: Invalid input handling
    print("\n[Test 5] Invalid Input:")
    result = run(
        code="",  # Empty code
        session_id="test_session_5"
    )
    print(json.dumps(result, indent=2))

    # Test 6: List sessions
    print("\n[Test 6] List All Sessions:")
    sessions = list_sessions()
    print(json.dumps(sessions, indent=2))

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
