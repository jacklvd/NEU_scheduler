import strawberry
from typing import Optional
from datetime import datetime
from app.services.auth import AuthService
from app.graphql.types.user import User, AuthResponse, VerifyOTPInput

@strawberry.type
class AuthMutation:
    @strawberry.mutation
    async def requestOtp(self, email: str, purpose: str) -> AuthResponse:
        """Request OTP for login or registration"""
        try:
            # Validate purpose
            if purpose not in ['login', 'register']:
                return AuthResponse(
                    success=False,
                    message="Invalid purpose. Must be 'login' or 'register'"
                )
            
            # For login, check if user exists
            if purpose == 'login':
                user = AuthService.get_user_by_email(email)
                if not user:
                    return AuthResponse(
                        success=False,
                        message="No account found with this email address"
                    )
            
            # For register, check if user already exists
            if purpose == 'register':
                user = AuthService.get_user_by_email(email)
                if user:
                    return AuthResponse(
                        success=False,
                        message="An account with this email already exists"
                    )
            
            # Send OTP - at this point we don't store any user data yet
            success = await AuthService.send_otp_email(email, purpose)
            
            if success:
                return AuthResponse(
                    success=True,
                    message=f"Verification code sent to {email}"
                )
            else:
                return AuthResponse(
                    success=False,
                    message="Failed to send verification code. Please try again."
                )
                
        except Exception as e:
            print(f"Error in request_otp: {e}")
            return AuthResponse(
                success=False,
                message="An unexpected error occurred"
            )
    
    @strawberry.mutation
    async def verifyOtp(self, input: VerifyOTPInput) -> AuthResponse:
        """Verify OTP and complete login/registration"""
        try:
            # Verify OTP
            is_valid = AuthService.verify_otp(input.email, input.code, input.purpose)
            
            if not is_valid:
                return AuthResponse(
                    success=False,
                    message="Invalid or expired verification code"
                )
            
            user_data = None
            
            # Handle registration
            if input.purpose == 'register':
                if not input.registerData:
                    return AuthResponse(
                        success=False,
                        message="Registration data is required for registration"
                    )
                
                # Only store user data after OTP verification has succeeded
                # This ensures we don't store users until they're verified
                try:
                    # Use camelCase fields from the input and convert to snake_case for the service
                    user_data = AuthService.create_user(
                        email=input.email,
                        first_name=input.registerData.firstName,
                        last_name=input.registerData.lastName,
                        student_id=input.registerData.studentId,
                        graduation_year=input.registerData.graduationYear,
                        major=input.registerData.major
                    )
                except Exception as create_error:
                    return AuthResponse(
                        success=False,
                        message=f"Error creating user: {str(create_error)}"
                    )
            
            # Handle login
            elif input.purpose == 'login':
                user_data = AuthService.get_user_by_email(input.email)
                if not user_data:
                    return AuthResponse(
                        success=False,
                        message="User not found"
                    )
            
            # Generate JWT token
            try:
                token_data = {
                    "user_id": user_data["id"],
                    "email": user_data["email"],
                    "purpose": input.purpose
                }
                token = AuthService.generate_jwt_token(token_data)
            except Exception as auth_error:
                return AuthResponse(
                    success=False,
                    message=f"Authentication error: {str(auth_error)}"
                )
            
            # Convert to GraphQL user type
            # Convert ISO string back to datetime object for GraphQL
            created_at_str = user_data["created_at"]
            created_at_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            
            graphql_user = User(
                id=user_data["id"],
                email=user_data["email"],
                firstName=user_data["first_name"],
                lastName=user_data["last_name"],
                studentId=user_data.get("student_id"),
                graduationYear=user_data.get("graduation_year"),
                major=user_data.get("major"),
                isVerified=user_data.get("is_verified", True),
                createdAt=created_at_dt
            )
            
            message = "Registration successful!" if input.purpose == 'register' else "Login successful!"
            
            return AuthResponse(
                success=True,
                message=message,
                token=token,
                user=graphql_user
            )
            
        except Exception as e:
            print(f"Error in verify_otp: {e}")
            return AuthResponse(
                success=False,
                message="An unexpected error occurred"
            )

@strawberry.type
class AuthQuery:
    @strawberry.field
    def getCurrentUser(self, token: str) -> Optional[User]:
        """Get current user from token"""
        try:
            # Verify token
            payload = AuthService.verify_jwt_token(token)
            if not payload:
                return None
            
            # Get user
            user_data = AuthService.get_user_by_email(payload.get("email"))
            if not user_data:
                return None
            
            # Convert ISO string back to datetime object for GraphQL
            created_at_str = user_data["created_at"]
            created_at_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            
            return User(
                id=user_data["id"],
                email=user_data["email"],
                firstName=user_data["first_name"],
                lastName=user_data["last_name"],
                studentId=user_data.get("student_id"),
                graduationYear=user_data.get("graduation_year"),
                major=user_data.get("major"),
                isVerified=user_data.get("is_verified", True),
                createdAt=created_at_dt
            )
            
        except Exception as e:
            print(f"Error in get_current_user: {e}")
            return None
