from sqlalchemy import Column, Integer, String
from db import Base


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=True)
    album = Column(String(255), nullable=True)
    path = Column(String(1024), unique=True, nullable=False)
    duration = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<Track id={self.id} title={self.title!r} path={self.path!r}>"
