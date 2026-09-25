"""Flask blueprint for registration-service HTTP layer."""
from flask import Blueprint, request, jsonify, current_app
from . import service as svc

registrations_bp = Blueprint("registrations", __name__)


def _repo():
    return current_app.config["REPOSITORY"]


def _error(code: str, message: str, details: dict = None, status: int = 400):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def _get_json():
    data = request.get_json(silent=True)
    if data is None:
        from flask import abort
        abort(400)
    return data


@registrations_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "registration-service"}), 200


@registrations_bp.route("/api/v1/registrations", methods=["POST"])
def create_registration():
    data = _get_json()
    try:
        reg = svc.create_registration(_repo(), data)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.ReferenceNotFoundError as e:
        return _error("REFERENCE_NOT_FOUND", str(e), status=422)
    except svc.EventNotOpenError as e:
        return _error("EVENT_NOT_OPEN", str(e), status=422)
    except svc.ConflictError as e:
        return _error(e.code, e.message, status=409)
    except svc.DependencyError as e:
        return _error("DEPENDENCY_UNAVAILABLE", str(e), status=503)
    resp = jsonify(reg)
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/registrations/{reg['id']}"
    return resp


@registrations_bp.route("/api/v1/registrations", methods=["GET"])
def list_registrations():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except (ValueError, TypeError):
        return _error("VALIDATION_ERROR", "page and page_size must be integers", status=422)

    user_id = request.args.get("user_id")
    event_id = request.args.get("event_id")
    status = request.args.get("status")

    try:
        items, total = svc.list_registrations(_repo(), page, page_size,
                                               user_id=user_id, event_id=event_id, status=status)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)

    return jsonify({"items": items, "page": page, "page_size": page_size, "total": total}), 200


# Stats must be declared BEFORE /{id} to avoid Flask matching "stats" as an id
@registrations_bp.route("/api/v1/registrations/stats", methods=["GET"])
def get_stats():
    event_id = request.args.get("event_id")
    if not event_id:
        return _error("VALIDATION_ERROR", "event_id is required", status=422)
    try:
        stats = svc.get_stats(_repo(), event_id)
    except svc.NotFoundError as e:
        return _error("NOT_FOUND", str(e), status=404)
    except svc.DependencyError as e:
        return _error("DEPENDENCY_UNAVAILABLE", str(e), status=503)
    return jsonify(stats), 200


@registrations_bp.route("/api/v1/registrations/<string:reg_id>", methods=["GET"])
def get_registration(reg_id):
    try:
        reg = svc.get_registration(_repo(), reg_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Registration {reg_id} not found", status=404)
    return jsonify(reg), 200


@registrations_bp.route("/api/v1/registrations/<string:reg_id>", methods=["PUT"])
def put_not_allowed(reg_id):
    return _error("METHOD_NOT_ALLOWED", "PUT is not allowed on registrations", status=405)


@registrations_bp.route("/api/v1/registrations/<string:reg_id>", methods=["PATCH"])
def patch_registration(reg_id):
    data = _get_json()
    try:
        reg = svc.patch_registration(_repo(), reg_id, data)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Registration {reg_id} not found", status=404)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.InvalidStatusTransitionError as e:
        return _error("INVALID_STATUS_TRANSITION", str(e), status=422)
    return jsonify(reg), 200


@registrations_bp.route("/api/v1/registrations/<string:reg_id>", methods=["DELETE"])
def delete_registration(reg_id):
    try:
        svc.delete_registration(_repo(), reg_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Registration {reg_id} not found", status=404)
    return "", 204


@registrations_bp.app_errorhandler(400)
def bad_request(e):
    return _error("BAD_REQUEST", "Malformed JSON body", status=400)
