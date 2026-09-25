"""Flask blueprint for feedback-service HTTP layer."""
from flask import Blueprint, request, jsonify, current_app
from . import service as svc

feedbacks_bp = Blueprint("feedbacks", __name__)


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


@feedbacks_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "feedback-service"}), 200


@feedbacks_bp.route("/api/v1/feedbacks", methods=["POST"])
def create_feedback():
    data = _get_json()
    try:
        fb = svc.create_feedback(_repo(), data)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.NotRegisteredError as e:
        return _error("NOT_REGISTERED", str(e), status=422)
    except svc.ConflictError as e:
        return _error(e.code, e.message, status=409)
    except svc.DependencyError as e:
        return _error("DEPENDENCY_UNAVAILABLE", str(e), status=503)
    resp = jsonify(fb)
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/feedbacks/{fb['id']}"
    return resp


@feedbacks_bp.route("/api/v1/feedbacks", methods=["GET"])
def list_feedbacks():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except (ValueError, TypeError):
        return _error("VALIDATION_ERROR", "page and page_size must be integers", status=422)
    try:
        items, total = svc.list_feedbacks(_repo(), page, page_size,
                                          event_id=request.args.get("event_id"),
                                          user_id=request.args.get("user_id"))
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    return jsonify({"items": items, "page": page, "page_size": page_size, "total": total}), 200


@feedbacks_bp.route("/api/v1/feedbacks/summary", methods=["GET"])
def summary():
    event_id = request.args.get("event_id")
    if not event_id:
        return _error("VALIDATION_ERROR", "event_id is required", status=422)
    try:
        result = svc.get_summary(_repo(), event_id)
    except svc.NotFoundError as e:
        return _error("NOT_FOUND", str(e), status=404)
    except svc.DependencyError as e:
        return _error("DEPENDENCY_UNAVAILABLE", str(e), status=503)
    return jsonify(result), 200


@feedbacks_bp.route("/api/v1/feedbacks/<string:fb_id>", methods=["GET"])
def get_feedback(fb_id):
    try:
        fb = svc.get_feedback(_repo(), fb_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Feedback {fb_id} not found", status=404)
    return jsonify(fb), 200


@feedbacks_bp.route("/api/v1/feedbacks/<string:fb_id>", methods=["PATCH"])
def patch_feedback(fb_id):
    data = _get_json()
    try:
        fb = svc.patch_feedback(_repo(), fb_id, data)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Feedback {fb_id} not found", status=404)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    return jsonify(fb), 200


@feedbacks_bp.route("/api/v1/feedbacks/<string:fb_id>", methods=["DELETE"])
def delete_feedback(fb_id):
    try:
        svc.delete_feedback(_repo(), fb_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Feedback {fb_id} not found", status=404)
    return "", 204


@feedbacks_bp.app_errorhandler(400)
def bad_request(e):
    return _error("BAD_REQUEST", "Malformed JSON body", status=400)
