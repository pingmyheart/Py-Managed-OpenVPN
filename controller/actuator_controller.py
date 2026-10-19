"""Expose static health and readiness endpoints under ``/actuator``."""

from flask import Blueprint, jsonify

from configuration.logging_configuration import logger as log

blueprint = Blueprint('actuator', __name__, url_prefix='/actuator')


@blueprint.route('/health', methods=['GET'])
def health():
    """Report application liveness without probing external dependencies.

    :return: A JSON response with status ``healthy`` and HTTP status 200.
    """
    log.info("[INCOMING REQUEST] - Health actuator")
    return jsonify(status="healthy"), 200


@blueprint.route('/readiness', methods=['GET'])
def readiness():
    """Report readiness without probing VPN state or external dependencies.

    :return: A JSON response with status ``ready`` and HTTP status 200.
    """
    log.info("[INCOMING REQUEST] - Ready actuator")
    return jsonify(status="ready"), 200
