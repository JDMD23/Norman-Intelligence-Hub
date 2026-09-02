"""Run the full Lease Comps v4 migration, gated: structure -> verify -> style -> finalize.
Each stage prints its own receipts; the pipeline stops on the first failure."""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
for step in ['migrate_structure.py', 'verify_wire.py', 'style.py', 'finalize.py']:
    print(f'\n=== {step} ===')
    r = subprocess.run([sys.executable, os.path.join(HERE, step)], cwd=HERE)
    if r.returncode != 0:
        print(f'STOPPED at {step} (exit {r.returncode})')
        sys.exit(r.returncode)
print('\nMIGRATION COMPLETE')
