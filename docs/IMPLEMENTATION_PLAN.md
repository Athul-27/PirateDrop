Implementation Plan -- PirateDrop
==============================

1. Vision
---------
A lightweight desktop application that wraps the croc CLI with a polished black-and-white Neo-Brutalist graphical interface. The user should never need to open a terminal, understand networking, configure ports, or manually execute croc commands.

2. Technology Stack
-------------------
- Python 3.12
- PySide6 6.12.0 (Qt for Python)
- croc CLI v11.5.4 (Windows executable, bundled with app)
- PyInstaller for Windows packaging
- pytest for testing
- subprocess.Popen + daemon reader thread for asynchronous process management

4. Screens
---------
- Send: file picker, folder picker, drag-and-drop, selection list, SEND button, share code display + copy, waiting/receiving status, progress, cancellation
- Receive: share code input, paste clipboard, folder picker, RECEIVE button, status, progress, cancellation, open folder after success
- Settings: croc executable path, version, repo link, diagnostics

5. State Model
--------------
Idle -> Preparing -> WaitingForReceiver -> Connecting -> Transferring -> Completed -> Failed -> Cancelling -> Cancelled
Only states supported by actual CLI output or confirmed process events.

6. Process Management
---------------------
- subprocess.Popen + daemon reader thread for all croc subprocess management
- Merged stdout/stderr stream (stderr=STDOUT), parsed line-by-line
- Continuous streaming, pipe deadlock prevention
- Terminal control sequences stripped before parsing
- Detect process-start errors, unexpected termination
- Graceful cancellation + bounded forced termination
- No orphaned processes; cleanup on shutdown
- Send and Receive screens each hold an independent service instance; a send and a receive may run concurrently

7. Visual Design -- Neo-Brutalism
---------------------------------
Color palette (only):
  - #000000 pure black
  - #FFFFFF pure white
No gradients, no shadows, no glow, no blur, no translucency.

Geometry:
  - Solid 2-3px black borders
  - Flat rectangular surfaces
  - Corner radii 2-6px
  - Strong alignment, consistent spacing
  - Thin solid divider lines
  - Generous whitespace

Typography:
  - Clean sans-serif for headings/body
  - Monospace for share codes/technical details
  - Bold high-contrast headings
  - Strong hierarchy, legible at Windows scaling

Window structure:
  - Compact top bar with PIRATEDROP wordmark + descriptor (SIMPLE / SECURE / FILE SHARING)
  - Left navigation rail: SEND / RECEIVE / SETTINGS
  - Spacious main content region
  - Bordered panels, section headings
  - Distinct share-code panel
  - Dedicated transfer-status section

Reusable components:
  - Primary buttons, secondary buttons
  - Navigation items, bordered panels
  - Section headings, file-list entries
  - Share-code display, status indicators
  - Progress displays, empty states, error states
  - Hover, pressed, focused, active, disabled states
  - Keyboard navigation, focus indicators

8. Packaging
------------
- PyInstaller bundling:
  - Python runtime, PySide6 libraries
  - croc.exe executable (bundled)
  - Correct packaged-application resource paths
  - Windows-specific process management
- Reproducible build command documented
- Application icon if practical
- Verify startup/shutdown, resource resolution

9. Security & Reliability
-------------------------
- Preserve croc encryption/authentication
- Never implement custom encryption
- Share codes and links are stored in the local transfer history by design (capped at 200 entries in %APPDATA%\PirateDrop\history.json)
- Do not expose secrets in logs
- Do not silently overwrite files
- Validate paths and executable locations
- Understandable error messages without sensitive details

10. Testing Requirements
------------------------
Unit tests (mocked processes):
  1. Share-code extraction
  2. ANSI escape-sequence removal
  3. Paths containing spaces
  4. Unicode filenames
  5. Process argument construction
  6. stdout/stderr handling
  7. Process-start failures
  8. Unexpected process exits
  9. Cancellation and cleanup
  10. Destination file conflicts
  11. Progress parsing
  12. State transitions
  13. Missing share codes
  14. Empty file selections
  15. Invalid destination paths
  16. Diagnostic-log redaction

Integration tests (where feasible):
  - Real local transfer using separate croc processes

Do not claim real transfers were tested if they were not.

11. Dependencies
----------------
- PySide6>=6.12
- PyInstaller (for build)
- pytest

12. Known Limitations
---------------------
- Network-dependent (requires relay or direct connection)
- crc --no-local flag may be needed for restrictive networks
- Progress parsing version-dependent
- No custom relays or custom networking
- Windows-only
13. Build & Run Commands
------------------------
- Install dependencies: pip install -r requirements.txt
- Run development: python app.py
- Build packaged app: .\build.ps1 (PyInstaller via app.spec)
- Run bundled app: dist\PirateDrop.exe
- Run tests: python -m pytest
- Run integration tests (network required): python -m pytest --run-integration