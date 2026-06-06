"""
Bərəkətli Telegram Bot — Main File
====================================

Run with: python bot.py

What this bot does (the flow):
1. Customer sends /start → welcome message
2. Shows menu as buttons
3. Customer taps product → shows farmer photo + story → asks quantity
4. Customer picks quantity → added to cart → back to menu
5. Loop until customer taps "Sifarişi tamamla"
6. Shows cart summary with totals
7. Customer confirms / edits / cancels
8. Asks for contact (name + phone)
9. Asks for delivery location (Google Maps pin)
10. Saves to Google Sheet + notifies admin + sends customer confirmation
"""

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from menu import (
    PRODUCTS,
    FARMERS,
    MINIMUM_ORDER_AZN,
    DELIVERY_DAY_AZ,
    DELIVERY_TIME_AZ,
    BANK_INFO_AZ,
    get_active_products,
    format_price,
)

# ============================================================
# SETUP
# ============================================================

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================================
# CONVERSATION STATES
# ============================================================
# Each state is a "step" in the conversation.
# The bot remembers which step each user is on.

(
    BROWSING_MENU,       # showing main menu, waiting for product choice
    CHOOSING_QUANTITY,   # showed product, waiting for quantity
    REVIEWING_CART,      # showing cart summary, waiting for confirm/edit/cancel
    AWAITING_CONTACT,    # waiting for customer to share contact
    AWAITING_LOCATION,   # waiting for Google Maps location
) = range(5)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_or_create_cart(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Get the user's cart from their personal session storage, or create empty one."""
    if "cart" not in context.user_data:
        context.user_data["cart"] = {}  # {product_id: quantity}
    return context.user_data["cart"]


def calculate_cart_total(cart: dict) -> float:
    """Sum up all items in cart × their prices."""
    total = 0.0
    for product_id, quantity in cart.items():
        if product_id in PRODUCTS:
            total += PRODUCTS[product_id]["price"] * quantity
    return total


def format_cart_summary(cart: dict) -> str:
    """Return a nicely formatted string showing all items in cart."""
    if not cart:
        return "Səbətiniz boşdur."

    lines = []
    for product_id, quantity in cart.items():
        product = PRODUCTS[product_id]
        line_total = product["price"] * quantity
        # Format quantity nicely: 1.0 -> "1", 0.5 -> "0.5"
        qty_str = f"{quantity:g}"
        lines.append(
            f"{product['emoji']} {product['name_az']}: "
            f"{qty_str} {product['unit_label_az']} × {format_price(product['price'])} "
            f"= {format_price(line_total)}"
        )
    total = calculate_cart_total(cart)
    lines.append(f"\n💰 Cəmi: {format_price(total)}")
    return "\n".join(lines)


def build_menu_keyboard(cart: dict) -> InlineKeyboardMarkup:
    """Build the main menu as inline buttons (2 products per row)."""
    products = get_active_products()
    buttons = []
    row = []
    for pid, p in products.items():
        # Show ✓ next to products already in cart
        in_cart = " ✓" if pid in cart else ""
        label = f"{p['emoji']} {p['name_az']}{in_cart}"
        row.append(InlineKeyboardButton(label, callback_data=f"product:{pid}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Bottom action buttons
    cart_total = calculate_cart_total(cart)
    if cart:
        buttons.append([
            InlineKeyboardButton(
                f"🛒 Səbət ({format_price(cart_total)})",
                callback_data="action:view_cart",
            )
        ])
        buttons.append([
            InlineKeyboardButton("✅ Sifarişi tamamla", callback_data="action:checkout")
        ])
    return InlineKeyboardMarkup(buttons)


def build_quantity_keyboard(product_id: str) -> InlineKeyboardMarkup:
    """Build quantity selection buttons for a product."""
    product = PRODUCTS[product_id]
    buttons = []
    row = []
    for qty in product["quantity_options"]:
        qty_str = f"{qty:g}"
        label = f"{qty_str} {product['unit_label_az']}"
        row.append(
            InlineKeyboardButton(label, callback_data=f"qty:{product_id}:{qty}")
        )
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton("⬅️ Geri", callback_data="action:back_to_menu")
    ])
    return InlineKeyboardMarkup(buttons)


def build_cart_review_keyboard() -> InlineKeyboardMarkup:
    """Buttons shown when reviewing the cart before checkout."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Təsdiq edirəm", callback_data="action:confirm_order")],
        [InlineKeyboardButton("✏️ Düzəliş et", callback_data="action:back_to_menu")],
        [InlineKeyboardButton("❌ Sifarişi ləğv et", callback_data="action:cancel_order")],
    ])


# ============================================================
# HANDLERS — these run when customer takes specific actions
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Triggered when customer sends /start or just says hi."""
    user = update.effective_user
    logger.info(f"New session: {user.id} ({user.first_name})")

    # Reset cart for fresh session
    context.user_data["cart"] = {}

    welcome = (
        f"Salam, {user.first_name}! 🌿\n\n"
        f"*Bərəkətli*-yə xoş gəlmisiniz — Lənkərandan kənd məhsulları, "
        f"birbaşa sizə.\n\n"
        f"🚚 Çatdırılma: hər {DELIVERY_DAY_AZ} ({DELIVERY_TIME_AZ})\n"
        f"📋 Sifariş son tarixi: hər Çərşənbə axşamı 18:00\n"
        f"💰 Minimum sifariş: {format_price(MINIMUM_ORDER_AZN)}\n\n"
        f"Aşağıdakı menyudan məhsul seçin 👇"
    )

    cart = get_or_create_cart(context)
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=build_menu_keyboard(cart),
    )
    return BROWSING_MENU


