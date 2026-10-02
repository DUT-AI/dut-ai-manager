from pathlib import Path
from app.core.config import settings


def get_asset_url(asset_name: str | None) -> str | None:
    """
    Sinh URL công khai tuyệt đối cho một file asset tĩnh nằm trong backend/app/assets.
    
    Args:
        asset_name: Tên file (ví dụ: 'meme-hoc-bai.webp')
        
    Returns:
        URL tuyệt đối (ví dụ: 'http://localhost:8000/static/assets/meme-hoc-bai.webp') hoặc None nếu không tồn tại.
    """
    if not asset_name:
        return None

    # Kiểm tra file có thực sự nằm trong assets không
    assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"
    asset_file = assets_dir / asset_name
    if not asset_file.is_file():
        return None

    base_url = settings.BACKEND_PUBLIC_URL.rstrip("/")
    return f"{base_url}/static/assets/{asset_name}"


def get_asset_path(asset_name: str | None) -> Path | None:
    """
    Trả về đường dẫn tệp Path tuyệt đối trên disk cho file asset nếu tồn tại.
    """
    if not asset_name:
        return None
    assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"
    asset_file = assets_dir / asset_name
    if asset_file.is_file():
        return asset_file
    return None
