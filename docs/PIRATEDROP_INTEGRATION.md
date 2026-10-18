croc Integration -- PirateDrop
============================

1. CLI Behavior Verification
-----------------------------
Version: 11.5.4
Executable: croc.exe
Download: https://github.com/schollz/croc/releases

2. Send Command Syntax
----------------------
croc send [file(s) or folder]
Options: --code, --zip, --transport, --port, --transfers
Output: share code on completion

3. Receive Command Syntax
-------------------------
croc --yes --out [destination] [code]
Validation: missing code detected before process start

4. Progress Output Format
-------------------------
Lines read from stdout/stderr
ANSI escape sequences stripped before parsing
No fabricated percentages or ETA

5. Process Management
---------------------
- subprocess.Popen + daemon reader thread for async management
- Merged stdout/stderr stream (stderr=STDOUT), parsed line-by-line
- Continuous streaming
- Pipe deadlock prevention
- Start error detection
- Unexpected termination handling
- Graceful cancellation
- No orphaned processes

6. Conflict Handling
--------------------
croc prompts for conflict resolution
PirateDrop passes --yes, so conflicts are auto-accepted (overwrite)

7. Environment Variables
------------------------
No custom environment variables required
- May use --port, --transfers for customization

8. Cancellation Behavior
------------------------
SIGTERM/SIGINT to process
Bounded forced termination if needed

9. Security Notes
------------------
- Preserve croc encryption/authentication
- Do not implement custom encryption
- Do not expose secrets in logs
- Validate all paths and executable locations

