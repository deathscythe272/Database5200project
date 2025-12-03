# Gym Equipment Management System

A web-based application for managing gym equipment lifecycle, maintenance schedules, repair parts inventory, and service history.

## CS5200 Database Theory and Application - Course Project

### Features

- **Equipment Management**: Track all gym equipment with details like serial numbers, purchase dates, warranty status, and usage hours
- **Work Order System**: Create, assign, and track preventive, corrective, and emergency maintenance work orders
- **Maintenance Scheduling**: Set up recurring maintenance schedules based on time or usage hours
- **Parts Inventory**: Manage parts stock levels, track usage, receive shipments, and get low-stock alerts
- **User Roles**: Admin, Manager, and Technician roles with appropriate access controls
- **Dashboard**: At-a-glance view of equipment status, pending work, overdue maintenance, and inventory alerts

### Test Accounts

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Manager | manager | manager123 |
| Technician | tech1 | tech123 |
| Technician | tech2 | tech123 |

### Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login + bcrypt
- **Frontend**: Jinja2 templates + Bootstrap 5
- **Deployment**: Render.com

### Database Features

- 13 interconnected tables with proper relationships
- Optimistic locking (version columns) for concurrent access
- Automatic work order number generation
- Audit trail for inventory changes
- Triggers for timestamp updates and maintenance scheduling

### Local Development

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set environment variables:
   ```bash
   export DATABASE_URL=postgresql://localhost/gym_equipment
   export SECRET_KEY=dev-secret-key
   export FLASK_ENV=development
   ```
5. Initialize database:
   ```bash
   flask init-db
   flask seed-demo
   ```
6. Run the application:
   ```bash
   flask run
   ```

### Deployment to Render.com

1. Push code to GitHub
2. Create new Web Service on Render.com
3. Connect to GitHub repository
4. Render will auto-detect settings from `render.yaml`
5. Database and web service will be created automatically

### API Endpoints

The application includes REST API endpoints at `/api/`:

- `GET /api/equipment` - List equipment with filters
- `GET /api/equipment/<id>` - Get equipment details
- `POST /api/equipment` - Create equipment (manager+)
- `PUT /api/equipment/<id>` - Update equipment
- `GET /api/work-orders` - List work orders
- `POST /api/work-orders` - Create work order
- `PATCH /api/work-orders/<id>/status` - Update status
- `GET /api/inventory` - List inventory
- `POST /api/inventory/<id>/adjust` - Adjust inventory
- `GET /api/dashboard/stats` - Dashboard statistics

### Project Structure

```
gym_app/
├── app/
│   ├── __init__.py          # App factory
│   ├── models/
│   │   └── models.py        # SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py          # Authentication
│   │   ├── main.py          # Dashboard
│   │   ├── equipment.py     # Equipment CRUD
│   │   ├── work_orders.py   # Work order management
│   │   ├── inventory.py     # Parts inventory
│   │   ├── maintenance.py   # Maintenance schedules
│   │   └── api.py           # REST API
│   └── templates/           # Jinja2 templates
├── config.py                # Configuration
├── run.py                   # Entry point
├── requirements.txt         # Dependencies
├── render.yaml             # Render.com config
└── build.sh                # Build script
```

### Security Features

- Password hashing with bcrypt
- Session-based authentication
- Role-based access control
- CSRF protection via Flask-WTF
- Input validation
- SQL injection prevention via SQLAlchemy ORM

---

**Author**: Jeff  
**Course**: CS5200 Database Theory and Application  
**Semester**: Fall 2024
