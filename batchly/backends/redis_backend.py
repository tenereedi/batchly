import json
from typing import Optional
from batchly.job import Job
from batchly.backends.base import BaseBackend


class RedisBackend(BaseBackend):
    """Redis-backed FIFO job queue using a Redis list.

    Requires the ``redis`` package to be installed.
    The queue is stored under ``key`` in the provided Redis instance.
    """

    def __init__(self, redis_client, key: str = "batchly:queue") -> None:
        self._redis = redis_client
        self._key = key

    def push(self, job: Job) -> None:
        payload = json.dumps({
            "id": job.id,
            "func": f"{job.func.__module__}.{job.func.__qualname__}",
            "args": job.args,
            "kwargs": job.kwargs,
            "max_retries": job.max_retries,
            "retries": job.retries,
            "status": job.status.value,
        })
        self._redis.rpush(self._key, payload)

    def pop(self) -> Optional[Job]:
        raw = self._redis.lpop(self._key)
        if raw is None:
            return None
        return self._deserialize(raw)

    def peek(self) -> Optional[Job]:
        raw = self._redis.lindex(self._key, 0)
        if raw is None:
            return None
        return self._deserialize(raw)

    def size(self) -> int:
        return self._redis.llen(self._key)

    def clear(self) -> None:
        self._redis.delete(self._key)

    def _deserialize(self, raw) -> Job:
        import importlib
        from batchly.job import JobStatus
        data = json.loads(raw)
        module_path, _, func_name = data["func"].rpartition(".")
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        job = Job(func, args=data["args"], kwargs=data["kwargs"],
                  max_retries=data["max_retries"])
        job.retries = data["retries"]
        job.status = JobStatus(data["status"])
        return job
