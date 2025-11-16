import logging
import time
from app.anchor_service import perform_anchor_sync, start_anchor_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

print("=== SYNC CALL ===")
res = perform_anchor_sync({"resource_id": "demo-sync"}, {"user_id": "dev-user"})
print("sync result:", res)

print("\n=== ASYNC CALL ===")
job = start_anchor_job({"resource_id": "demo-async"}, {"user_id": "dev-user"})
print("async job:", job)

# let the background thread run briefly so its logs appear
time.sleep(1)
print("done")
