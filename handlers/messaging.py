from aiogram.types import LinkPreviewOptions

# Сообщения с ссылками на Tonviewer — только текст, без превью в Telegram
HIDE_LINK_PREVIEW = LinkPreviewOptions(is_disabled=True)
