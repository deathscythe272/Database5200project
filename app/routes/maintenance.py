from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import MaintenanceSchedule, Equipment, WorkOrder
from datetime import datetime, timedelta

maintenance_bp = Blueprint('maintenance', __name__)


@maintenance_bp.route('/')
@login_required
def list_schedules():
    page = request.args.get('page', 1, type=int)
    equipment_id = request.args.get('equipment_id', type=int)
    overdue = request.args.get('overdue')
    
    query = MaintenanceSchedule.query.filter_by(is_active=True)
    
    if equipment_id:
        query = query.filter_by(equipment_id=equipment_id)
    if overdue:
        query = query.filter(MaintenanceSchedule.next_due < datetime.utcnow())
    
    schedules = query.order_by(MaintenanceSchedule.next_due).paginate(page=page, per_page=20)
    equipment = Equipment.query.filter(Equipment.status != 'retired').order_by(Equipment.name).all()
    
    return render_template('maintenance/list.html', schedules=schedules, equipment=equipment)


@maintenance_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        schedule = MaintenanceSchedule(
            equipment_id=request.form.get('equipment_id'),
            task_name=request.form.get('task_name'),
            description=request.form.get('description'),
            frequency_days=request.form.get('frequency_days') or None,
            frequency_hours=request.form.get('frequency_hours') or None,
            estimated_duration_min=request.form.get('estimated_duration_min') or None,
            priority=request.form.get('priority', 'medium')
        )
        
        # Calculate next due
        if schedule.frequency_days:
            schedule.next_due = datetime.utcnow() + timedelta(days=schedule.frequency_days)
        
        db.session.add(schedule)
        db.session.commit()
        
        flash(f'Maintenance schedule "{schedule.task_name}" created.', 'success')
        return redirect(url_for('maintenance.list_schedules'))
    
    equipment = Equipment.query.filter(Equipment.status != 'retired').order_by(Equipment.name).all()
    selected_equipment = request.args.get('equipment_id', type=int)
    
    return render_template('maintenance/form.html', 
                          schedule=None, 
                          equipment=equipment,
                          selected_equipment=selected_equipment)


@maintenance_bp.route('/<int:schedule_id>')
@login_required
def view(schedule_id):
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    related_work_orders = WorkOrder.query.filter_by(schedule_id=schedule_id).order_by(WorkOrder.created_at.desc()).limit(10).all()
    return render_template('maintenance/view.html', schedule=schedule, work_orders=related_work_orders)


@maintenance_bp.route('/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(schedule_id):
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    if request.method == 'POST':
        schedule.task_name = request.form.get('task_name')
        schedule.description = request.form.get('description')
        schedule.frequency_days = request.form.get('frequency_days') or None
        schedule.frequency_hours = request.form.get('frequency_hours') or None
        schedule.estimated_duration_min = request.form.get('estimated_duration_min') or None
        schedule.priority = request.form.get('priority')
        schedule.is_active = request.form.get('is_active') == 'on'
        schedule.version += 1
        
        db.session.commit()
        flash('Maintenance schedule updated.', 'success')
        return redirect(url_for('maintenance.view', schedule_id=schedule_id))
    
    equipment = Equipment.query.filter(Equipment.status != 'retired').order_by(Equipment.name).all()
    return render_template('maintenance/form.html', schedule=schedule, equipment=equipment)


@maintenance_bp.route('/<int:schedule_id>/create-work-order', methods=['POST'])
@login_required
def create_work_order(schedule_id):
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    # Create work order from schedule
    work_order = WorkOrder(
        equipment_id=schedule.equipment_id,
        schedule_id=schedule.schedule_id,
        title=f"{schedule.task_name} - {schedule.equipment.name}",
        description=schedule.description,
        type='preventive',
        priority=schedule.priority,
        created_by=current_user.user_id
    )
    
    db.session.add(work_order)
    db.session.flush()
    work_order.generate_number()
    db.session.commit()
    
    flash(f'Work order {work_order.work_order_number} created from maintenance schedule.', 'success')
    return redirect(url_for('work_orders.view', work_order_id=work_order.work_order_id))


@maintenance_bp.route('/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete(schedule_id):
    if not current_user.is_manager():
        flash('Only managers can delete maintenance schedules.', 'danger')
        return redirect(url_for('maintenance.list_schedules'))
    
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    schedule.is_active = False
    db.session.commit()
    
    flash('Maintenance schedule deactivated.', 'success')
    return redirect(url_for('maintenance.list_schedules'))


@maintenance_bp.route('/upcoming')
@login_required
def upcoming():
    days = request.args.get('days', 7, type=int)
    
    schedules = MaintenanceSchedule.query.filter(
        MaintenanceSchedule.is_active == True,
        MaintenanceSchedule.next_due <= datetime.utcnow() + timedelta(days=days)
    ).order_by(MaintenanceSchedule.next_due).all()
    
    return render_template('maintenance/upcoming.html', schedules=schedules, days=days, today=datetime.utcnow().date())


@maintenance_bp.route('/overdue')
@login_required
def overdue():
    schedules = MaintenanceSchedule.query.filter(
        MaintenanceSchedule.is_active == True,
        MaintenanceSchedule.next_due < datetime.utcnow()
    ).order_by(MaintenanceSchedule.next_due).all()
    
    return render_template('maintenance/overdue.html', schedules=schedules, now=datetime.utcnow())
