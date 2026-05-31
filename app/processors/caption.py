from app.models import Product


def generate_caption(product: Product, platform: str) -> str:
    """Generate platform-specific caption for product"""

    base_caption = f"🛍️ {product.title}\n💰 ${product.price:.2f}" if product.price else f"🛍️ {product.title}"

    if platform == "twitter":
        # Twitter has 280 char limit
        return f"{base_caption}\n\n🔗 Link en bio" if len(base_caption) < 250 else base_caption[:260]

    elif platform == "facebook":
        return f"{base_caption}\n\n¡Disponible ahora! 🎉"

    elif platform == "instagram":
        return f"{base_caption}\n\n✨ Descubre más en nuestro link de bio\n\n#shopping #oferta"

    elif platform == "tiktok":
        return f"{base_caption}\n\n#shopping #tiktok #oferta"

    return base_caption
