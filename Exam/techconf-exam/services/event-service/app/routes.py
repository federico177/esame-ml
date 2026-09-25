"""Flask blueprint for event-service HTTP layer."""
from flask import Blueprint, request, jsonify, current_app
from . import service as svc

events_bp = Blueprint("events", __name__)


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


# Health
@events_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "event-service"}), 200


# Collection
@events_bp.route("/api/v1/events", methods=["POST"])
def create_event():
    data = _get_json()
    try:
        event = svc.create_event(_repo(), data)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.ReferenceNotFoundError as e:
        return _error("REFERENCE_NOT_FOUND", str(e), status=422)
    except svc.InvalidOrganizerError as e:
        return _error("INVALID_ORGANIZER", str(e), status=422)
    except svc.DependencyError as e:
        return _error("DEPENDENCY_UNAVAILABLE", str(e), status=503)

    resp = jsonify(event)
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/events/{event['id']}"
    return resp


@events_bp.route("/api/v1/events", methods=["GET"])
def list_events():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except (ValueError, TypeError):
        return _error("VALIDATION_ERROR", "page and page_size must be integers", status=422)

    status = request.args.get("status")
    city = request.args.get("city")

    try:
        items, total = svc.list_events(_repo(), page, page_size, status=status, city=city)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)

    return jsonify({"items": items, "page": page, "page_size": page_size, "total": total}), 200


# Resource
@events_bp.route("/api/v1/events/<string:event_id>", methods=["GET"])
def get_event(event_id):
    try:
        event = svc.get_event(_repo(), event_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Event {event_id} not found", status=404)
    return jsonify(event), 200


@events_bp.route("/api/v1/events/<string:event_id>", methods=["PUT"])
def replace_event(event_id):
    data = _get_json()
    try:
        event = svc.replace_event(_repo(), event_id, data)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Event {event_id} not found", status=404)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.ReferenceNotFoundError as e:
        return _error("REFERENCE_NOT_FOUND", str(e), status=422)
    except svc.InvalidOrganizerError as e:
        return _error("INVALID_ORGANIZER", str(e), status=422)
    except svc.InvalidStatusTransitionError as e:
        return _error("INVALID_STATUS_TRANSITION", str(e), status=422)
    except svc.DependencyError as e:
        return _error("DEPENDENCY_UNAVAILABLE", str(e), status=503)
    return jsonify(event), 200


@events_bp.route("/api/v1/events/<string:event_id>", methods=["PATCH"])
def patch_event(event_id):
    data = _get_json()
    try:
        event = svc.patch_event(_repo(), event_id, data)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Event {event_id} not found", status=404)
    except svc.ValidationError as e:
        return _error("VALIDATION_ERROR", e.message, e.details, 422)
    except svc.ReferenceNotFoundError as e:
        return _error("REFERENCE_NOT_FOUND", str(e), status=422)
    except svc.InvalidOrganizerError as e:
        return _error("INVALID_ORGANIZER", str(e), status=422)
    except svc.InvalidStatusTransitionError as e:
        return _error("INVALID_STATUS_TRANSITION", str(e), status=422)
    except svc.DependencyError as e:
        return _error("DEPENDENCY_UNAVAILABLE", str(e), status=503)
    return jsonify(event), 200


@events_bp.route("/api/v1/events/<string:event_id>", methods=["DELETE"])
def delete_event(event_id):
    try:
        svc.delete_event(_repo(), event_id)
    except svc.NotFoundError:
        return _error("NOT_FOUND", f"Event {event_id} not found", status=404)
    return "", 204


# Error handlers
@events_bp.app_errorhandler(400)
def bad_request(e):
    return _error("BAD_REQUEST", "Malformed JSON body", status=400)


@events_bp.app_errorhandler(405)
def method_not_allowed(e):
    return _error("METHOD_NOT_ALLOWED", "Method not allowed", status=405)
