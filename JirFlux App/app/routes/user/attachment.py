import os
import re
import uuid
from flask import (Blueprint, redirect, url_for, flash, session, request, abort, current_app, send_from_directory)
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import File, WorkItem, Project
from app.routes.user.user import user_required
from app.routes.user.project_member import project_access, is_project_person
 
attachment_bp = Blueprint('attachment', __name__)
 
MAX_FILE_SIZE = 5 * 1024 * 1024          # 5 MB per file
MAX_FILES_PER_ITEM = 20
 
# what each real file type is allowed to be called
_ALLOWED_EXTENSIONS = {
    'image/png': {'.png'},
    'image/jpeg': {'.jpg', '.jpeg'},
    'application/pdf': {'.pdf'},
}
_STORED_EXTENSION = {'image/png': '.png', 'image/jpeg': '.jpg', 'application/pdf': '.pdf'}
 
 
def upload_dir():
    return os.path.join(current_app.instance_path, 'uploads')
 
 
def _sniff_type(head):
    """Work out the real file type from the first bytes, not from the file name."""
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if head.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if head.startswith(b'%PDF-'):
        return 'application/pdf'
    return None
 
 
def _display_name(filename):
    """The name shown on the page. Keeps any language, removes path parts and control characters."""
    name = os.path.basename((filename or '').replace('\\', '/'))
    name = re.sub(r'[\x00-\x1f\x7f]', '', name).strip()
    return (name or 'file')[:150]
 
 
# ---------- helpers used by other files when a work item / project is deleted ----------
 
def stored_paths(work_items):
    """Collect the stored file names of these work items. Call this BEFORE deleting them."""
    return [f.file_path for wi in work_items for f in wi.files]
 
 
def remove_stored_files(paths):
    """Delete the files from disk. Call this AFTER the database delete was committed."""
    for stored in paths:
        try:
            os.remove(os.path.join(upload_dir(), stored))
        except OSError:
            pass
 

def _load_item(p_id, w_id):
    proj = Project.query.get_or_404(p_id)
    work_item = WorkItem.query.get_or_404(w_id)
    if work_item.p_id != p_id:               # item must belong to this project
        abort(404)
    return proj, work_item
 
 
# ---------- routes ----------
 
# Attach a file (owner, or member who isn't a visitor)
@attachment_bp.route('/project/<int:p_id>/workitem/<int:w_id>/file/add', methods=['POST'])
def add_file(p_id, w_id):
    denied = user_required()
    if denied:
        return denied
 
    proj, work_item = _load_item(p_id, w_id)
    uid = session['user_id']
    back = redirect(url_for('project.project'))
 
    if not project_access(proj):
        flash("Visitors cannot attach files.", "error")
        return back
 
    upload = request.files.get('file')
    if not upload or not upload.filename:
        flash("Choose a file first.", "error")
        return back
 
    if File.query.filter_by(w_id=w_id).count() >= MAX_FILES_PER_ITEM:
        flash(f"A work item can have at most {MAX_FILES_PER_ITEM} files.", "error")
        return back
 
    data = upload.read(MAX_FILE_SIZE + 1)
    if not data:
        flash("That file is empty.", "error")
        return back
    if len(data) > MAX_FILE_SIZE:
        flash("That file is larger than 5 MB.", "error")
        return back
 
    mime = _sniff_type(data[:16])
    if not mime:
        flash("Only PNG, JPEG and PDF files are allowed.", "error")
        return back
 
    original_ext = os.path.splitext(upload.filename)[1].lower()
    if original_ext not in _ALLOWED_EXTENSIONS[mime]:
        flash("The file name does not match what is inside the file.", "error")
        return back
 
    # saved under a random name, so the original name can never touch the disk
    stored = uuid.uuid4().hex + _STORED_EXTENSION[mime]
    os.makedirs(upload_dir(), exist_ok=True)
    path = os.path.join(upload_dir(), stored)
    with open(path, 'wb') as out:
        out.write(data)
 
    try:
        db.session.add(File(
            f_title=_display_name(upload.filename),
            f_type=mime,
            f_size=len(data),
            file_path=stored,
            u_id=uid,
            w_id=w_id,
        ))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        try:
            os.remove(path)                   # don't leave a file with no database row
        except OSError:
            pass
        flash("Could not save the file.", "error")
        return back
 
    flash("File attached.", "success")
    return back
 
 
# Open / download a file (anyone in the project, visitors included)
@attachment_bp.route('/project/<int:p_id>/workitem/<int:w_id>/file/<int:f_id>')
def download_file(p_id, w_id, f_id):
    denied = user_required()
    if denied:
        return denied
 
    proj, work_item = _load_item(p_id, w_id)
    f = File.query.get_or_404(f_id)
    if f.w_id != w_id:
        abort(404)
 
    if not is_project_person(proj, session['user_id']):
        abort(403)
 
    response = send_from_directory(upload_dir(), f.file_path,
                                   mimetype=f.f_type, download_name=f.f_title)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response
 
 
# Remove a file (only the person who attached it)
@attachment_bp.route('/project/<int:p_id>/workitem/<int:w_id>/file/delete/<int:f_id>', methods=['POST'])
def delete_file(p_id, w_id, f_id):
    denied = user_required()
    if denied:
        return denied
 
    proj, work_item = _load_item(p_id, w_id)
    f = File.query.get_or_404(f_id)
    if f.w_id != w_id:
        abort(404)
 
    if f.u_id != session['user_id']:
        flash("You can only remove files you attached.", "error")
        return redirect(url_for('project.project'))
 
    stored = f.file_path
    db.session.delete(f)
    db.session.commit()
    remove_stored_files([stored])
 
    flash("File removed.", "success")
    return redirect(url_for('project.project'))
 