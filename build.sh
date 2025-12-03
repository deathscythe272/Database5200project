#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python << 'EOF'
from datetime import datetime, timedelta
from run import app, db
from app.models import User, Location, EquipmentCategory, Equipment, Part, PartsInventory, MaintenanceSchedule, WorkOrder

with app.app_context():
    db.create_all()
    
    if not User.query.filter_by(username='admin').first():
        # Locations
        loc1 = Location(name='Main Gym Downtown', address='123 Fitness Ave', city='Boston', state='MA', postal_code='02101', phone='617-555-0100')
        loc2 = Location(name='West Side Fitness', address='456 Wellness Blvd', city='Boston', state='MA', postal_code='02134', phone='617-555-0200')
        loc3 = Location(name='Campus Recreation Center', address='789 University Dr', city='Cambridge', state='MA', postal_code='02139', phone='617-555-0300')
        db.session.add_all([loc1, loc2, loc3])
        db.session.flush()
        
        # Categories
        cat1 = EquipmentCategory(name='Cardio', description='Treadmills, ellipticals, bikes')
        cat2 = EquipmentCategory(name='Strength Machines', description='Cable machines, leg press')
        cat3 = EquipmentCategory(name='Free Weights', description='Dumbbells, barbells, plates')
        cat4 = EquipmentCategory(name='Benches & Racks', description='Benches, power racks')
        db.session.add_all([cat1, cat2, cat3, cat4])
        db.session.flush()
        
        # Users
        admin = User(username='admin', email='admin@gymequip.com', first_name='System', last_name='Administrator', role='admin', location_id=loc1.location_id)
        admin.set_password('admin123')
        manager = User(username='manager', email='manager@gymequip.com', first_name='Mike', last_name='Manager', role='manager', location_id=loc1.location_id)
        manager.set_password('manager123')
        tech1 = User(username='tech1', email='tech1@gymequip.com', first_name='Tom', last_name='Technician', role='technician', location_id=loc1.location_id)
        tech1.set_password('tech123')
        tech2 = User(username='tech2', email='tech2@gymequip.com', first_name='Sarah', last_name='Smith', role='technician', location_id=loc2.location_id)
        tech2.set_password('tech123')
        db.session.add_all([admin, manager, tech1, tech2])
        db.session.flush()
        
        # Equipment
        equip1 = Equipment(name='Treadmill Pro 5000', model='TP-5000', serial_number='TM-001-2024', manufacturer='Life Fitness', category_id=cat1.category_id, location_id=loc1.location_id, status='active', purchase_date=datetime(2024,1,15).date(), purchase_price=4500.00, warranty_expiration=datetime(2027,1,15).date(), usage_hours=1250)
        equip2 = Equipment(name='Treadmill Pro 5000', model='TP-5000', serial_number='TM-002-2024', manufacturer='Life Fitness', category_id=cat1.category_id, location_id=loc1.location_id, status='active', purchase_date=datetime(2024,1,15).date(), purchase_price=4500.00, usage_hours=980)
        equip3 = Equipment(name='Elliptical E700', model='E700', serial_number='EL-001-2023', manufacturer='Precor', category_id=cat1.category_id, location_id=loc1.location_id, status='under_repair', purchase_date=datetime(2023,6,1).date(), purchase_price=3800.00, usage_hours=2100)
        equip4 = Equipment(name='Cable Crossover Machine', model='CCM-200', serial_number='CM-001-2024', manufacturer='Hammer Strength', category_id=cat2.category_id, location_id=loc1.location_id, status='active', purchase_date=datetime(2024,3,1).date(), purchase_price=6500.00, usage_hours=650)
        equip5 = Equipment(name='Leg Press', model='LP-450', serial_number='LP-001-2023', manufacturer='Cybex', category_id=cat2.category_id, location_id=loc2.location_id, status='active', purchase_date=datetime(2023,9,15).date(), purchase_price=5200.00, usage_hours=1800)
        equip6 = Equipment(name='Dumbbell Set 5-100lb', model='PRO-DB', serial_number='DB-001-2024', manufacturer='Rogue Fitness', category_id=cat3.category_id, location_id=loc1.location_id, status='active', purchase_date=datetime(2024,2,1).date(), purchase_price=3200.00)
        equip7 = Equipment(name='Power Rack', model='PR-4000', serial_number='PR-001-2024', manufacturer='Rogue Fitness', category_id=cat4.category_id, location_id=loc2.location_id, status='active', purchase_date=datetime(2024,4,1).date(), purchase_price=1800.00, usage_hours=420)
        equip8 = Equipment(name='Adjustable Bench', model='AB-300', serial_number='AB-001-2024', manufacturer='Rep Fitness', category_id=cat4.category_id, location_id=loc1.location_id, status='active', purchase_date=datetime(2024,4,1).date(), purchase_price=450.00)
        db.session.add_all([equip1, equip2, equip3, equip4, equip5, equip6, equip7, equip8])
        db.session.flush()
        
        # Parts
        part1 = Part(part_number='BELT-TM-001', name='Treadmill Drive Belt', description='Replacement drive belt for treadmills', category='Belts', unit_cost=45.00)
        part2 = Part(part_number='MOTOR-TM-001', name='Treadmill Motor', description='2.5HP DC Motor', category='Motors', unit_cost=350.00)
        part3 = Part(part_number='CABLE-CC-001', name='Cable Assembly', description='High-tension steel cable for cable machines', category='Cables', unit_cost=65.00)
        part4 = Part(part_number='PULLEY-001', name='Pulley Wheel', description='Replacement pulley wheel', category='Hardware', unit_cost=28.00)
        part5 = Part(part_number='PAD-001', name='Seat Pad', description='Replacement seat cushion', category='Pads', unit_cost=55.00)
        part6 = Part(part_number='LUBE-001', name='Silicone Lubricant', description='Treadmill belt lubricant', category='Supplies', unit_cost=15.00)
        db.session.add_all([part1, part2, part3, part4, part5, part6])
        db.session.flush()
        
        # Inventory
        inv1 = PartsInventory(part_id=part1.part_id, location_id=loc1.location_id, quantity_on_hand=8, reorder_point=3, reorder_quantity=5, bin_location='A-1-1')
        inv2 = PartsInventory(part_id=part2.part_id, location_id=loc1.location_id, quantity_on_hand=2, reorder_point=1, reorder_quantity=2, bin_location='A-1-2')
        inv3 = PartsInventory(part_id=part3.part_id, location_id=loc1.location_id, quantity_on_hand=5, reorder_point=2, reorder_quantity=4, bin_location='A-2-1')
        inv4 = PartsInventory(part_id=part4.part_id, location_id=loc1.location_id, quantity_on_hand=12, reorder_point=4, reorder_quantity=8, bin_location='A-2-2')
        inv5 = PartsInventory(part_id=part5.part_id, location_id=loc1.location_id, quantity_on_hand=3, reorder_point=2, reorder_quantity=4, bin_location='B-1-1')
        inv6 = PartsInventory(part_id=part6.part_id, location_id=loc1.location_id, quantity_on_hand=15, reorder_point=5, reorder_quantity=10, bin_location='B-1-2')
        inv7 = PartsInventory(part_id=part1.part_id, location_id=loc2.location_id, quantity_on_hand=4, reorder_point=2, reorder_quantity=4, bin_location='A-1-1')
        inv8 = PartsInventory(part_id=part3.part_id, location_id=loc2.location_id, quantity_on_hand=1, reorder_point=2, reorder_quantity=4, bin_location='A-1-2')
        db.session.add_all([inv1, inv2, inv3, inv4, inv5, inv6, inv7, inv8])
        db.session.flush()
        
        # Maintenance Schedules
        maint1 = MaintenanceSchedule(equipment_id=equip1.equipment_id, task_name='Belt Inspection', description='Inspect and lubricate treadmill belt', frequency_days=30, priority='medium', next_due=datetime.utcnow() + timedelta(days=5))
        maint2 = MaintenanceSchedule(equipment_id=equip1.equipment_id, task_name='Motor Service', description='Check motor brushes and bearings', frequency_days=180, priority='high', next_due=datetime.utcnow() + timedelta(days=45))
        maint3 = MaintenanceSchedule(equipment_id=equip4.equipment_id, task_name='Cable Inspection', description='Inspect cables for wear and fraying', frequency_days=14, priority='high', next_due=datetime.utcnow() - timedelta(days=2))
        maint4 = MaintenanceSchedule(equipment_id=equip5.equipment_id, task_name='Lubrication', description='Lubricate guide rods and pivot points', frequency_days=60, priority='medium', next_due=datetime.utcnow() + timedelta(days=20))
        maint5 = MaintenanceSchedule(equipment_id=equip7.equipment_id, task_name='Safety Check', description='Inspect J-hooks and safeties', frequency_days=7, priority='critical', next_due=datetime.utcnow() + timedelta(days=3))
        db.session.add_all([maint1, maint2, maint3, maint4, maint5])
        db.session.flush()
        
        # Work Orders
        wo1 = WorkOrder(equipment_id=equip3.equipment_id, title='Elliptical Making Noise', description='Grinding noise from flywheel area', type='corrective', status='in_progress', priority='high', assigned_to=tech1.user_id, created_by=manager.user_id, started_at=datetime.utcnow() - timedelta(hours=2))
        wo1.work_order_number = 'WO-20241202-0001'
        wo2 = WorkOrder(equipment_id=equip1.equipment_id, title='Monthly Belt Service', description='Regular monthly belt inspection and lubrication', type='preventive', status='open', priority='medium', assigned_to=tech1.user_id, created_by=admin.user_id, scheduled_date=datetime.utcnow().date() + timedelta(days=3))
        wo2.work_order_number = 'WO-20241202-0002'
        wo3 = WorkOrder(equipment_id=equip4.equipment_id, title='Cable Replacement', description='Replace worn cable on left side', type='corrective', status='open', priority='high', created_by=manager.user_id)
        wo3.work_order_number = 'WO-20241202-0003'
        wo4 = WorkOrder(equipment_id=equip2.equipment_id, title='Belt Replacement', description='Replaced worn drive belt', type='corrective', status='completed', priority='medium', assigned_to=tech2.user_id, created_by=manager.user_id, completed_at=datetime.utcnow() - timedelta(days=5), labor_hours=1.5, labor_cost=75.00)
        wo4.work_order_number = 'WO-20241127-0001'
        db.session.add_all([wo1, wo2, wo3, wo4])
        db.session.commit()
        print('All demo data seeded successfully!')
    else:
        print('Demo data already exists.')
EOF

echo "Build completed!"