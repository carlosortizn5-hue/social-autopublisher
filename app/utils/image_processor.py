import io
import logging
import httpx
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from app.models import Product

logger = logging.getLogger(__name__)

CANVAS_SIZE = (1080, 1080)
BADGE_COLOR = (230, 0, 35, 220)       # #E60023 with alpha
PRICE_BAR_COLOR = (0, 0, 0, 180)      # semi-transparent dark
FOOTER_COLOR = (0, 0, 0, 200)
WHITE = (255, 255, 255, 255)
GRAY_BG = (245, 245, 245)


def download_image(image_url: str) -> Optional[bytes]:
    """Download an image from a URL and return raw bytes, or None on error."""
    if not image_url:
        return None
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(image_url)
            response.raise_for_status()
            return response.content
    except Exception as e:
        logger.warning(f"Failed to download image from {image_url}: {e}")
        return None


def _load_font(size: int) -> ImageFont.ImageFont:
    """Load a built-in Pillow font at the requested size (best-effort)."""
    try:
        # Pillow 10+ ships FreeType fonts
        return ImageFont.load_default(size=size)
    except TypeError:
        # Pillow < 10 load_default() takes no args
        return ImageFont.load_default()


def _center_text(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.ImageFont, fill: tuple) -> None:
    """Draw text centered horizontally at given y position."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x = (CANVAS_SIZE[0] - text_w) // 2
    draw.text((x, y), text, font=font, fill=fill)


def add_overlay(image_bytes: bytes, product: Product) -> Optional[bytes]:
    """
    Composite the product image onto a 1080x1080 canvas and add:
      - "OFERTA" badge (top-left, red)
      - Price bar (bottom, semi-transparent dark, white text)
      - Footer "MERCADOLIBRE" branding
    Returns JPEG bytes or None on error.
    """
    try:
        # --- Build canvas ---
        canvas = Image.new("RGB", CANVAS_SIZE, GRAY_BG)

        # --- Paste product image centered ---
        try:
            product_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        except Exception as e:
            logger.warning(f"Cannot open product image bytes: {e}")
            product_img = None

        if product_img:
            product_img.thumbnail((900, 900), Image.LANCZOS)
            paste_x = (CANVAS_SIZE[0] - product_img.width) // 2
            paste_y = (CANVAS_SIZE[1] - product_img.height) // 2
            # Use alpha channel as mask if present
            mask = product_img.split()[3] if product_img.mode == "RGBA" else None
            canvas.paste(product_img.convert("RGB"), (paste_x, paste_y), mask)

        # --- Build overlay layer (RGBA) ---
        overlay = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # --- OFERTA badge (top-left) ---
        badge_font = _load_font(40)
        badge_text = "OFERTA"
        badge_padding = 14
        # Measure text
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        badge_w = text_w + badge_padding * 2
        badge_h = text_h + badge_padding * 2
        badge_x, badge_y = 30, 30
        draw.rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            fill=BADGE_COLOR,
        )
        draw.text(
            (badge_x + badge_padding, badge_y + badge_padding),
            badge_text,
            font=badge_font,
            fill=WHITE,
        )

        # --- Price bar (bottom 160px) ---
        bar_top = CANVAS_SIZE[1] - 160
        draw.rectangle([0, bar_top, CANVAS_SIZE[0], CANVAS_SIZE[1] - 50], fill=PRICE_BAR_COLOR)

        price_font = _load_font(54)
        title_font = _load_font(30)

        # Price text
        if product.price:
            price_str = f"$ {product.price:,.0f}"
        else:
            price_str = "Ver precio"

        _center_text(draw, price_str, bar_top + 14, price_font, WHITE)

        # Title (truncated)
        title = (product.title[:52] + "…") if product.title and len(product.title) > 52 else (product.title or "")
        _center_text(draw, title, bar_top + 78, title_font, WHITE)

        # --- Footer "MERCADOLIBRE" branding ---
        footer_font = _load_font(28)
        footer_text = "mercadolibre.com"
        draw.rectangle([0, CANVAS_SIZE[1] - 50, CANVAS_SIZE[0], CANVAS_SIZE[1]], fill=FOOTER_COLOR)
        _center_text(draw, footer_text, CANVAS_SIZE[1] - 40, footer_font, WHITE)

        # --- Composite overlay onto canvas ---
        canvas_rgba = canvas.convert("RGBA")
        canvas_rgba = Image.alpha_composite(canvas_rgba, overlay)
        final = canvas_rgba.convert("RGB")

        # --- Encode as JPEG ---
        buffer = io.BytesIO()
        final.save(buffer, format="JPEG", quality=88, optimize=True)
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"add_overlay failed: {e}", exc_info=True)
        return None


def enhance_product_image(product: Product) -> Optional[bytes]:
    """
    Orchestrator: downloads the product image and applies the overlay.
    Returns JPEG bytes (1080x1080) or None if anything fails.
    """
    raw_bytes = download_image(product.image_url) if product.image_url else None

    result = add_overlay(raw_bytes or b"", product)
    if result is None:
        logger.warning(f"enhance_product_image returned None for product id={product.id}")
    return result
