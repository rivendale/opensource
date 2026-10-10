#!/usr/bin/env python3
"""Shows that every game-sfx checker can fail (see evals/studio/lib/selfcheck_core.py).

    python3 evals/studio/game-sfx/build/selfcheck.py [CASE_ID_PREFIX]
"""
import pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "lib"))
import make_cases as M
import selfcheck_core

if __name__ == "__main__":
    sys.exit(selfcheck_core.main(M, sys.argv[1:]))
