from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class GenProcNews(Base):
    __tablename__ = 'genproc_news'
    
    id = Column(Integer, primary_key=True)
    last_title = Column(String(500))

class MVDNews(Base):
    __tablename__ = 'mvd_news'
    
    id = Column(Integer, primary_key=True)
    last_title = Column(String(500))

class YKLNews(Base):
    __tablename__ = 'ykl_news'
    
    id = Column(Integer, primary_key=True)
    last_title = Column(String(500))

# Create database engine
engine = create_engine('sqlite:///news.db')
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine) 