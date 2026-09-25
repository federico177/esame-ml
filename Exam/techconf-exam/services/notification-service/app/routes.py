"""Flask blueprint for notification-service HTTP layer."""
from flask import Blueprint, request, jsonify, current_app
from . import service as svc

notifications_bp = Blueprint("notifications", __name__)


def _repo():
    return current_app.config["REPOSITORY"]


def _error(code, message, details=None, status=400):
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


@notifications_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "notification-service"}), 200


@notifications_bp.route("/api/v1/notifications", methods=["POST"])
def create_notification():
    data = _get_json()
    try:
        n = svc.create_notification(_repo(), data)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.ReferenceNotFoundError as e:
        return _error("REFERENCE_NOT_FOUND", str(e), status=422)
    except svc.DependencyError as e:
        return _error("DEPENDENCY_UNAVAILABLE", str(e), status=503)
    resp = jsonify(n)
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/notifications/{n['id']}"
    return resp


@notifications_bp.route("/api/v1/notifications", methods=["GET"])
def list_notifications():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except (ValueError, TypeError):
        return _error("VALIDATION_ERROR", "page and page_size must be integers", status=422)
    try:
        items, total = svc.list_notifications(_repo(), page, page_size,
                                              user_id=request.args.get("user_id"),
                                              status=request.args.get("status"))
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    return jsonify({"items": items, "page": page, "page_size": page_size, "total": total}), 200


@notifications_bp.route("/api/v1/notifications/broadcast", methods=["POST"])
def broadcast():
    data = _get_json()
    try:
        result = svc.broadcast(_repo(), data)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.DependencyError as e:
        return _error("DEPENDENCY_UNAVAILABLE", str(e), status=503)
    resp = jsonify(result)
    resp.status_code = 201
    return resp


@notifications_bp.route("/api/v1/notifications/<string:n_id>", methods=["GET"])
def get_notification(n_id):
    try:
        n = svc.get_notification(_repo(), n_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Notification {n_id} not found", status=404)
    return jsonify(n), 200


@notifications_bp.route("/api/v1/notifications/<string:n_id>", methods=["PATCH"])
def patch_notification(n_id):
    data = _get_json()
    try:
        n = svc.patch_notification(_repo(), n_id, data)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Notification {n_id} not found", status=404)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.InvalidStatusTransitionError as e:
        return _error("INVALID_STATUS_TRANSITION", str(e), status=422)
    return jsonify(n), 200


@notifications_bp.route("/api/v1/notifications/<string:n_id>", methods=["DELETE"])
def delete_notification(n_id):
    try:
        svc.delete_notification(_repo(), n_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Notification {n_id} not found", status=404)
    return "", 204


@notifications_bp.app_errorhandler(400)
def bad_request(e):
    return _error("BAD_REQUEST", "Malformed JSON body", status=400)
