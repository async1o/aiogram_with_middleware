from typing import Dict, List, TypedDict

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.utils.config import settings
from sqlalchemy import select
from src.db.db import async_session_maker
from src.models.users import UserModel


class Product(TypedDict):
    id: int
    title: str
    price: int


PRODUCTS: List[Product] = [
    {"id": 1, "title": "T‑Shirt", "price": 1999},
    {"id": 2, "title": "Mug", "price": 1299},
    {"id": 3, "title": "Sticker Pack", "price": 499},
]


_user_carts: Dict[int, Dict[int, int]] = {}


def get_product_by_id(product_id: int) -> Product | None:
    for product in PRODUCTS:
        if product["id"] == product_id:
            return product
    return None


def add_to_cart(user_id: int, product_id: int, qty: int = 1) -> None:
    cart = _user_carts.setdefault(user_id, {})
    cart[product_id] = cart.get(product_id, 0) + max(1, qty)


def get_cart(user_id: int) -> Dict[int, int]:
    return _user_carts.get(user_id, {})


def clear_cart(user_id: int) -> None:
    _user_carts.pop(user_id, None)


def format_price_minor(price_minor: int) -> str:
    return f"{price_minor / 100:.2f}"


router = Router(name="user_messages")


def _is_admin_local(user_id: int) -> bool:
    return user_id in set(settings.ADMIN_IDS or [])


async def _db_is_admin(user_id: int) -> bool:
    async with async_session_maker() as session:
        q = select(UserModel.is_admin).where(UserModel.user_id == str(user_id))
        res = await session.execute(q)
        row = res.first()
    return bool(row and row[0])


def build_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📦 Каталог"), KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="ℹ️ Помощь")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="🛠 Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message):
    #is_admin = _is_admin_local(message.from_user.id) or await _db_is_admin(message.from_user.id)
    await message.answer(
        "Добро пожаловать! Выберите действие через меню ниже.",
        reply_markup=build_main_menu()
    )


@router.message(Command("help"))
@router.message(F.text.in_({"help", "/help", "ℹ️ Помощь"}))
async def cmd_help(message: Message):
    await message.answer(
        "Помощь:\n"
        "— Нажмите ‘📦 Каталог’, чтобы просмотреть товары.\n"
        "— Нажмите ‘🛒 Корзина’, чтобы увидеть выбранные товары.\n"
        "— Администраторы могут открыть ‘🛠 Админ-панель’."
    )


@router.message(F.text.in_({"📦 Каталог"}))
async def cmd_catalog(message: Message):
    kb = InlineKeyboardBuilder()
    for p in PRODUCTS:
        kb.button(text=f"{p['title']} — {format_price_minor(p['price'])} ₽", callback_data=f"product:{p['id']}")
    kb.adjust(1)
    await message.answer("Каталог товаров:", reply_markup=kb.as_markup())


@router.message(F.text.in_({"🛒 Корзина"}))
async def cmd_cart(message: Message):
    cart = get_cart(message.from_user.id)
    if not cart:
        await message.answer("Ваша корзина пуста. Нажмите ‘📦 Каталог’, чтобы выбрать товары.")
        return

    lines = ["Корзина:"]
    total = 0
    for product_id, qty in cart.items():
        product = get_product_by_id(product_id)
        if not product:
            continue
        line_sum = product["price"] * qty
        total += line_sum
        lines.append(f"- {product['title']} x{qty} — {format_price_minor(line_sum)} ₽")

    lines.append(f"Итого: {format_price_minor(total)} ₽")
    await message.answer("\n".join(lines))

