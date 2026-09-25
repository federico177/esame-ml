"""
Flask blueprint for user-service HTTP layer.
No business logic here — all rules live in service.py.
"""
from flask import Blueprint, request, jsonify, current_app

from . import service as svc

users_bp = Blueprint("users", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _repo():
    return current_app.config["REPOSITORY"]


def _error(code: str, message: str, details: dict = None, status: int = 400):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def _get_json():
    """Parse JSON body; raise 400 on malformed input."""
    data = request.get_json(silent=True)
    if data is None:
        from flask import abort
        abort(400)
    return data


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@users_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "user-service"}), 200


# ---------------------------------------------------------------------------
# Collection endpoints
# ---------------------------------------------------------------------------

@users_bp.route("/api/v1/users", methods=["POST"])
def create_user():
    data = _get_json()
    try:
        user = svc.create_user(_repo(), data)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.ConflictError as e:
        return _error(e.code, e.message, status=409)

    response = jsonify(user)
    response.status_code = 201
    response.headers["Location"] = f"/api/v1/users/{user['id']}"
    return response


@users_bp.route("/api/v1/users", methods=["GET"])
def list_users():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except (ValueError, TypeError):
        return _error("VALIDATION_ERROR", "page and page_size must be integers", status=422)

    role = request.args.get("role")
    email = request.args.get("email")

    try:
        items, total = svc.list_users(_repo(), page, page_size, role=role, email=email)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)

    return jsonify({"items": items, "page": page, "page_size": page_size, "total": total}), 200


# ---------------------------------------------------------------------------
# Resource endpoints
# ---------------------------------------------------------------------------

@users_bp.route("/api/v1/users/<string:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user = svc.get_user(_repo(), user_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"User {user_id} not found", status=404)
    return jsonify(user), 200


@users_bp.route("/api/v1/users/<string:user_id>", methods=["PUT"])
def replace_user(user_id):
    data = _get_json()
    try:
        user = svc.replace_user(_repo(), user_id, data)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"User {user_id} not found", status=404)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.ConflictError as e:
        return _error(e.code, e.message, status=409)
    return jsonify(user), 200


@users_bp.route("/api/v1/users/<string:user_id>", methods=["PATCH"])
def patch_user(user_id):
    data = _get_json()
    try:
        user = svc.patch_user(_repo(), user_id, data)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"User {user_id} not found", status=404)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.ConflictError as e:
        return _error(e.code, e.message, status=409)
    return jsonify(user), 200


@users_bp.route("/api/v1/users/<string:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        svc.delete_user(_repo(), user_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"User {user_id} not found", status=404)
    return "", 204


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@users_bp.app_errorhandler(400)
def bad_request(e):
    return _error("BAD_REQUEST", "Malformed JSON body", status=400)


@users_bp.app_errorhandler(405)
def method_not_allowed(e):
    return _error("METHOD_NOT_ALLOWED", "Method not allowed", status=405)
