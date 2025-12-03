from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager, bcrypt


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Location(db.Model):
    __tablename__ = 'locations'
    
    location_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    equipment = db.relationship('Equipment', backref='location', lazy='dynamic')
    users = db.relationship('User', backref='location', lazy='dynamic')
    inventory = db.relationship('PartsInventory', backref='location', lazy='dynamic')
    
    def to_dict(self):
        return {
            'location_id': self.location_id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'is_active': self.is_active
        }


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='technician')
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_work_orders = db.relationship('WorkOrder', foreign_keys='WorkOrder.assigned_to', backref='assignee', lazy='dynamic')
    created_work_orders = db.relationship('WorkOrder', foreign_keys='WorkOrder.created_by', backref='creator', lazy='dynamic')
    
    def get_id(self):
        return str(self.user_id)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role in ['admin', 'manager']
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'is_active': self.is_active
        }


class EquipmentCategory(db.Model):
    __tablename__ = 'equipment_categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    equipment = db.relationship('Equipment', backref='category', lazy='dynamic')
    
    def to_dict(self):
        return {
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description
        }


class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    equipment_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100), unique=True)
    manufacturer = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('equipment_categories.category_id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'))
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Numeric(10, 2))
    warranty_expiration = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')
    usage_hours = db.Column(db.Numeric(10, 2), default=0)
    notes = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    maintenance_schedules = db.relationship('MaintenanceSchedule', backref='equipment', lazy='dynamic', cascade='all, delete-orphan')
    work_orders = db.relationship('WorkOrder', backref='equipment', lazy='dynamic')
    
    @property
    def under_warranty(self):
        if self.warranty_expiration:
            return self.warranty_expiration > datetime.utcnow().date()
        return False
    
    def to_dict(self):
        return {
            'equipment_id': self.equipment_id,
            'name': self.name,
            'model': self.model,
            'serial_number': self.serial_number,
            'manufacturer': self.manufacturer,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'purchase_price': float(self.purchase_price) if self.purchase_price else None,
            'warranty_expiration': self.warranty_expiration.isoformat() if self.warranty_expiration else None,
            'under_warranty': self.under_warranty,
            'status': self.status,
            'usage_hours': float(self.usage_hours) if self.usage_hours else 0,
            'notes': self.notes,
            'version': self.version
        }


class MaintenanceSchedule(db.Model):
    __tablename__ = 'maintenance_schedules'
    
    schedule_id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.equipment_id', ondelete='CASCADE'), nullable=False)
    task_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    frequency_days = db.Column(db.Integer)
    frequency_hours = db.Column(db.Numeric(10, 2))
    estimated_duration_min = db.Column(db.Integer)
    priority = db.Column(db.String(20), default='medium')
    is_active = db.Column(db.Boolean, default=True)
    last_performed = db.Column(db.DateTime)
    next_due = db.Column(db.DateTime)
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    work_orders = db.relationship('WorkOrder', backref='schedule', lazy='dynamic')
    
    @property
    def is_overdue(self):
        if self.next_due:
            return self.next_due < datetime.utcnow()
        return False
    
    def to_dict(self):
        return {
            'schedule_id': self.schedule_id,
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment.name if self.equipment else None,
            'task_name': self.task_name,
            'description': self.description,
            'frequency_days': self.frequency_days,
            'frequency_hours': float(self.frequency_hours) if self.frequency_hours else None,
            'estimated_duration_min': self.estimated_duration_min,
            'priority': self.priority,
            'is_active': self.is_active,
            'last_performed': self.last_performed.isoformat() if self.last_performed else None,
            'next_due': self.next_due.isoformat() if self.next_due else None,
            'is_overdue': self.is_overdue
        }


class Vendor(db.Model):
    __tablename__ = 'vendors'
    
    vendor_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(100))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    website = db.Column(db.String(255))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'vendor_id': self.vendor_id,
            'name': self.name,
            'contact_name': self.contact_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'website': self.website,
            'is_active': self.is_active
        }


class Part(db.Model):
    __tablename__ = 'parts'
    
    part_id = db.Column(db.Integer, primary_key=True)
    part_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    unit_cost = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    inventory = db.relationship('PartsInventory', backref='part', lazy='dynamic')
    
    def to_dict(self):
        return {
            'part_id': self.part_id,
            'part_number': self.part_number,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'is_active': self.is_active
        }


