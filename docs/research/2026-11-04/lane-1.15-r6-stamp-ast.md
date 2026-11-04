# Lane 1.15-r6-stamp-ast: stage stamps hash code, not comments

- Cause: stamps hashed the bytes of every covered .py, so a comment edit (fcfbff08) moved the ground stamp and killed r6-chain20.
- Fix: `pipeline._code_bytes` hashes `ast.dump` of the module with module/class/function docstrings stripped; unparsable files and non-.py files keep bytes. Used by `_files_key` (so `_cover_key`), the ground, terrain, water and vegetation hand lists, and the generator source walk.
- Test: `test_code_bytes_ignores_comments_and_docstrings_not_code` (comment, docstring, formatting leave it; a constant moves it).
- One-off: the key's value changes once from the new hashing (ground 88c55c71... to edaa9830...); the planner regenerates once.
- Cost: `_ground_stamp()` 0.69 s.
