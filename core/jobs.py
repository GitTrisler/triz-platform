import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Any

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Slot

from core.logger import log


@dataclass
class JobResult:
    name: str
    status: str
    started: datetime
    finished: datetime | None = None
    result: Any = None
    error: str | None = None


@dataclass
class Job:
    name: str
    function: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    started: datetime | None = None
    finished: datetime | None = None
    status: str = "Queued"
    result: Any = None
    error: str | None = None


class JobSignals(QObject):
    started = Signal(str)
    message = Signal(str, str)
    finished = Signal(object)
    failed = Signal(object)


class JobWorker(QRunnable):
    def __init__(self, job: Job):
        super().__init__()
        self.job = job
        self.signals = JobSignals()

    @Slot()
    def run(self):
        self.job.started = datetime.now()
        self.job.status = "Running"

        self.signals.started.emit(self.job.name)
        log(f"Job started: {self.job.name}")

        try:
            result = self.job.function(*self.job.args, **self.job.kwargs)

            self.job.result = result
            self.job.status = "Completed"
            self.job.finished = datetime.now()

            job_result = JobResult(
                name=self.job.name,
                status=self.job.status,
                started=self.job.started,
                finished=self.job.finished,
                result=result,
            )

            log(f"Job finished: {self.job.name}")
            self.signals.finished.emit(job_result)

        except Exception:
            self.job.status = "Failed"
            self.job.finished = datetime.now()
            self.job.error = traceback.format_exc()

            job_result = JobResult(
                name=self.job.name,
                status=self.job.status,
                started=self.job.started,
                finished=self.job.finished,
                error=self.job.error,
            )

            log(self.job.error)
            self.signals.failed.emit(job_result)


class JobManager(QObject):
    job_started = Signal(str)
    job_message = Signal(str, str)
    job_finished = Signal(object)
    job_failed = Signal(object)

    def __init__(self):
        super().__init__()

        self.pool = QThreadPool.globalInstance()
        self.jobs = []

    def submit(self, job: Job):
        self.jobs.append(job)

        worker = JobWorker(job)

        worker.signals.started.connect(self.job_started.emit)
        worker.signals.message.connect(self.job_message.emit)
        worker.signals.finished.connect(self.job_finished.emit)
        worker.signals.failed.connect(self.job_failed.emit)

        self.pool.start(worker)

        return worker

    def active_jobs(self):
        return [job for job in self.jobs if job.status == "Running"]

    def completed_jobs(self):
        return [job for job in self.jobs if job.status == "Completed"]

    def failed_jobs(self):
        return [job for job in self.jobs if job.status == "Failed"]


job_manager = JobManager()