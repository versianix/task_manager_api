from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLACHELMY_DATABASE_URL = "postgresql://marcelversiani:cecel@localhost:5432/case_mention"
engine = create_engine(SQLACHELMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()