class PartsInventory(db.Model):
    __tablename__ = 'parts_inventory'
    
    inventory_id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.part_id', ondelete='CASCADE'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id', ondelete='CASCADE'), nullable=False)
    quantity_on_hand = db.Column(db.Integer, default=0)
    quantity_reserved = db.Column(db.Integer, default=0)
    reorder_point = db.Column(db.Integer, default=0)
    reorder_quantity = db.Column(db.Integer, default=1)
    bin_location = db.Column(db.String(50))
    last_counted = db.Column(db.DateTime)
    version = db.Column(db.Integer, default=1)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('part_id', 'location_id'),)
    
    @property
    def available(self):
        return self.quantity_on_hand - self.quantity_reserved
    
    @property
    def is_low_stock(self):
        return self.quantity_on_hand <= self.reorder_point
    
    def to_dict(self):
        return {
            'inventory_id': self.inventory_id,
            'part_id': self.part_id,
            'part_number': self.part.part_number if self.part else None,
            'part_name': self.part.name if self.part else None,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'quantity_on_hand': self.quantity_on_hand,
            'quantity_reserved': self.quantity_reserved,
            'available': self.available,
            'reorder_point': self.reorder_point,
            'bin_location': self.bin_location,
            'is_low_stock': self.is_low_stock,
            'version': self.version
        }


class WorkOrder(db.Model):
    __tablename__ = 'work_orders'
    
    work_order_id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.equipment_id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('maintenance_schedules.schedule_id'))
    work_order_number = db.Column(db.String(20), unique=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='open')
    priority = db.Column(db.String(20), default='medium')
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    scheduled_date = db.Column(db.Date)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    labor_hours = db.Column(db.Numeric(6, 2))
    labor_cost = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parts_used = db.relationship('WorkOrderPart', backref='work_order', lazy='dynamic', cascade='all, delete-orphan')
    
    def generate_number(self):
        if not self.work_order_number:
            date_str = datetime.utcnow().strftime('%Y%m%d')
            self.work_order_number = f"WO-{date_str}-{self.work_order_id:04d}"
    
    @property
    def parts_cost(self):
        total = sum(wp.quantity_used * float(wp.unit_cost or 0) for wp in self.parts_used)
        return total
    
    @property
    def total_cost(self):
        labor = float(self.labor_cost or 0)
        return labor + self.parts_cost
    
    def to_dict(self):
        return {
            'work_order_id': self.work_order_id,
            'work_order_number': self.work_order_number,
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment.name if self.equipment else None,
            'location_name': self.equipment.location.name if self.equipment and self.equipment.location else None,
            'schedule_id': self.schedule_id,
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'assigned_to_name': self.assignee.full_name if self.assignee else None,
            'created_by': self.created_by,
            'created_by_name': self.creator.full_name if self.creator else None,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'labor_hours': float(self.labor_hours) if self.labor_hours else None,
            'labor_cost': float(self.labor_cost) if self.labor_cost else None,
            'parts_cost': self.parts_cost,
            'total_cost': self.total_cost,
            'notes': self.notes,
            'version': self.version
        }


class WorkOrderPart(db.Model):
    __tablename__ = 'work_order_parts'
    
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.work_order_id', ondelete='CASCADE'), primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.part_id'), primary_key=True)
    quantity_used = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2))
    
    part = db.relationship('Part')
    
    def to_dict(self):
        return {
            'part_id': self.part_id,
            'part_number': self.part.part_number if self.part else None,
            'part_name': self.part.name if self.part else None,
            'quantity_used': self.quantity_used,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'total_cost': self.quantity_used * float(self.unit_cost or 0)
        }


class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('parts_inventory.inventory_id'), nullable=False)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.work_order_id'))
    transaction_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2))
    reference_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    inventory = db.relationship('PartsInventory', backref='transactions')
    user = db.relationship('User')
    work_order = db.relationship('WorkOrder')
    
    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'inventory_id': self.inventory_id,
            'work_order_id': self.work_order_id,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'performed_by': self.user.full_name if self.user else None,
            'created_at': self.created_at.isoformat()
        }
