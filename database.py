import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

PATH = os.path.dirname(__file__)

DATABASE_URL = f"sqlite:///{PATH}/snkrs.db"
print("DATABASE_URL: ", DATABASE_URL)

# DATABASE_URL = "sqlite://"

engine = create_engine(DATABASE_URL, echo=False, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session():
    return SessionLocal()
