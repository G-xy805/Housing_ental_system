from app import create_app, db

app = create_app()
with app.app_context():
    result = db.session.execute(db.text('PRAGMA table_info(landlords)')).fetchall()
    print("landlords columns:", [row[1] for row in result])
    
    result = db.session.execute(db.text('PRAGMA table_info(tenants)')).fetchall()
    print("tenants columns:", [row[1] for row in result])
