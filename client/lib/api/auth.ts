/* eslint-disable @typescript-eslint/no-explicit-any */
// Removing "use server" directive and exporting functions directly

import { graphqlClient } from './graphql';
import type { AuthResponse, RegisterData, User } from '@/types/auth';

export class AuthAPI {
	static async requestOTP(
		email: string,
		purpose: 'login' | 'register'
	): Promise<AuthResponse> {
		const mutation = `
      mutation RequestOTP($email: String!, $purpose: String!) {
        requestOtp(email: $email, purpose: $purpose) {
          success
          message
        }
      }
    `;

		// console.log('Requesting OTP with:', { email, purpose });

		try {
			const response = (await graphqlClient.request(mutation, {
				email,
				purpose,
			})) as { requestOtp: AuthResponse };
			// console.log('OTP request response:', response);
			return response.requestOtp;
		} catch (error) {
			console.error('Error requesting OTP:', error);

			// Log detailed error info
			if (error instanceof Error) {
				console.error('Error message:', error.message);
				console.error('Error stack:', error.stack);
				if ('response' in (error as any)) {
					console.error('Error response:', (error as any).response);
				}
			}

			return {
				success: false,
				message: 'Failed to send verification code. Please try again.',
			};
		}
	}

	static async verifyOTP(
		email: string,
		code: string,
		purpose: 'login' | 'register',
		register_data?: RegisterData
	): Promise<AuthResponse> {
		const mutation = `
      mutation VerifyOTP($input: VerifyOTPInput!) {
        verifyOtp(input: $input) {
          success
          message
          token
          user {
            id
            email
            first_name
            last_name
            student_id
            major
            graduation_year
            is_verified
            created_at
          }
        }
      }
    `;

		const input: any = {
			email,
			code,
			purpose,
		};

		if (purpose === 'register' && register_data) {
			// Send snake_case field names to match the GraphQL schema
			input.register_data = {
				firstName: register_data.firstName,
				lastName: register_data.lastName,
				studentId: register_data.studentId,
				major: register_data.major,
				graduationYear: register_data.graduationYear,
			};

			// console.log('Preparing GraphQL input:', JSON.stringify(input));
		}

		try {
			console.log('🔍 Sending GraphQL mutation:', mutation);
			console.log('🔍 GraphQL input:', input);

			const response = (await graphqlClient.request(mutation, { input })) as {
				verifyOtp: AuthResponse;
			} | null;

			console.log('🔍 Raw GraphQL response:', response);

			// Check if response is null or undefined
			if (!response) {
				console.error('❌ Error: GraphQL returned null response');
				return {
					success: false,
					message: 'Verification failed. The server did not respond properly.',
				};
			}

			// Check if verifyOtp property exists in response
			if (!response.verifyOtp) {
				console.error(
					'❌ Error: GraphQL response missing verifyOtp field:',
					response
				);
				return {
					success: false,
					message: 'Verification failed. Invalid server response format.',
				};
			}

			console.log('✅ Server response user data:', response.verifyOtp.user);
			console.log('✅ Server response success:', response.verifyOtp.success);
			console.log('✅ Server response message:', response.verifyOtp.message);

			return response.verifyOtp;
		} catch (error) {
			console.error('Error verifying OTP:', error);

			// Extract more detailed error information if available
			let errorMessage =
				'Verification failed. Please check your code and try again.';
			if (error instanceof Error) {
				console.error('Error details:', {
					message: error.message,
					stack: error.stack,
				});

				// Check for GraphQL specific errors
				const gqlError = error as any;
				if (gqlError.response?.errors?.length) {
					const firstError = gqlError.response.errors[0];
					errorMessage = `GraphQL error: ${firstError.message || 'Unknown error'}`;
					console.error('GraphQL error details:', gqlError.response.errors);
				}
			}

			return {
				success: false,
				message: errorMessage,
			};
		}
	}

	static async getCurrentUser(token: string): Promise<User | null> {
		const query = `
      query GetCurrentUser($token: String!) {
        getCurrentUser(token: $token) {
          id
          email
          first_name
          last_name
          student_id
          major
          graduation_year
          is_verified
          created_at
        }
      }
    `;

		try {
			const response = (await graphqlClient.request(query, { token })) as {
				getCurrentUser: User | null;
			} | null;

			// Check if response is null or undefined
			if (!response) {
				console.error(
					'Error: GraphQL returned null response for getCurrentUser'
				);
				return null;
			}

			return response.getCurrentUser;
		} catch (error) {
			console.error('Error getting current user:', error);

			// Extract more detailed error information if available
			if (error instanceof Error) {
				console.error('Error details:', {
					message: error.message,
					stack: error.stack,
				});

				// Check for GraphQL specific errors
				const gqlError = error as any;
				if (gqlError.response?.errors?.length) {
					console.error('GraphQL error details:', gqlError.response.errors);
				}
			}

			return null;
		}
	}
}

// Export the class as the default export as well for better compatibility
export default AuthAPI;
