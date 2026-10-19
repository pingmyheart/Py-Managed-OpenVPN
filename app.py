"""Create the instrumented Flask app and initialize the VPN on import.

Importing this module verifies external tools, initializes persistent VPN files,
registers HTTP routes, and starts the background PKI scheduler.
"""

from flask import Flask
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider

from exception.tool_not_installed_exception import ToolNotInstalledException
from scheduling import scheduler
from util import (initialization_util)


def verify_tools():
    """Check that the OpenSSL and OpenVPN version commands succeed.

    :raises ToolNotInstalledException: If either tool is missing or its version
        command exits with a nonzero status.
    """
    from service import tool_service
    if not tool_service.check_openssl_is_installed():
        raise ToolNotInstalledException("OpenSSL")
    if not tool_service.check_openvpn_is_installed():
        raise ToolNotInstalledException("OpenVPN")


from controller import blueprints

provider = TracerProvider()
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("py-managed-openvpn")

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


@app.after_request
def add_trace_headers(response):
    """Attach the active trace identifier to an outgoing Flask response.

    :param response: Flask response to modify in place.
    :return: The same response with a ``Request-ID`` header containing the trace
        ID, or ``no-trace`` when no valid span is active.
    """
    span = trace.get_current_span()
    ctx = span.get_span_context()

    if ctx and ctx.is_valid:
        trace_id = format(ctx.trace_id, "032x")
    else:
        trace_id = "no-trace"

    response.headers["Request-ID"] = trace_id
    return response


for blueprint in blueprints:
    app.register_blueprint(blueprint)

verify_tools()
initialization_util.initialize()
scheduler.start()

if __name__ == '__main__':
    app.run(host="0.0.0.0",
            port=5000,
            debug=False)
