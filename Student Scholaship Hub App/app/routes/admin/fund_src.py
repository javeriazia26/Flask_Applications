from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import FundingSource
from app.routes.admin.admin import admin_required, log_action  # shared helper

fund_src_bp = Blueprint('fund_src', __name__)


# LIST all funding sources
@fund_src_bp.route('/admin/fund_src')
def fund_src():
    denied = admin_required()
    if denied:
        return denied

    all_funding_sources = FundingSource.query.all()
    
    edit_id = request.args.get('edit')
    editing_fund_src = None
    if edit_id:
        editing_fund_src = FundingSource.query.get(edit_id)    

    return render_template('admin/fund_src.html',
        funding_sources=all_funding_sources,
        editing_fund_src=editing_fund_src
    )


# ADD funding source
@fund_src_bp.route('/admin/fund_src/add', methods=['POST'])
def add_fund_src():
    denied = admin_required()
    if denied:
        return denied

    source_name = request.form.get('source_name')
    phone_no    = request.form.get('phone_no')
    email_id    = request.form.get('email_id')
    type        = request.form.get('type')

    # Duplicate check
    existing = FundingSource.query.filter_by(source_name=source_name).first()
    if existing:
        flash(f'Funding source "{source_name}" already exists in the system.', "error")
        return redirect(url_for('fund_src.fund_src'))

    new_fund_src = FundingSource(
        source_name = source_name,
        phone_no    = phone_no,
        email_id    = email_id,
        type        = type
    )

    db.session.add(new_fund_src)
    db.session.commit()
    log_action('Added', 'Funding Source')
    


    flash(f'Funding source "{source_name}" has been added successfully.', "success")
    return redirect(url_for('fund_src.fund_src'))


# EDIT funding source
@fund_src_bp.route('/admin/fund_src/edit/<int:f_source_id>', methods=['GET', 'POST'])
def edit_fund_src(f_source_id):
    denied = admin_required()
    if denied:
        return denied

    funding_source = FundingSource.query.get_or_404(f_source_id)

    if request.method == 'POST':
        funding_source.source_name = request.form.get('source_name')
        funding_source.phone_no    = request.form.get('phone_no')
        funding_source.email_id    = request.form.get('email_id')
        funding_source.type        = request.form.get('type')

        db.session.commit()
        log_action('Updated', 'Funding Source')
        flash(f'Funding source "{funding_source.source_name}" has been updated successfully.', "success")
        return redirect(url_for('fund_src.fund_src'))

    return redirect(url_for('fund_src.fund_src'))


# DELETE funding source
@fund_src_bp.route('/admin/fund_src/delete/<int:f_source_id>', methods=['POST'])
def delete_fund_src(f_source_id):
    denied = admin_required()
    if denied:
        return denied

    funding_source = FundingSource.query.get_or_404(f_source_id)
    source_name = funding_source.source_name

    db.session.delete(funding_source)
    db.session.commit()
    log_action('Deleted', 'Funding Source')

    flash(f'Funding source "{source_name}" has been permanently removed from the system.', "error")
    return redirect(url_for('fund_src.fund_src'))