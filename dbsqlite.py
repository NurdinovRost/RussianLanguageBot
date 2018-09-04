from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Words(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True)
    word = Column(String)
    transcription = Column(String)
    example = Column(String)
    audio = Column(String)
    image = Column(String)
    type_word = Column(String)
    level = Column(Integer)
    translate_eng = Column(String)
    example_eng = Column(String)
    translate_pers = Column(String)
    example_pers = Column(String)


engine = create_engine("sqlite:///words.db", connect_args={'check_same_thread': False})
Base.metadata.create_all(bind=engine)

session = sessionmaker(bind=engine)
s = session()




