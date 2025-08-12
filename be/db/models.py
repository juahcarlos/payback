from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    VARCHAR,
    BigInteger,
    Boolean,
    Column,
    Index,
    Integer,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Partners(Base):
    """
    Partners program allowing participants to earn commissions.
    """
    __tablename__ = "partners"

    id = Column(BigInteger, nullable=False, primary_key=True)
    created = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    password = Column(VARCHAR(100), default=None, nullable=True)
    commission = Column(BigInteger, default=None, nullable=True)
    description = Column(Text, default=None, nullable=True)
    lang = Column(VARCHAR(2), default="en", nullable=False)

    __table_args__ = (
        Index("id", "id", unique=True),
    )


class TariffsWh(Base):
    """
    The tariff table for frontend specific fields
    that all are text  (varchar) based on FE specific needs
    """
    __tablename__ = "tariffs_wh"

    id = Column(VARCHAR(10), nullable=True, primary_key=True)
    month = Column(VARCHAR(10), default=None, nullable=True)
    count = Column(VARCHAR(5), default=None, nullable=True)
    economy = Column(VARCHAR(5), default=None, nullable=True)
    popular = Column(VARCHAR(5), default=None, nullable=True)
    countTextSum = Column(VARCHAR(5), default=None, nullable=True)
    date = Column(VARCHAR(5), default=None, nullable=True)
    countText = Column(VARCHAR(5), default=None, nullable=True)