async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Customer tapped a product button → show farmer + ask quantity."""
    query = update.callback_query
    await query.answer()

    product_id = query.data.split(":")[1]
    product = PRODUCTS[product_id]
    farmer = FARMERS[product["farmer_id"]]

    # Store which product we're configuring (in case customer goes back)
    context.user_data["current_product"] = product_id

    caption = (
        f"{product['emoji']} *{product['name_az']}* — "
        f"{format_price(product['price'])}/{product['unit_label_az']}\n\n"
        f"👩‍🌾 *Tanış olun: {farmer['name']}*\n"
        f"📍 {farmer['village']}\n\n"
        f"_{farmer['story']}_"
    )

    # Build the photo carousel: main photo first (with caption), then farm photos
    from telegram import InputMediaPhoto

    photo_ids = []
    if farmer["main_photo_id"]:
        photo_ids.append(farmer["main_photo_id"])
    photo_ids.extend(farmer["farm_photo_ids"])
    photo_ids = photo_ids[:10]  # Telegram allows max 10 in a media group

    if len(photo_ids) >= 2:
        # Send swipeable carousel — caption on the FIRST photo only
        media = [
            InputMediaPhoto(
                pid,
                caption=caption if i == 0 else None,
                parse_mode="Markdown" if i == 0 else None,
            )
            for i, pid in enumerate(photo_ids)
        ]
        await query.message.reply_media_group(media=media)
        # Quantity buttons in a follow-up message
        await query.message.reply_text(
            f"Neçə {product['unit_label_az']} istəyirsiniz?",
            reply_markup=build_quantity_keyboard(product_id),
        )
    elif len(photo_ids) == 1:
        # Single photo — caption + buttons together
        await query.message.reply_photo(
            photo=photo_ids[0],
            caption=caption + f"\n\nNeçə {product['unit_label_az']} istəyirsiniz?",
            parse_mode="Markdown",
            reply_markup=build_quantity_keyboard(product_id),
        )
    else:
        # No photos yet — text-only fallback
        await query.message.reply_text(
            caption + f"\n\nNeçə {product['unit_label_az']} istəyirsiniz?",
            parse_mode="Markdown",
            reply_markup=build_quantity_keyboard(product_id),
        )

    return CHOOSING_QUANTITY


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Customer picked a quantity → add to cart → return to menu."""
    query = update.callback_query
    await query.answer()

    # callback_data format: "qty:product_id:quantity"
    parts = query.data.split(":")
    product_id = parts[1]
    quantity = float(parts[2])

    cart = get_or_create_cart(context)
    # If product already in cart, replace (could also add — but replace is clearer)
    cart[product_id] = quantity

    product = PRODUCTS[product_id]
    line_total = product["price"] * quantity
    cart_total = calculate_cart_total(cart)

    confirmation = (
        f"✅ Səbətə əlavə edildi:\n"
        f"{product['emoji']} {product['name_az']}: "
        f"{quantity:g} {product['unit_label_az']} = {format_price(line_total)}\n\n"
        f"🛒 Səbət cəmi: {format_price(cart_total)}\n\n"
        f"Daha nə istəyirsiniz?"
    )

    await query.message.reply_text(
        confirmation,
        reply_markup=build_menu_keyboard(cart),
    )
    return BROWSING_MENU


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show menu again (from Back button or after Edit)."""
    query = update.callback_query
    await query.answer()

    cart = get_or_create_cart(context)
    text = "📋 Menyu:"
    if cart:
        text = f"📋 Menyu:\n\n🛒 Səbətdə: {format_price(calculate_cart_total(cart))}"

    await query.message.reply_text(
        text,
        reply_markup=build_menu_keyboard(cart),
    )
    return BROWSING_MENU


async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Customer tapped 🛒 Səbət — show cart contents."""
    query = update.callback_query
    await query.answer()

    cart = get_or_create_cart(context)
    summary = format_cart_summary(cart)

    await query.message.reply_text(
        f"🛒 *Səbətiniz:*\n\n{summary}",
        parse_mode="Markdown",
        reply_markup=build_menu_keyboard(cart),
    )
    return BROWSING_MENU


