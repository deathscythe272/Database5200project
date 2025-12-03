from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import (Equipment, WorkOrder, MaintenanceSchedule, 
                        PartsInventory, Part, Location, EquipmentCategory, User)

api_bp = Blueprint('api', __name__)


# ============================================
# Equipment API
# ============================================

@api_bp.route('/equipment', methods=['GET'])
@login_required
def get_equipment():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Equipment.query
    
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    location_id = request.args.get('location_id', type=int)
    if location_id:
        query = query.filter_by(location_id=location_id)
    
    equipment = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [e.to_dict() for e in equipment.items],
        'total': equipment.total,
        'page': page,
        'pages': equipment.pages
    })


@api_bp.route('/equipment/<int:equipment_id>', methods=['GET'])
@login_required
def get_equipment_detail(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    return jsonify(equipment.to_dict())


@api_bp.route('/equipment', methods=['POST'])
@login_required
def create_equipment():
    if not current_user.is_manager():
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    equipment = Equipment(
        name=data.get('name'),
        model=data.get('model'),
        serial_number=data.get('serial_number'),
        manufacturer=data.get('manufacturer'),
        category_id=data.get('category_id'),
        location_id=data.get('location_id'),
        status=data.get('status', 'active')
    )
    
    db.session.add(equipment)
    db.session.commit()
    
    return jsonify(equipment.to_dict()), 201


@api_bp.route('/equipment/<int:equipment_id>', methods=['PUT'])
@login_required
def update_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    data = request.get_json()
    
    # Optimistic locking
    if data.get('version') and data['version'] != equipment.version:
        return jsonify({'error': 'Concurrent modification detected'}), 409
    
    for field in ['name', 'model', 'serial_number', 'manufacturer', 'status', 'notes']:
        if field in data:
            setattr(equipment, field, data[field])
    
    equipment.version += 1
    db.session.commit()
    
    return jsonify(equipment.to_dict())


# ============================================
# Work Orders API
# ============================================

@api_bp.route('/work-orders', methods=['GET'])
@login_required
def get_work_orders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = WorkOrder.query
    
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    assigned_to = request.args.get('assigned_to', type=int)
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    
    work_orders = query.order_by(WorkOrder.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [wo.to_dict() for wo in work_orders.items],
        'total': work_orders.total,
        'page': page,
        'pages': work_orders.pages
    })


@api_bp.route('/work-orders/<int:work_order_id>', methods=['GET'])
@login_required
def get_work_order_detail(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    data = work_order.to_dict()
    data['parts_used'] = [p.to_dict() for p in work_order.parts_used]
    return jsonify(data)


@api_bp.route('/work-orders', methods=['POST'])
@login_required
def create_work_order():
    data = request.get_json()
    
    work_order = WorkOrder(
        equipment_id=data.get('equipment_id'),
        title=data.get('title'),
        description=data.get('description'),
        type=data.get('type'),
        priority=data.get('priority', 'medium'),
        assigned_to=data.get('assigned_to'),
        created_by=current_user.user_id
    )
    
    db.session.add(work_order)
    db.session.flush()
    work_order.generate_number()
    db.session.commit()
    
    return jsonify(work_order.to_dict()), 201


@api_bp.route('/work-orders/<int:work_order_id>/status', methods=['PATCH'])
@login_required
def update_work_order_status(work_order_id):
    work_order = WorkOrder.query.get_or_404(work_order_id)
    data = request.get_json()
    
    new_status = data.get('status')
    if new_status not in ['open', 'in_progress', 'on_hold', 'completed', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    work_order.status = new_status
    work_order.version += 1
    
    if new_status == 'completed':
        from datetime import datetime
        work_order.completed_at = datetime.utcnow()
        work_order.labor_hours = data.get('labor_hours')
    
    db.session.commit()
    return jsonify(work_order.to_dict())


# ============================================
# Inventory API
# ============================================

@api_bp.route('/inventory', methods=['GET'])
@login_required
def get_inventory():
    location_id = request.args.get('location_id', type=int)
    low_stock = request.args.get('low_stock', type=bool)
    
    query = PartsInventory.query
    
    if location_id:
        query = query.filter_by(location_id=location_id)
    if low_stock:
        query = query.filter(PartsInventory.quantity_on_hand <= PartsInventory.reorder_point)
    
    inventory = query.all()
    return jsonify([i.to_dict() for i in inventory])


@api_bp.route('/inventory/<int:inventory_id>/adjust', methods=['POST'])
@login_required
def adjust_inventory(inventory_id):
    inventory = PartsInventory.query.get_or_404(inventory_id)
    data = request.get_json()
    
    quantity = data.get('quantity', 0)
    transaction_type = data.get('type', 'adjustment')
    
    if transaction_type == 'issue' and inventory.available < abs(quantity):
        return jsonify({'error': 'Insufficient inventory'}), 400
    
    inventory.quantity_on_hand += quantity
    inventory.version += 1
    
    from app.models import InventoryTransaction
    transaction = InventoryTransaction(
        inventory_id=inventory_id,
        transaction_type=transaction_type,
        quantity=quantity,
        notes=data.get('notes'),
        performed_by=current_user.user_id
    )
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify(inventory.to_dict())


# ============================================
# Lookup Data API
# ============================================

@api_bp.route('/locations', methods=['GET'])
@login_required
def get_locations():
    locations = Location.query.filter_by(is_active=True).all()
    return jsonify([l.to_dict() for l in locations])


@api_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    categories = EquipmentCategory.query.all()
    return jsonify([c.to_dict() for c in categories])


@api_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    role = request.args.get('role')
    query = User.query.filter_by(is_active=True)
    
    if role:
        query = query.filter_by(role=role)
    
    users = query.all()
    return jsonify([u.to_dict() for u in users])


# ============================================
# Dashboard Stats API
# ============================================

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    from datetime import datetime
    
    stats = {
        'equipment': {
            'total': Equipment.query.count(),
            'active': Equipment.query.filter_by(status='active').count(),
            'under_repair': Equipment.query.filter_by(status='under_repair').count()
        },
        'work_orders': {
            'open': WorkOrder.query.filter_by(status='open').count(),
            'in_progress': WorkOrder.query.filter_by(status='in_progress').count(),
            'completed_today': WorkOrder.query.filter(
                WorkOrder.status == 'completed',
                db.func.date(WorkOrder.completed_at) == datetime.utcnow().date()
            ).count()
        },
        'maintenance': {
            'overdue': MaintenanceSchedule.query.filter(
                MaintenanceSchedule.is_active == True,
                MaintenanceSchedule.next_due < datetime.utcnow()
            ).count()
        },
        'inventory': {
            'low_stock': PartsInventory.query.filter(
                PartsInventory.quantity_on_hand <= PartsInventory.reorder_point
            ).count()
        }
    }
    
    return jsonify(stats)
