Think because this task is complex.
Analyse the pre-commit configuration.
Run ALL precommit hooks individually on the codebase WITHOUT fast fail mode and analyse the errors.
For each hook (one to the other and also inside each hook), breakdown all type of errors encountered. (e.g., syntax errors, linting errors, etc.)
Then, in a SINGLE MESSAGE, spawn parrallel lint-type-fixer subagents to fix each type of error.