async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Customer tapped 'Sifarişi tamamla' — show summary, ask to confirm."""
    query = update.callback_query
    await query.answer()

    cart = get_or_create_cart(context)
    total = calculate_cart_total(cart)

    if not cart:
        await query.message.reply_text(
            "Səbətiniz boşdur. Əvvəlcə məhsul seçin 🙂",
            reply_markup=build_menu_keyboard(cart),
        )
        return BROWSING_MENU

    if total < MINIMUM_ORDER_AZN:
        needed = MINIMUM_ORDER_AZN - total
        await query.message.reply_text(
            f"Minimum sifariş məbləği {format_price(MINIMUM_ORDER_AZN)}.\n"
            f"Sizdə hələ {format_price(needed)} çatmır.\n\n"
            f"Zəhmət olmasa daha bir neçə məhsul əlavə edin 🙏",
            reply_markup=build_menu_keyboard(cart),
        )
        return BROWSING_MENU

    summary = format_cart_summary(cart)
    await query.message.reply_text(
        f"📝 *Sifarişinizin xülasəsi:*\n\n{summary}\n\n"
        f"Hər şey doğrudur?",
        parse_mode="Markdown",
        reply_markup=build_cart_review_keyboard(),
    )
    return REVIEWING_CART


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Customer tapped 'Ləğv et' — clear cart, end conversation."""
    query = update.callback_query
    await query.answer()

    context.user_data["cart"] = {}
    await query.message.reply_text(
        "Sifarişiniz ləğv edildi. Yenidən başlamaq üçün /start yazın 👋"
    )
    return ConversationHandler.END


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Customer confirmed cart — now collect contact info."""
    query = update.callback_query
    await query.answer()

    # Calculate next Saturday for delivery date
    today = datetime.now()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:  # if today is Saturday, next one
        days_until_saturday = 7
    delivery_date = today + timedelta(days=days_until_saturday)
    context.user_data["delivery_date"] = delivery_date.strftime("%d.%m.%Y")

    await query.message.reply_text(
        f"🎉 Çox sayğı! Sifarişinizi qeyd edirəm.\n\n"
        f"🚚 Çatdırılma: *{DELIVERY_DAY_AZ}, "
        f"{context.user_data['delivery_date']}* ({DELIVERY_TIME_AZ})\n\n"
        f"İndi əlaqə məlumatlarınızı paylaşın — adınız və telefon nömrəniz üçün "
        f"aşağıdakı düyməyə basın 👇",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Əlaqə məlumatımı paylaş", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return AWAITING_CONTACT


async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Customer shared contact — save it, ask for location."""
    contact = update.message.contact
    context.user_data["contact"] = {
        "name": f"{contact.first_name or ''} {contact.last_name or ''}".strip(),
        "phone": contact.phone_number,
    }

    await update.message.reply_text(
        f"Təşəkkürlər, {context.user_data['contact']['name']}! ✅\n\n"
        f"Son bir addım: çatdırılma ünvanınızı *Google Maps lokasiyası* "
        f"olaraq paylaşın 📍\n\n"
        f"_(Telegram-da əlavə düyməsi → Lokasiya → Bu mövqeyi göndər)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Cari lokasiyamı paylaş", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return AWAITING_LOCATION


async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Customer shared location — finalize order, save everywhere, notify admin."""
    location = update.message.location
    context.user_data["location"] = {
        "lat": location.latitude,
        "lng": location.longitude,
        "maps_link": f"https://maps.google.com/?q={location.latitude},{location.longitude}",
    }

    # Build the complete order record
    cart = get_or_create_cart(context)
    contact = context.user_data["contact"]
    loc = context.user_data["location"]
    order_id = f"BRK-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{update.effective_user.id}"
    total = calculate_cart_total(cart)

    # Build the order record (shape matches sheets.save_order_to_sheet)
    order_record = {
        "order_id": order_id,
        "timestamp": datetime.now().isoformat(),
        "customer_name": contact["name"],
        "customer_phone": contact["phone"],
        "telegram_user_id": update.effective_user.id,
        "telegram_username": update.effective_user.username or "",
        "delivery_date": context.user_data["delivery_date"],
        "items": cart.copy(),
        "total_azn": total,
        "location_lat": loc["lat"],
        "location_lng": loc["lng"],
        "maps_link": loc["maps_link"],
    }

    # Save to Google Sheets via webhook
    try:
        from sheets import save_order_to_sheet
        save_order_to_sheet(order_record)
        logger.info(f"Order {order_id} saved to Google Sheets")
    except ValueError as e:
        logger.warning(f"Google Sheets not configured: {e}")
    except Exception as e:
        logger.error(f"Failed to save to Google Sheets: {e}")
        # Don't fail the order — admin will get notification anyway

    # Notify admin
    if ADMIN_CHAT_ID:
        try:
            admin_msg = (
                f"🆕 *YENİ SİFARİŞ*\n\n"
                f"📦 ID: `{order_id}`\n"
                f"👤 {contact['name']}\n"
                f"📞 {contact['phone']}\n"
                f"📅 Çatdırılma: {context.user_data['delivery_date']}\n\n"
                f"{format_cart_summary(cart)}\n\n"
                f"📍 [Lokasiya]({loc['maps_link']})"
            )
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_msg,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

    # Confirm to customer
    confirmation = (
        f"🎉 *Sifarişiniz qəbul edildi!*\n\n"
        f"📦 Sifariş №: `{order_id}`\n"
        f"💰 Cəmi: {format_price(total)}\n"
        f"🚚 Çatdırılma: {DELIVERY_DAY_AZ}, "
        f"{context.user_data['delivery_date']} ({DELIVERY_TIME_AZ})\n\n"
        f"{BANK_INFO_AZ}\n\n"
        f"Hər hansı sual üçün buradan yaza bilərsiniz. Sağ olun! 🌿"
    )
    await update.message.reply_text(
        confirmation,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Clear session for next order
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User typed /cancel anywhere — exit conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "Sifariş prosesi dayandırıldı. Yenidən başlamaq üçün /start yazın.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ============================================================
# HEALTH-CHECK SERVER (for Render free web service)
# ============================================================
# Render's free tier runs "web services" (not "workers") for free.
# A web service must listen on a port. This tiny server does that —
# it just replies "alive" to any visit. The bot keeps polling as normal.
# This does NOT change any bot behavior; it's purely a "doorbell".

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Replies 'alive' to any HTTP request so Render sees a web service."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Bərəkətli bot alive 🌿".encode("utf-8"))

    def log_message(self, format, *args):
        # Silence the default noisy request logging
        return


def start_health_server():
    """Start the health-check server on the port Render provides."""
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"Health-check server listening on port {port}")
    server.serve_forever()


# ============================================================
# MAIN — wire it all up
# ============================================================

def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print("❌ ERROR: Set your BOT_TOKEN in the .env file first!")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler defines the full flow
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r"(?i)^(salam|hi|hello|hey)"), start),
        ],
        states={
            BROWSING_MENU: [
                CallbackQueryHandler(show_product, pattern=r"^product:"),
                CallbackQueryHandler(view_cart, pattern=r"^action:view_cart$"),
                CallbackQueryHandler(checkout, pattern=r"^action:checkout$"),
            ],
            CHOOSING_QUANTITY: [
                CallbackQueryHandler(add_to_cart, pattern=r"^qty:"),
                CallbackQueryHandler(back_to_menu, pattern=r"^action:back_to_menu$"),
            ],
            REVIEWING_CART: [
                CallbackQueryHandler(confirm_order, pattern=r"^action:confirm_order$"),
                CallbackQueryHandler(back_to_menu, pattern=r"^action:back_to_menu$"),
                CallbackQueryHandler(cancel_order, pattern=r"^action:cancel_order$"),
            ],
            AWAITING_CONTACT: [
                MessageHandler(filters.CONTACT, receive_contact),
            ],
            AWAITING_LOCATION: [
                MessageHandler(filters.LOCATION, receive_location),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        per_message=False,
    )

    application.add_handler(conv_handler)

    # Start health-check server in background (for Render free web service)
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    print("🤖 Bərəkətli bot işə düşdü. Dayandırmaq üçün Ctrl+C basın.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    # Ensure an event loop exists in the main thread.
    # Newer Python versions (3.12+) no longer auto-create one, which can
    # cause "no current event loop" errors with some library versions.
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    main()
