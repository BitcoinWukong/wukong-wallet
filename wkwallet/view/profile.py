import cProfile
import io
import pstats
from pstats import SortKey

from kivy.logger import Logger


def start_profiling():
    _profiler.enable()


def complete_profiling():
    _profiler.disable()

    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(_profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    Logger.debug("WKWallet: " + s.getvalue())


_profiler = cProfile.Profile()
