from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import WorkOrder, Equipment, User, Location
from datetime import datetime

work_orders_bp = Blueprint('work_orders', __name__)


@work_orders_bp.route('/')
@login_required
def list_work_orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    wo_type = request.args.get('type')
    assigned_to = request.args.get('assigned_to', type=int)
    my_orders = request.args.get('my_orders')
    
    query = WorkOrder.query
    
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if wo_type:
        query = query.filter_by(type=wo_type)
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    if my_orders:
        query = query.filter_by(assigned_to=current_user.user_id)
    
    # Default sort: priority then date
    query = query.order_by(
        db.case(
            (WorkOrder.priority == 'critical', 1),
            (WorkOrder.priority == 'high', 2),
            (WorkOrder.priority == 'medium', 3),
            else_=4
        ),
        WorkOrder.scheduled_date.asc().nullslast()
    )
    
    work_orders = query.paginate(page=page, per_page=20)
    technicians = User.query.filter(User.role.in_(['technician', 'manager'])).order_by(User.first_name).all()
    
    return render_template('work_orders/list.html', 
                          work_orders=work_orders,
                          technicians=technicians)


@work_orders_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        work_order = WorkOrder(
            equipment_id=request.form.get('equipment_id'),
            title=request.form.get('title'),
            description=request.form.get('description'),
            type=request.form.get('type'),
            priority=request.form.get('priority', 'medium'),
            assigned_to=request.form.get('assigned_to') or None,
            created_by=current_user.user_id,
            scheduled_date=request.form.get('scheduled_date') or None
        )
        
        db.session.add(work_order)
        db.session.flush()  # Get the ID
        work_order.generate_number()
        db.session.commit()
        
        flash(f'Work order {work_order.work_order_number} created successfully.', 'success')
        return redirect(url_for('work_orders.view', work_order_id=work_order.work_order_id))
    
    equipment = Equipment.query.filter(Equipment.status != 'retired').order_by(Equipment.name).all()
    technicians = User.query.filter(User.role.in_(['technician', 'manager']), User.is_active == True).order_by(User.first_name).all()
    
    # Pre-select equipment if passed in URL
    selected_equipment = request.args.get('equipment_id', type=int)
    
    return render_template('work_orders/form.html',
                          equipment=equipment,
                          technicians=technicians,
                          work_order=None,
                          selected_equipment=selected_equipment)


@work_orders_bp.route('/<int:work_order_id>')
@login_required
def view(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    return render_template('work_orders/view.html', work_order=work_order)


@work_orders_bp.route('/<int:work_order_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    
    if request.method == 'POST':
        # Optimistic locking check
        submitted_version = int(request.form.get('version', 0))
        if submitted_version != work_order.version:
            flash('This work order was modified by another user. Please review and try again.', 'warning')
            return redirect(url_for('work_orders.edit', work_order_id=work_order_id))
        
        work_order.title = request.form.get('title')
        work_order.description = request.form.get('description')
        work_order.type = request.form.get('type')
        work_order.priority = request.form.get('priority')
        work_order.assigned_to = request.form.get('assigned_to') or None
        work_order.scheduled_date = request.form.get('scheduled_date') or None
        work_order.notes = request.form.get('notes')
        work_order.version += 1
        
        db.session.commit()
        flash('Work order updated successfully.', 'success')
        return redirect(url_for('work_orders.view', work_order_id=work_order_id))
    
    equipment = Equipment.query.filter(Equipment.status != 'retired').order_by(Equipment.name).all()
    technicians = User.query.filter(User.role.in_(['technician', 'manager']), User.is_active == True).order_by(User.first_name).all()
    
    return render_template('work_orders/form.html',
                          work_order=work_order,
                          equipment=equipment,
                          technicians=technicians,
                          selected_equipment=work_order.equipment_id)


@work_orders_bp.route('/<int:work_order_id>/start', methods=['POST'])
@login_required
def start(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    
    if work_order.status != 'open':
        flash('Can only start work orders with "open" status.', 'warning')
        return redirect(url_for('work_orders.view', work_order_id=work_order_id))
    
    work_order.status = 'in_progress'
    work_order.started_at = datetime.utcnow()
    work_order.version += 1
    
    # Set equipment to under_repair if it's a corrective/emergency order
    if work_order.type in ['corrective', 'emergency']:
        work_order.equipment.status = 'under_repair'
    
    db.session.commit()
    flash('Work order started.', 'success')
    return redirect(url_for('work_orders.view', work_order_id=work_order_id))


@work_orders_bp.route('/<int:work_order_id>/complete', methods=['GET', 'POST'])
@login_required
def complete(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    
    if work_order.status not in ['open', 'in_progress']:
        flash('Cannot complete this work order.', 'warning')
        return redirect(url_for('work_orders.view', work_order_id=work_order_id))
    
    if request.method == 'POST':
        work_order.status = 'completed'
        work_order.completed_at = datetime.utcnow()
        work_order.labor_hours = request.form.get('labor_hours') or None
        work_order.labor_cost = request.form.get('labor_cost') or None
        work_order.notes = request.form.get('notes')
        work_order.version += 1
        
        # Set equipment back to active
        if work_order.equipment.status == 'under_repair':
            work_order.equipment.status = 'active'
        
        # Update maintenance schedule if linked
        if work_order.schedule:
            work_order.schedule.last_performed = datetime.utcnow()
        
        db.session.commit()
        flash(f'Work order {work_order.work_order_number} completed!', 'success')
        return redirect(url_for('work_orders.view', work_order_id=work_order_id))
    
    return render_template('work_orders/complete.html', work_order=work_order)


@work_orders_bp.route('/<int:work_order_id>/cancel', methods=['POST'])
@login_required
def cancel(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    
    if work_order.status in ['completed', 'cancelled']:
        flash('Cannot cancel this work order.', 'warning')
        return redirect(url_for('work_orders.view', work_order_id=work_order_id))
    
    reason = request.form.get('reason', 'No reason provided')
    work_order.status = 'cancelled'
    work_order.notes = (work_order.notes or '') + f'\n\nCancelled: {reason}'
    work_order.version += 1
    
    db.session.commit()
    flash('Work order cancelled.', 'info')
    return redirect(url_for('work_orders.view', work_order_id=work_order_id))
