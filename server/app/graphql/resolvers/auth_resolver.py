import strawberry
from typing import Optional
from app.services.auth import AuthService
from app.graphql.types.user import User, AuthResponse, LoginInput, VerifyOTPInput, RegisterInput

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
            print(f"🔍 Verifying OTP: email={input.email}, purpose={input.purpose}, code_length={len(input.code) if input.code else 0}")
            print(f"📋 Registration data provided: {input.register_data is not None}")
            
            # Verify OTP
            is_valid = AuthService.verify_otp(input.email, input.code, input.purpose)
            
            if not is_valid:
                print(f"❌ OTP verification failed: email={input.email}, purpose={input.purpose}")
                return AuthResponse(
                    success=False,
                    message="Invalid or expired verification code"
                )
            
            user_data = None
            
            # Handle registration
            if input.purpose == 'register':
                if not input.register_data:
                    print(f"❌ Missing registration data for email={input.email}")
                    return AuthResponse(
                        success=False,
                        message="Registration data is required for registration"
                    )
                
                print(f"✅ OTP verified, creating user for email={input.email}")
                print(f"📋 Registration data: first_name={input.register_data.firstName}, last_name={input.register_data.lastName}")
                
                # Only store user data after OTP verification has succeeded
                # This ensures we don't store users until they're verified
                try:
                    # Use the snake_case fields directly
                    user_data = AuthService.create_user(
                        email=input.email,
                        first_name=input.register_data.first_name,
                        last_name=input.register_data.last_name,
                        student_id=input.register_data.student_id,
                        graduation_year=input.register_data.graduation_year,
                        major=input.register_data.major
                    )
                    print(f"✅ User created successfully: id={user_data.get('id')}")
                except Exception as create_error:
                    print(f"❌ Error creating user: {create_error}")
                    return AuthResponse(
                        success=False,
                        message=f"Error creating user: {str(create_error)}"
                    )
            
            # Handle login
            elif input.purpose == 'login':
                print(f"✅ OTP verified for login, retrieving user data for email={input.email}")
                user_data = AuthService.get_user_by_email(input.email)
                if not user_data:
                    print(f"❌ User not found for login: email={input.email}")
                    return AuthResponse(
                        success=False,
                        message="User not found"
                    )
                print(f"✅ User found for login: id={user_data.get('id')}")
            
            # Generate JWT token
            try:
                token_data = {
                    "user_id": user_data["id"],
                    "email": user_data["email"],
                    "purpose": input.purpose
                }
                print(f"🔑 Generating token for user: id={user_data['id']}")
                token = AuthService.generate_jwt_token(token_data)
                
                # Create session
                print(f"🔒 Creating session for user: id={user_data['id']}")
                session_token = AuthService.create_session(user_data["id"])
                print(f"✅ Session created successfully")
            except Exception as auth_error:
                print(f"❌ Error during authentication: {auth_error}")
                return AuthResponse(
                    success=False,
                    message=f"Authentication error: {str(auth_error)}"
                )
            
            # Convert to GraphQL user type
            graphql_user = User(
                id=user_data["id"],
                email=user_data["email"],
                firstName=user_data["first_name"],
                lastName=user_data["last_name"],
                studentId=user_data.get("student_id"),
                graduationYear=user_data.get("graduation_year"),
                major=user_data.get("major"),
                isVerified=user_data.get("is_verified", True),
                createdAt=user_data["created_at"]
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
            
            return User(
                id=user_data["id"],
                email=user_data["email"],
                firstName=user_data["first_name"],
                lastName=user_data["last_name"],
                studentId=user_data.get("student_id"),
                graduationYear=user_data.get("graduation_year"),
                major=user_data.get("major"),
                isVerified=user_data.get("is_verified", True),
                createdAt=user_data["created_at"]
            )
            
        except Exception as e:
            print(f"Error in get_current_user: {e}")
            return None
