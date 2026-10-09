from flask import Blueprint, request, jsonify

from configuration.logging_configuration import logger as log
from dto.create_client import CreateClientRequest
from dto.delete_client import DeleteClientRequest
from dto.renew_client import RenewClientRequest
from dto.revoke_client import RevokeClientRequest
from enumeration.response_code_enums import ResponseCodeEnums
from service import client_service, openvpn_service

blueprint = Blueprint('client', __name__, url_prefix='/py-managed-openvpn/client')


@blueprint.route('', methods=['POST'])
def create_new_client():
    log.info("[INCOMING REQUEST] - Create new client")
    request_data = CreateClientRequest(**request.get_json())
    response = client_service.create_client(request_data=request_data)
    return (jsonify(response.model_dump()),
            ResponseCodeEnums.get_by_code(code=response.code).http_status_code)


@blueprint.route('', methods=['PATCH'])
def renew_client():
    log.info("[INCOMING REQUEST] - Renew client")
    request_data = RenewClientRequest(**request.get_json())
    response = client_service.renew_client(request_data=request_data)
    return (jsonify(response.model_dump()),
            ResponseCodeEnums.get_by_code(code=response.code).http_status_code)


@blueprint.route('/<client_name>/revoke', methods=['DELETE'])
def revoke_client(client_name):
    log.info("[INCOMING REQUEST] - Revoke client")
    request_data = RevokeClientRequest(client_name=client_name)
    response = client_service.revoke_client(request_data=request_data)
    return (jsonify(response.model_dump()),
            ResponseCodeEnums.get_by_code(code=response.code).http_status_code)


@blueprint.route('/<client_name>', methods=['GET'])
def download_client(client_name):
    log.info("[INCOMING REQUEST] - Download client")
    response = client_service.generate_client_openvpn_file(client_name=client_name)
    return (jsonify(response.model_dump()),
            ResponseCodeEnums.get_by_code(code=response.code).http_status_code)


@blueprint.route('/<client_name>', methods=['DELETE'])
def delete_client(client_name):
    log.info("[INCOMING REQUEST] - Delete client")
    request_data = DeleteClientRequest(client_name=client_name)
    response = client_service.delete_client(request_data=request_data)
    return (jsonify(response.model_dump()),
            ResponseCodeEnums.get_by_code(code=response.code).http_status_code)


@blueprint.route('/connected', methods=['GET'])
def obtain_connected_clients():
    log.info("[INCOMING REQUEST] - Obtain connected clients")
    response = openvpn_service.obtain_connected_clients()
    return (jsonify(response.model_dump()),
            ResponseCodeEnums.get_by_code(code=response.code).http_status_code)
