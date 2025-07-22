export interface User {
	id: string;
	email: string;
	first_name: string;
	last_name: string;
	student_id?: string;
	major?: string;
	graduation_year?: number;
	is_verified: boolean;
	created_at: string;

	// Maintain camelCase aliases for backwards compatibility
	firstName?: string;
	lastName?: string;
	studentId?: string;
	graduationYear?: number;
	isVerified?: boolean;
	createdAt?: string;
}

export interface AuthResponse {
	success: boolean;
	message: string;
	token?: string;
	user?: User;
}

export interface RegisterData {
	// Snake case fields for server communication
	first_name?: string;
	last_name?: string;
	student_id?: string;
	graduation_year?: number;

	// CamelCase fields for client-side usage
	firstName: string;
	lastName: string;
	studentId?: string;
	major?: string;
	graduationYear?: number;
}

export interface AuthState {
	user: User | null;
	token: string | null;
	isAuthenticated: boolean;
	isLoading: boolean;
}
