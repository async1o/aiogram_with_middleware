from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .message import (
    PRODUCTS,
    get_product_by_id,
    add_to_cart,
    format_price_minor,
)


router = Router(name="user_callbacks")


@router.callback_query(F.data.startswith("product:"))
async def on_product(call: CallbackQuery):
    try:
        product_id = int(call.data.split(":", 1)[1])
    except Exception:
        await call.answer("Некорректный товар", show_alert=True)
        return

    product = get_product_by_id(product_id)
    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить в корзину", callback_data=f"add:{product_id}")
    kb.button(text="Назад к каталогу", callback_data="back:catalog")
    kb.adjust(1)

    text = (
        f"<b>{product['title']}</b>\n"
        f"Цена: {format_price_minor(product['price'])} ₽"
    )

    try:
        await call.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await call.message.answer(text, reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(F.data == "back:catalog")
async def on_back_catalog(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    for p in PRODUCTS:
        kb.button(text=f"{p['title']} — {format_price_minor(p['price'])} ₽", callback_data=f"product:{p['id']}")
    kb.adjust(1)
    if getattr(call.message, "text", None):
        await call.message.edit_text("Каталог товаров:", reply_markup=kb.as_markup())
    else:
        await call.message.answer("Каталог товаров:", reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("add:"))
async def on_add_to_cart(call: CallbackQuery):
    try:
        product_id = int(call.data.split(":", 1)[1])
    except Exception:
        await call.answer("Ошибка добавления", show_alert=True)
        return

    product = get_product_by_id(product_id)
    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return

    add_to_cart(call.from_user.id, product_id, 1)
    await call.answer("Добавлено в корзину")

