# Changelog

## v3.0.1
- Updated maingui so that interface does not break on high dpi display

## v3.0.0
- Stopped using Tkinter and switched to PyQt.
- Download path cannot contain spaces – bug solved.
- UI update.
- Some minor UI bugs solved.
- Can check for app updates.
- Anonymously logs user country and app open time for analyzing total app users.
- Can show notifications from remote server.
- Organized the repo, deleted the old code.
- Fixed Chinese subtitle code to `zh-CN`.
- using rookiepy instead of browsercookie3 for cookie fetching. can now fetch cookie from edge, firefox, brave.


## v2.1.0
- Solved the bug of permission error for Chrome and Edge.
- Authentication is now only possible from Firefox and Chrome.
- Added menu.
- Added error handling in `maingui.py` and `general.py`.
- Solved logical error in `urltoclassname` function.
- Also some minor changes.

**Unsolved problems:**
- Space in download path is still a problem.
- Add permission error handling for `data.bin` reading and writing.

## v2.0.0
- Uses the fork by [raffaem](https://github.com/raffaem/cs-dlp).

## v1.0.0
- Uses the `coursera-dl` script.
