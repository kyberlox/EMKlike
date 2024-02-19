from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import  Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

engine = create_engine("postgresql://emk_u:cdjkjxm@127.0.0.1:5432/emk")

Session = sessionmaker(autoflush=True, bind=engine)


class Base(DeclarativeBase): pass
  
class Activites(Base):
    __tablename__ = "activites"
  
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    coast = Column(Integer)
    user_uuid = Column(String)

    activeusers = relationship("ActiveUsers", back_populates="activites")
    

class ActiveUsers(Base):
    __tablename__ = "activeusers"
  
    id = Column(Integer, primary_key=True, index=True)
    uuid_from = Column(String)
    uuid_to = Column(String)
    description = Column(String)
    valid = Column(Integer)
    date_time = Column(DateTime)
    activitesId = Column(Integer, ForeignKey(Integer, back_populates="activites.id"))

    activites = relationship("Activites", back_populates="activeusers")



with Session(autoflush=False, bind=engine) as db:
    # получение всех объектов
    activites = db.query(Activites).all()
    for activity in activites:
        print(activity.id, activity)