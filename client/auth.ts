import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
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
		CredentialsProvider({
			id: 'otp-auth',
			name: 'OTP Authentication',
			credentials: {
				email: { label: 'Email', type: 'email' },
				code: { label: 'Verification Code', type: 'text' },
				purpose: { label: 'Purpose', type: 'text' },
				// Registration fields
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
					!credentials?.purpose
				) {
					throw new Error('Missing required credentials');
				}

				try {
					const registerData =
						credentials.purpose === 'register'
							? {
									// Only pass camelCase field names to the API
									// The API client will handle conversion to snake_case
									firstName: credentials.firstName as string,
									lastName: credentials.lastName as string,
									studentId: (credentials.studentId as string) || undefined,
									major: (credentials.major as string) || undefined,
									graduationYear: credentials.graduationYear
										? parseInt(credentials.graduationYear as string)
										: undefined,
								}
							: undefined;

					const response = await AuthAPI.verifyOTP(
						credentials.email as string,
						credentials.code as string,
						credentials.purpose as 'login' | 'register',
						registerData
					);

					if (response.success && response.user) {
						// Handle both camelCase and snake_case field names from response
						const user = response.user;
						return {
							id: user.id,
							email: user.email,
							firstName: user.firstName || user.first_name,
							lastName: user.lastName || user.last_name,
							studentId: user.studentId || user.student_id,
							major: user.major,
							graduationYear: user.graduationYear || user.graduation_year,
							isVerified: user.isVerified || user.is_verified,
						};
					}

					throw new Error(response.message || 'Authentication failed');
				} catch (error) {
					console.error('Auth error:', error);
					throw new Error(
						error instanceof Error ? error.message : 'Authentication failed'
					);
				}
			},
		}),
	],
	session: {
		strategy: 'jwt',
		maxAge: 4 * 60 * 60,
		updateAge: 60 * 30,
	},
	jwt: {
		maxAge: 60 * 60, // 1 hour
	},
	callbacks: {
		async jwt({ token, user }) {
			if (user) {
				// Make sure we have all required fields
				token.id = user.id;
				token.firstName = user.firstName || '';
				token.lastName = user.lastName || '';
				token.studentId = user.studentId;
				token.major = user.major;
				token.graduationYear = user.graduationYear;
				token.isVerified =
					typeof user.isVerified === 'boolean' ? user.isVerified : true;
			}
			return token;
		},
		async session({ session, token }) {
			if (token && session.user) {
				session.user.id = token.id as string;
				session.user.firstName = token.firstName as string;
				session.user.lastName = token.lastName as string;
				session.user.studentId = token.studentId as string | undefined;
				session.user.major = token.major as string | undefined;
				session.user.graduationYear =
					typeof token.graduationYear === 'number'
						? token.graduationYear
						: typeof token.graduationYear === 'string'
							? parseInt(token.graduationYear)
							: undefined;
				session.user.isVerified =
					typeof token.isVerified === 'boolean' ? token.isVerified : true;
			}
			return session;
		},
	},
	pages: {
		signIn: '/sign-in',
		error: '/error',
	},
});
