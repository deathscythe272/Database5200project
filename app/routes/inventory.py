from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Part, PartsInventory, Location, InventoryTransaction
from sqlalchemy.exc import IntegrityError

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/')
@login_required
def list_inventory():
    page = request.args.get('page', 1, type=int)
    location_id = request.args.get('location', type=int)
    low_stock = request.args.get('low_stock')
    search = request.args.get('search', '')
    
    query = PartsInventory.query.join(Part)
    
    if location_id:
        query = query.filter(PartsInventory.location_id == location_id)
    if low_stock:
        query = query.filter(PartsInventory.quantity_on_hand <= PartsInventory.reorder_point)
    if search:
        query = query.filter(
            db.or_(
                Part.name.ilike(f'%{search}%'),
                Part.part_number.ilike(f'%{search}%')
            )
        )
    
    inventory = query.order_by(Part.name).paginate(page=page, per_page=20)
    locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    
    return render_template('inventory/list.html', 
                          inventory=inventory,
                          locations=locations)


@inventory_bp.route('/parts')
@login_required
def list_parts():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Part.query
    
    if search:
        query = query.filter(
            db.or_(
                Part.name.ilike(f'%{search}%'),
                Part.part_number.ilike(f'%{search}%'),
                Part.category.ilike(f'%{search}%')
            )
        )
    
    parts = query.order_by(Part.name).paginate(page=page, per_page=20)
    return render_template('inventory/parts.html', parts=parts)


@inventory_bp.route('/parts/create', methods=['GET', 'POST'])
@login_required
def create_part():
    if request.method == 'POST':
        part = Part(
            part_number=request.form.get('part_number'),
            name=request.form.get('name'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            unit_cost=request.form.get('unit_cost') or None
        )
        
        try:
            db.session.add(part)
            db.session.commit()
            flash(f'Part "{part.name}" created successfully.', 'success')
            return redirect(url_for('inventory.list_parts'))
        except IntegrityError:
            db.session.rollback()
            flash('Part number already exists.', 'danger')
    
    return render_template('inventory/part_form.html', part=None)


@inventory_bp.route('/parts/<int:part_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_part(part_id):
    part = Part.query.get_or_404(part_id)
    
    if request.method == 'POST':
        part.part_number = request.form.get('part_number')
        part.name = request.form.get('name')
        part.description = request.form.get('description')
        part.category = request.form.get('category')
        part.unit_cost = request.form.get('unit_cost') or None
        
        try:
            db.session.commit()
            flash('Part updated successfully.', 'success')
            return redirect(url_for('inventory.list_parts'))
        except IntegrityError:
            db.session.rollback()
            flash('Part number already exists.', 'danger')
    
    return render_template('inventory/part_form.html', part=part)


@inventory_bp.route('/receive', methods=['GET', 'POST'])
@login_required
def receive_parts():
    if request.method == 'POST':
        part_id = request.form.get('part_id', type=int)
        location_id = request.form.get('location_id', type=int)
        quantity = request.form.get('quantity', type=int)
        unit_cost = request.form.get('unit_cost', type=float)
        reference = request.form.get('reference')
        
        # Find or create inventory record
        inventory = PartsInventory.query.filter_by(
            part_id=part_id, 
            location_id=location_id
        ).first()
        
        if not inventory:
            inventory = PartsInventory(
                part_id=part_id,
                location_id=location_id,
                quantity_on_hand=0
            )
            db.session.add(inventory)
            db.session.flush()
        
        # Update quantity
        inventory.quantity_on_hand += quantity
        inventory.version += 1
        
        # Log transaction
        transaction = InventoryTransaction(
            inventory_id=inventory.inventory_id,
            transaction_type='receipt',
            quantity=quantity,
            unit_cost=unit_cost,
            reference_number=reference,
            performed_by=current_user.user_id
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Received {quantity} units into inventory.', 'success')
        return redirect(url_for('inventory.list_inventory'))
    
    parts = Part.query.filter_by(is_active=True).order_by(Part.name).all()
    locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    
    return render_template('inventory/receive.html', parts=parts, locations=locations)


@inventory_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue_parts():
    if request.method == 'POST':
        inventory_id = request.form.get('inventory_id', type=int)
        quantity = request.form.get('quantity', type=int)
        work_order_id = request.form.get('work_order_id', type=int) or None
        notes = request.form.get('notes')
        
        inventory = PartsInventory.query.get_or_404(inventory_id)
        
        # Check available quantity
        if inventory.available < quantity:
            flash(f'Insufficient inventory. Available: {inventory.available}', 'danger')
            return redirect(url_for('inventory.issue_parts'))
        
        # Update quantity
        inventory.quantity_on_hand -= quantity
        inventory.version += 1
        
        # Log transaction
        transaction = InventoryTransaction(
            inventory_id=inventory_id,
            work_order_id=work_order_id,
            transaction_type='issue',
            quantity=-quantity,
            unit_cost=inventory.part.unit_cost,
            notes=notes,
            performed_by=current_user.user_id
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Issued {quantity} units from inventory.', 'success')
        return redirect(url_for('inventory.list_inventory'))
    
    from app.models import WorkOrder
    inventory = PartsInventory.query.join(Part).order_by(Part.name).all()
    work_orders = WorkOrder.query.filter(WorkOrder.status.in_(['open', 'in_progress'])).all()
    
    return render_template('inventory/issue.html', inventory=inventory, work_orders=work_orders)


@inventory_bp.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    
    transactions = InventoryTransaction.query.order_by(
        InventoryTransaction.created_at.desc()
    ).paginate(page=page, per_page=50)
    
    return render_template('inventory/transactions.html', transactions=transactions)


@inventory_bp.route('/low-stock')
@login_required
def low_stock():
    inventory = PartsInventory.query.join(Part).filter(
        PartsInventory.quantity_on_hand <= PartsInventory.reorder_point
    ).order_by(Part.name).all()
    
    return render_template('inventory/low_stock.html', inventory=inventory)
