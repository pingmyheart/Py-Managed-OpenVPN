from flask import Blueprint, jsonify

from configuration.logging_configuration import logger as log

blueprint = Blueprint('actuator', __name__, url_prefix='/actuator')


@blueprint.route('/health', methods=['GET'])
def health():
    log.info("[INCOMING REQUEST] - Health actuator")
    return jsonify(status="healthy"), 200


@blueprint.route('/readiness', methods=['GET'])
def readiness():
    log.info("[INCOMING REQUEST] - Ready actuator")
    return jsonify(status="ready"), 200
