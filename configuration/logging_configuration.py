import logging
import sys

from opentelemetry import trace


class TraceContextFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        span_ctx = span.get_span_context()

        if span_ctx and span_ctx.is_valid:
            record.trace_id = format(span_ctx.trace_id, "032x")
            record.span_id = format(span_ctx.span_id, "016x")
        else:
            record.trace_id = "no-trace"
            record.span_id = "no-span"

        return True


logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(trace_id)s,%(span_id)s] %(levelname)s %(message)s',
                              '%Y-%m-%d %H:%M:%S')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)
stdout_handler.addFilter(TraceContextFilter())

logger.addHandler(stdout_handler)
