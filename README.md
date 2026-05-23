# batchly

Simple job queue library for Python with pluggable backends and retry policies.

---

## Installation

```bash
pip install batchly
```

## Usage

```python
from batchly import Queue, job

# Define a job
@job
def send_email(to, subject, body):
    # your logic here
    print(f"Sending email to {to}")

# Create a queue and enqueue work
q = Queue(backend="redis", url="redis://localhost:6379")

q.enqueue(send_email, to="user@example.com", subject="Hello", body="World")

# Start processing
q.run()
```

### Retry Policy

```python
from batchly import Queue, job, RetryPolicy

@job(retry=RetryPolicy(max_retries=3, backoff=2.0))
def flaky_task(data):
    process(data)
```

### Backends

| Backend   | Install Extra         |
|-----------|-----------------------|
| Redis     | `pip install batchly[redis]`  |
| In-Memory | built-in              |
| SQLite    | built-in              |

## Configuration

```python
q = Queue(
    backend="redis",
    url="redis://localhost:6379",
    workers=4,
    default_timeout=30,
)
```

## License

[MIT](LICENSE)