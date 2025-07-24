import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { AuthAPI } from '@/lib/api/auth';
import type { DefaultSession } from 'next-auth';

// Extend the built-in session types
declare module 'next-auth' {
	interface Session {
		user: {
			id: string;
			email: string;
			firstName: string;
			lastName: string;
			studentId?: string;
			major?: string;
			graduationYear?: number;
			isVerified: boolean;
		} & DefaultSession['user'];
	}

	// Extend the built-in user types
	interface User {
		id: string;
		email: string;
		firstName: string;
		lastName: string;
		studentId?: string;
		major?: string;
		graduationYear?: number;
		isVerified: boolean;
	}
}

// Extend the JWT token type
declare module '@auth/core/jwt' {
	interface JWT {
		id: string;
		email: string;
		firstName: string;
		lastName: string;
		studentId?: string;
		major?: string;
		graduationYear?: number;
		isVerified: boolean;
	}
}

export const { handlers, auth, signIn, signOut } = NextAuth({
	providers: [
		// Sign In Provider
		Credentials({
			id: 'signin',
			name: 'Sign In',
			credentials: {
				email: { label: 'Email', type: 'email' },
				code: { label: 'Verification Code', type: 'text' },
			},
			async authorize(credentials) {
				console.log('🔐 NextAuth authorize called for signin');
				if (!credentials?.email || !credentials?.code) {
					throw new Error('Missing email or verification code');
				}

				try {
					console.log('🔐 Calling AuthAPI.verifyOTP for login');
					const response = await AuthAPI.verifyOTP(
						credentials.email as string,
						credentials.code as string,
						'login'
					);

					console.log('🔐 AuthAPI response:', response);

					if (response.success && response.user) {
						const user = response.user;
						console.log('🔐 Raw user from server:', user);

						// Map snake_case server fields to camelCase NextAuth fields
						const mappedUser = {
							id: user.id,
							email: user.email,
							firstName: user.first_name || user.firstName || '',
							lastName: user.last_name || user.lastName || '',
							studentId: user.student_id || user.studentId || undefined,
							major: user.major || undefined,
							graduationYear:
								user.graduation_year || user.graduationYear || undefined,
							isVerified: user.is_verified ?? user.isVerified ?? true,
						};

						console.log('🔐 Mapped user for NextAuth:', mappedUser);
						return mappedUser;
					}

					throw new Error(response.message || 'Authentication failed');
				} catch (error) {
					console.error('Sign in error:', error);
					throw new Error(
						error instanceof Error ? error.message : 'Authentication failed'
					);
				}
			},
		}),
		// Registration Provider
		Credentials({
			id: 'register',
			name: 'Register',
			credentials: {
				email: { label: 'Email', type: 'email' },
				code: { label: 'Verification Code', type: 'text' },
				firstName: { label: 'First Name', type: 'text' },
				lastName: { label: 'Last Name', type: 'text' },
				studentId: { label: 'Student ID', type: 'text' },
				major: { label: 'Major', type: 'text' },
				graduationYear: { label: 'Graduation Year', type: 'number' },
			},
			async authorize(credentials) {
				if (
					!credentials?.email ||
					!credentials?.code ||
					!credentials?.firstName ||
					!credentials?.lastName
				) {
					throw new Error('Missing required registration information');
				}

				try {
					const registerData = {
						firstName: credentials.firstName as string,
						lastName: credentials.lastName as string,
						studentId: (credentials.studentId as string) || undefined,
						major: (credentials.major as string) || undefined,
						graduationYear: credentials.graduationYear
							? parseInt(credentials.graduationYear as string)
							: undefined,
					};

					const response = await AuthAPI.verifyOTP(
						credentials.email as string,
						credentials.code as string,
						'register',
						registerData
					);

					if (response.success && response.user) {
						const user = response.user;
						// Map snake_case server fields to camelCase NextAuth fields
						return {
							id: user.id,
							email: user.email,
							firstName: user.first_name || user.firstName || '',
							lastName: user.last_name || user.lastName || '',
							studentId: user.student_id || user.studentId || undefined,
							major: user.major || undefined,
							graduationYear:
								user.graduation_year || user.graduationYear || undefined,
							isVerified: user.is_verified ?? user.isVerified ?? true,
						};
					}

					throw new Error(response.message || 'Registration failed');
				} catch (error) {
					console.error('Registration error:', error);
					throw new Error(
						error instanceof Error ? error.message : 'Registration failed'
					);
				}
			},
		}),
	],
	session: {
		strategy: 'jwt',
		maxAge: 4 * 60 * 60, // 4 hours
		updateAge: 60 * 30, // 30 minutes
	},
	jwt: {
		maxAge: 60 * 60, // 1 hour
	},
	callbacks: {
		async jwt({ token, user }) {
			if (user) {
				console.log('JWT callback - user signed in:', {
					userId: user.id,
					email: user.email,
					firstName: user.firstName,
					isVerified: user.isVerified,
				});
				token.id = user.id;
				token.email = user.email;
				token.firstName = user.firstName || '';
				token.lastName = user.lastName || '';
				token.studentId = user.studentId;
				token.major = user.major;
				token.graduationYear = user.graduationYear;
				token.isVerified = user.isVerified ?? true;
			}
			console.log('JWT callback - final token:', {
				id: token.id,
				email: token.email,
				firstName: token.firstName,
			});
			return token;
		},
		async session({ session, token }) {
			console.log('Session callback - input token:', {
				tokenId: token.id,
				tokenEmail: token.email,
				tokenFirstName: token.firstName,
			});

			if (token && session.user) {
				console.log('Session callback - creating session for user:', {
					sessionEmail: session.user.email,
				});
				session.user.id = token.id as string;
				session.user.firstName = token.firstName as string;
				session.user.lastName = token.lastName as string;
				session.user.studentId = token.studentId as string | undefined;
				session.user.major = token.major as string | undefined;
				session.user.graduationYear = token.graduationYear as
					| number
					| undefined;
				session.user.isVerified = token.isVerified as boolean;
			}

			console.log('Session callback - final session:', {
				userId: session.user?.id,
				userEmail: session.user?.email,
				userFirstName: session.user?.firstName,
			});
			return session;
		},
	},
	pages: {
		signIn: '/sign-in',
		error: '/error',
	},
});
