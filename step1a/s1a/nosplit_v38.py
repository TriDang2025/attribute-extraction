"""wf_v3.8 task 2: read the A runs without the split pass. A cluster that the split pass would have split keeps its A
decision (name, merge). Two readers of the split responses are switched off while the loaders run:
- pilot_verify.load_split_results (the v3.1 split responses of dev50 v2.2: v34_data.load_all, v36_data.load_v36);
- run_data_v37.batch_jobs (family "split" rows of the v3.7 batch: run_data_v37.load_a).
Nothing is edited on disk; the patch lasts one `with no_split():` block.
"""

from contextlib import contextmanager
from unittest import mock

from . import pilot_verify as PV
from . import run_data_v37 as RD


def drop_split_jobs(batch_jobs):
    """Wrap run_data_v37.batch_jobs: (A jobs, []) instead of (A jobs, split jobs)."""
    def wrapped(*args, **kw):
        a, _ = batch_jobs(*args, **kw)
        return a, []
    return wrapped


@contextmanager
def no_split():
    with mock.patch.object(PV, "load_split_results", lambda *a, **k: {}), \
            mock.patch.object(RD, "batch_jobs", drop_split_jobs(RD.batch_jobs)):
        yield
