
import time

def mock_retries(n=None,
    interval=2,
    timeout=None,
    message="Operation timed-out (too many retries)"
):
    if (n is None) and (timeout is None):
        raise Exception("Specify either n or timeout for retries")

    if (n is not None) and (timeout is not None):
        interval = timeout / n

    if timeout is None:
        timeout = n * interval
    remaining = timeout
    n = 0
    while remaining > 0:
        remaining = remaining - interval
        n = n + 1
        yield n
        time.sleep(0)
    raise Exception(message)
