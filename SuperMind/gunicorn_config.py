timeout = 300  # Increase timeout to 5 minutes
workers = 2  # Reduce number of workers
worker_class = 'gthread'  # Use threaded workers
threads = 4  # Number of threads per worker
max_requests = 1000
max_requests_jitter = 50