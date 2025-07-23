'use server';

import { AuthAPI } from '../api/auth';
import type { RegisterData } from '@/types/auth';

export async function requestOTP(email: string, purpose: 'login' | 'register') {
	return await AuthAPI.requestOTP(email, purpose);
}

export async function verifyOTP(
	email: string,
	code: string,
	purpose: 'login' | 'register',
	register_data?: RegisterData
) {
	return await AuthAPI.verifyOTP(email, code, purpose, register_data);
}

export async function getCurrentUser(token: string) {
	return await AuthAPI.getCurrentUser(token);
}
