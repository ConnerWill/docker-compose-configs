from prometheus_client import CollectorRegistry, multiprocess


def when_ready(server):
    # Required for Django prometheus metrics
    multiprocess.MultiProcessCollector(CollectorRegistry())


def child_exit(server, worker):
    # Required for Django prometheus metrics
    multiprocess.mark_process_dead(worker.pid)
