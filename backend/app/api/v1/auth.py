from fastapi import APIRouter, Depends

from app.core.security import AdminUser, get_current_admin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def me(admin: AdminUser = Depends(get_current_admin)):
    return {"id": admin.id, "email": admin.email, "role": admin.role}
