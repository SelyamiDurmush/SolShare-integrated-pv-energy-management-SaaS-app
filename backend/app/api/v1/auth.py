from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.models.user import User
from app.schemas.user_schema import Token, ForgotPasswordRequest, Msg, ResetPasswordRequest
from app.services.email import send_password_reset_email

# router is used to group related endpoints and tags is used to group endpoints in the documentation
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password", response_model=Msg)
# Depends() is used to inject the database session into the endpoint
async def forgot_password(request: ForgotPasswordRequest, http_request: Request, db: Session = Depends(get_db)): 
    user = db.query(User).filter(User.email == request.email).first()
    if user and user.is_active:
        user.reset_token = secrets.token_urlsafe(32) # Generates a random URL-safe text string
        user.reset_token_expires = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
        db.commit()
        db.refresh(user)
        # Call the email service
        send_password_reset_email(to_email=user.email, token=user.reset_token, full_name=user.full_name)
    return {"message": f"If your email exists in our system, a password reset link has been sent to your email"}


@router.post("/reset-password", response_model=Msg)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == request.token).first()
    if  user and user.reset_token_expires > datetime.utcnow(): 
        user.hashed_password = get_password_hash(request.new_password) # Hashes the new password
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        db.refresh(user) # Updates the user object with the latest data from the database
        return {"message": "Password reset successful"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
            headers={"WWW-Authenticate": "Bearer"},
        )
