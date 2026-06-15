# web.py
import json
import time
from flask import Flask, Response, render_template, stream_with_context
from src.plc_reader import state, state_lock

# Set by main.py before app.run()
poll_interval: float = 1.0
template_path: str = ""

app = Flask(__name__)


@app.route("/")
def index():
    app.template_folder = template_path
    return render_template("index.html")


@app.route("/stream")
def stream():
    """SSE — pushes {"output": "..."} to the browser every second."""
    @stream_with_context
    def event_stream():
        while True:
            with state_lock:
                payload = json.dumps(state)
            yield f"data: {payload}\n\n"
            time.sleep(poll_interval)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",   # nginx: disable proxy buffering
        },
    )