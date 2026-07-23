from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    """
    Dependency that provides a database session.
    """
    with Session(engine) as session:
        yield session