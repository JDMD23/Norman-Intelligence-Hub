"""Run the full Lease Comps v4 migration, gated: structure -> verify -> style -> finalize -> sync.
Each stage prints its own receipts; the pipeline stops on the first failure. Every stage is
re-runnable (no-ops when its work is already in place), so a failed run can simply be re-run."""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
for step in ['migrate_structure.py', 'verify_wire.py', 'style.py', 'polish.py', 'finalize.py',
             'sync_schema.py']:
    print(f'\n=== {step} ===')
    r = subprocess.run([sys.executable, os.path.join(HERE, step)], cwd=HERE)
    if r.returncode != 0:
        print(f'STOPPED at {step} (exit {r.returncode})')
        sys.exit(r.returncode)
print('\nMIGRATION COMPLETE')
