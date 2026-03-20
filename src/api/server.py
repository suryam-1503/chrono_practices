import os
import threading
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from src.modmed.modmed_claims_main import run_workflow, stop_workflow, check_stop_flag_status
from src.utils.logger import LOG_FILE, setup_logger

logger = setup_logger(__name__)
app = FastAPI(title="ModMed Automation API")

automation_thread = None
automation_running = False


@app.post("/start")
def start_automation():
    global automation_thread, automation_running

    if automation_running:
        return JSONResponse(content={"status": "Automation already running"}, status_code=400)

    def task():
        global automation_running
        try:
            logger.info("Automation thread started")
            run_workflow()
        finally:
            automation_running = False
            logger.info("Automation thread finished")

    automation_running = True
    automation_thread = threading.Thread(target=task, daemon=True)
    automation_thread.start()

    logger.info("Automation started")
    return {"status": "Automation started"}


@app.post("/stop")
def stop_automation_api():
    stop_workflow()
    logger.info("Stop requested")
    return {"status": "Stopping"}


@app.get("/status")
def automation_status():
    if automation_running and not check_stop_flag_status():
        return {"status": "running"}
    return {"status": "stopped"}


@app.get("/logs")
def get_logs(
    level: str | None = Query(None),
    date: str | None = Query(None),
    limit: int | None = Query(None)
):
    if not os.path.exists(LOG_FILE):
        return {"error": "Log file not found"}

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    filtered_logs = []

    for line in lines:
        if level and f"| {level.upper()} |" not in line:
            continue
        if date and not line.startswith(date):
            continue
        filtered_logs.append(line.strip())

    if limit:
        filtered_logs = filtered_logs[-limit:]

    return JSONResponse(content={"logs": filtered_logs})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)