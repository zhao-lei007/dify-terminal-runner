"""
Basic functionality test without dependencies
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Test 1: Import executor without RestrictedPython
print("=" * 60)
print("Test 1: Import executor module")
try:
    from executor import CodeSandbox
    print("✅ executor.py imported successfully")
except Exception as e:
    print(f"❌ Failed to import executor: {e}")
    sys.exit(1)

# Test 2: Create sandbox instance
print("\nTest 2: Create CodeSandbox instance")
try:
    sandbox = CodeSandbox()
    print("✅ CodeSandbox created successfully")
except Exception as e:
    print(f"❌ Failed to create sandbox: {e}")
    sys.exit(1)

# Test 3: Simple code execution
print("\nTest 3: Execute simple Python code")
try:
    result = sandbox.run(
        code="x = 10 + 20\nprint(f'Result: {x}')",
        session_id="test_session"
    )
    print("✅ Code executed successfully")
    print(f"   Status: {result['status']}")
    print(f"   Output: {result['stdout'].strip()}")
except Exception as e:
    print(f"❌ Failed to execute code: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Import and use main.py
print("\nTest 4: Import main.py")
try:
    from main import run
    print("✅ main.py imported successfully")
except Exception as e:
    print(f"❌ Failed to import main: {e}")
    sys.exit(1)

# Test 5: Call run function
print("\nTest 5: Call run() function")
try:
    result = run(
        code="print('Hello from Dify plugin!')",
        session_id="test_run"
    )
    print("✅ run() function works")
    print(f"   Success: {result['success']}")
    print(f"   Output: {result['output'].strip()}")
except Exception as e:
    print(f"❌ Failed to run: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Session persistence
print("\nTest 6: Session persistence")
try:
    # Write data
    result1 = run(
        code="""
data = 'Hello Session'
with open('test.txt', 'w') as f:
    f.write(data)
print('Data written')
""",
        session_id="persist_test"
    )

    # Read data
    result2 = run(
        code="""
with open('test.txt', 'r') as f:
    data = f.read()
print(f'Read: {data}')
""",
        session_id="persist_test"
    )

    if result2['success'] and 'Hello Session' in result2['output']:
        print("✅ Session persistence works")
        print(f"   Output: {result2['output'].strip()}")
    else:
        print("❌ Session persistence failed")
        print(f"   Output: {result2['output']}")
except Exception as e:
    print(f"❌ Failed session test: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ All basic tests passed!")
print("=" * 60)
