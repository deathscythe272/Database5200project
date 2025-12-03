from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Equipment, EquipmentCategory, Location
from sqlalchemy.exc import IntegrityError

equipment_bp = Blueprint('equipment', __name__)


@equipment_bp.route('/')
@login_required
def list_equipment():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    category_id = request.args.get('category', type=int)
    location_id = request.args.get('location', type=int)
    search = request.args.get('search', '')
    
    query = Equipment.query
    
    if status:
        query = query.filter_by(status=status)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if location_id:
        query = query.filter_by(location_id=location_id)
    if search:
        query = query.filter(
            db.or_(
                Equipment.name.ilike(f'%{search}%'),
                Equipment.serial_number.ilike(f'%{search}%'),
                Equipment.manufacturer.ilike(f'%{search}%')
            )
        )
    
    equipment = query.order_by(Equipment.name).paginate(page=page, per_page=20)
    categories = EquipmentCategory.query.order_by(EquipmentCategory.name).all()
    locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    
    return render_template('equipment/list.html', 
                          equipment=equipment, 
                          categories=categories,
                          locations=locations)


@equipment_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        equipment = Equipment(
            name=request.form.get('name'),
            model=request.form.get('model'),
            serial_number=request.form.get('serial_number') or None,
            manufacturer=request.form.get('manufacturer'),
            category_id=request.form.get('category_id') or None,
            location_id=request.form.get('location_id') or None,
            purchase_date=request.form.get('purchase_date') or None,
            purchase_price=request.form.get('purchase_price') or None,
            warranty_expiration=request.form.get('warranty_expiration') or None,
            status=request.form.get('status', 'active'),
            notes=request.form.get('notes')
        )
        
        try:
            db.session.add(equipment)
            db.session.commit()
            flash(f'Equipment "{equipment.name}" created successfully.', 'success')
            return redirect(url_for('equipment.view', equipment_id=equipment.equipment_id))
        except IntegrityError:
            db.session.rollback()
            flash('Serial number already exists.', 'danger')
    
    categories = EquipmentCategory.query.order_by(EquipmentCategory.name).all()
    locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    
    return render_template('equipment/form.html', 
                          categories=categories, 
                          locations=locations,
                          equipment=None)


@equipment_bp.route('/<int:equipment_id>')
@login_required
def view(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template('equipment/view.html', equipment=equipment)


@equipment_bp.route('/<int:equipment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    if request.method == 'POST':
        # Check version for optimistic locking
        submitted_version = int(request.form.get('version', 0))
        if submitted_version != equipment.version:
            flash('This record was modified by another user. Please review and try again.', 'warning')
            return redirect(url_for('equipment.edit', equipment_id=equipment_id))
        
        equipment.name = request.form.get('name')
        equipment.model = request.form.get('model')
        equipment.serial_number = request.form.get('serial_number') or None
        equipment.manufacturer = request.form.get('manufacturer')
        equipment.category_id = request.form.get('category_id') or None
        equipment.location_id = request.form.get('location_id') or None
        equipment.purchase_date = request.form.get('purchase_date') or None
        equipment.purchase_price = request.form.get('purchase_price') or None
        equipment.warranty_expiration = request.form.get('warranty_expiration') or None
        equipment.status = request.form.get('status')
        equipment.usage_hours = request.form.get('usage_hours') or 0
        equipment.notes = request.form.get('notes')
        equipment.version += 1
        
        try:
            db.session.commit()
            flash('Equipment updated successfully.', 'success')
            return redirect(url_for('equipment.view', equipment_id=equipment_id))
        except IntegrityError:
            db.session.rollback()
            flash('Serial number already exists.', 'danger')
    
    categories = EquipmentCategory.query.order_by(EquipmentCategory.name).all()
    locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    
    return render_template('equipment/form.html', 
                          equipment=equipment,
                          categories=categories, 
                          locations=locations)


@equipment_bp.route('/<int:equipment_id>/delete', methods=['POST'])
@login_required
def delete(equipment_id):
    if not current_user.is_manager():
        flash('Only managers can delete equipment.', 'danger')
        return redirect(url_for('equipment.list_equipment'))
    
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Soft delete - set to retired
    equipment.status = 'retired'
    db.session.commit()
    
    flash(f'Equipment "{equipment.name}" has been retired.', 'success')
    return redirect(url_for('equipment.list_equipment'))
