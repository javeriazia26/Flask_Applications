# app/routes/user/avatar.py
import io
import time

from flask import Blueprint, Response, abort, session
from PIL import Image, ImageOps

from app import db
from app.models import User

avatar_bp = Blueprint("avatar", __name__)

MAX_UPLOAD_BYTES = 2 * 1024 * 1024      # 2 MB
MAX_PIXELS = 25_000_000                 # guards against decompression bombs
AVATAR_SIZE = (256, 256)


def save_avatar(user, file):
    """Validate, resize and store an uploaded image on ``user``.

    The caller is responsible for committing the session.
    Returns an error message, or ``None`` on success.
    """
    raw = file.read(MAX_UPLOAD_BYTES + 1)

    if not raw:
        return "No file received."
    if len(raw) > MAX_UPLOAD_BYTES:
        return "Image must be under 2 MB."

    try:
        image = Image.open(io.BytesIO(raw))
        if image.width * image.height > MAX_PIXELS:
            return "Image dimensions are too large."

        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail(AVATAR_SIZE)

        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=85)
    except Exception:
        return "That file is not a valid image."

    user.avatar_data = buffer.getvalue()
    user.avatar_mime = "image/jpeg"
    # The ?v= value changes on every upload so browsers drop the cached image.
    user.picture = f"/avatar/{user.user_id}?v={int(time.time())}"
    return None


@avatar_bp.route("/avatar/<int:user_id>")
def avatar(user_id):
    """Serve a user's profile picture to any logged-in user."""
    if "user_id" not in session:
        abort(401)

    user = db.session.get(User, user_id)
    if not user or not user.avatar_data:
        abort(404)

    response = Response(user.avatar_data, mimetype=user.avatar_mime or "image/jpeg")
    response.headers["Cache-Control"] = "private, max-age=86400"
    return response