from typing import Union

from sqlalchemy.orm import Mapped, mapped_column

from src.db.db import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str]
    is_bot: Mapped[bool]
    first_name: Mapped[str]
    last_name: Mapped[Union[str, None]] = None
    language_code: Mapped[Union[str, None]] = None
    username: Mapped[Union[str, None]] = None
    is_premium: Mapped[Union[str, None]] = None
    is_blocked: Mapped[bool] = mapped_column(default=False)
