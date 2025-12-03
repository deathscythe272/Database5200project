from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Equipment, WorkOrder, MaintenanceSchedule, PartsInventory
from datetime import datetime, timedelta
from sqlalchemy import func

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


from flask import redirect, url_for

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Equipment stats
    total_equipment = Equipment.query.count()
    active_equipment = Equipment.query.filter_by(status='active').count()
    under_repair = Equipment.query.filter_by(status='under_repair').count()
    
    # Work order stats
    open_work_orders = WorkOrder.query.filter(WorkOrder.status.in_(['open', 'in_progress'])).count()
    my_work_orders = WorkOrder.query.filter_by(assigned_to=current_user.user_id, status='open').count()
    
    # Overdue maintenance
    overdue_maintenance = MaintenanceSchedule.query.filter(
        MaintenanceSchedule.is_active == True,
        MaintenanceSchedule.next_due < datetime.utcnow()
    ).count()
    
    # Low stock items
    low_stock = PartsInventory.query.filter(
        PartsInventory.quantity_on_hand <= PartsInventory.reorder_point
    ).count()
    
    # Recent work orders
    recent_work_orders = WorkOrder.query.order_by(WorkOrder.created_at.desc()).limit(5).all()
    
    # Upcoming maintenance
    upcoming_maintenance = MaintenanceSchedule.query.filter(
        MaintenanceSchedule.is_active == True,
        MaintenanceSchedule.next_due <= datetime.utcnow() + timedelta(days=7)
    ).order_by(MaintenanceSchedule.next_due).limit(5).all()
    
    stats = {
        'total_equipment': total_equipment,
        'active_equipment': active_equipment,
        'under_repair': under_repair,
        'open_work_orders': open_work_orders,
        'my_work_orders': my_work_orders,
        'overdue_maintenance': overdue_maintenance,
        'low_stock': low_stock
    }
    
    return render_template('main/dashboard.html', 
                          stats=stats, 
                          recent_work_orders=recent_work_orders,
                          upcoming_maintenance=upcoming_maintenance)
