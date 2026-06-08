from apps.agent_engine.generic.config import ExtractorConfig

EXTRACTOR_CONFIG = ExtractorConfig(
    intent_keywords={
        "order_status": ["order status", "where is my order", "tracking", "shipment", "delivery"],
        "refund_request": ["refund", "money back", "return money"],
        "exchange_request": ["exchange", "swap", "replace item"],
        "product_question": ["product", "specification", "size", "color", "stock"],
        "complaint": ["complaint", "angry", "terrible", "worst", "damaged"],
    },
    need_keywords={
        "electronics": "Electronics product",
        "clothing": "Clothing product",
        "furniture": "Furniture product",
    },
)
