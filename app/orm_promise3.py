# app/orm_promise3.py
# case: create a new user in the database 
# 1. create a new user instance of the User class
# 2. get the database session/connection
# 3. issue commands to add the new user to the database



from app.database import Base, engine, get_session
from app.domain import User, Portfolio, Security, Investment, Transaction
from app.service import user_service
from app.domain import Security
from app.service import portfolio_service
from app.service import security_service


def main() -> None:
    # 1) Create all tables in the database (if they do not exist yet)
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    print("Tables created.")

    # 2) Insert a sample user (only if it does not already exist)
    sample_username = "admin"

    session = get_session()
    try:
        existing = session.get(User, sample_username)
        if existing is None:
            user = User(
                username=sample_username,
                password="adminpass",
                firstname="Admin",
                lastname="Admin",
                balance=0.0,
                role="admin",
            )
            session.add(user)
            session.commit()
            print("Sample user 'admin' created.")
        else:
            print("Sample user 'admin' already exists, skipping insert.")
            
    finally:
        session.close()


if __name__ == "__main__":
    main()
    
