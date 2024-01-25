from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

# Создание таблиц, если они еще не были созданы
Base = declarative_base()
Base.metadata.create_all(bind=engine)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()
