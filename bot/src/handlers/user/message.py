from typing import Dict, List, TypedDict

from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder


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


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать!\n"
        "Доступные команды:\n"
        "- /catalog — каталог товаров\n"
        "- /cart — корзина"
    )


@router.message(F.text == "/catalog")
async def cmd_catalog(message: Message):
    kb = InlineKeyboardBuilder()
    for p in PRODUCTS:
        kb.button(text=f"{p['title']} — {format_price_minor(p['price'])} ₽", callback_data=f"product:{p['id']}")
    kb.adjust(1)
    await message.answer("Каталог товаров:", reply_markup=kb.as_markup())


@router.message(F.text == "/cart")
async def cmd_cart(message: Message):
    cart = get_cart(message.from_user.id)
    if not cart:
        await message.answer("Ваша корзина пуста. Откройте /catalog чтобы выбрать товары.")
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

