import os
from app import create_app, db
from app.models import User, Location, EquipmentCategory

app = create_app(os.environ.get('FLASK_ENV', 'production'))


@app.cli.command('init-db')
def init_db():
    """Initialize the database with tables."""
    db.create_all()
    print('Database tables created.')


@app.cli.command('seed-demo')
def seed_demo():
    """Seed the database with demo data for grading."""
    # Check if already seeded
    if User.query.filter_by(username='admin').first():
        print('Demo data already exists.')
        return
    
    # Create locations
    locations = [
        Location(name='Main Gym Downtown', address='123 Fitness Ave', city='Boston', state='MA', postal_code='02101', phone='617-555-0100'),
        Location(name='West Side Fitness', address='456 Wellness Blvd', city='Boston', state='MA', postal_code='02134', phone='617-555-0200'),
        Location(name='Campus Recreation Center', address='789 University Dr', city='Cambridge', state='MA', postal_code='02139', phone='617-555-0300'),
    ]
    db.session.add_all(locations)
    db.session.flush()
    
    # Create categories
    categories = [
        EquipmentCategory(name='Cardio', description='Treadmills, ellipticals, bikes'),
        EquipmentCategory(name='Strength Machines', description='Cable machines, leg press'),
        EquipmentCategory(name='Free Weights', description='Dumbbells, barbells, plates'),
        EquipmentCategory(name='Benches & Racks', description='Benches, power racks'),
        EquipmentCategory(name='Functional Training', description='Kettlebells, battle ropes'),
        EquipmentCategory(name='Stretching & Recovery', description='Foam rollers, mats'),
    ]
    db.session.add_all(categories)
    
    # Create users
    admin = User(
        username='admin',
        email='admin@gymequip.com',
        first_name='System',
        last_name='Administrator',
        role='admin',
        location_id=locations[0].location_id
    )
    admin.set_password('admin123')
    
    manager = User(
        username='manager',
        email='manager@gymequip.com',
        first_name='Mike',
        last_name='Manager',
        role='manager',
        location_id=locations[0].location_id
    )
    manager.set_password('manager123')
    
    tech1 = User(
        username='tech1',
        email='tech1@gymequip.com',
        first_name='Tom',
        last_name='Technician',
        role='technician',
        location_id=locations[0].location_id
    )
    tech1.set_password('tech123')
    
    tech2 = User(
        username='tech2',
        email='tech2@gymequip.com',
        first_name='Sarah',
        last_name='Smith',
        role='technician',
        location_id=locations[1].location_id
    )
    tech2.set_password('tech123')
    
    db.session.add_all([admin, manager, tech1, tech2])
    db.session.commit()
    
    print('Demo data seeded successfully!')
    print('\nTest Accounts:')
    print('  Admin:     admin / admin123')
    print('  Manager:   manager / manager123')
    print('  Technician: tech1 / tech123')
    print('  Technician: tech2 / tech123')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
