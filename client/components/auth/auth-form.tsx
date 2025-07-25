'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { signIn } from 'next-auth/react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Mail, KeyRound, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { requestOTP as requestOTPAction } from '@/lib/actions/auth-actions';

interface RegisterData {
	firstName: string;
	lastName: string;
	studentId: string;
	major: string;
	graduationYear: number;
}

type AuthStep = 'email' | 'otp';
type AuthMode = 'login' | 'register';

interface OTPAuthFormProps {
	initialMode?: AuthMode;
}

const DEFAULT_YEARS_TO_GRADUATION = 4;

export function OTPAuthForm({ initialMode = 'login' }: OTPAuthFormProps) {
	const router = useRouter();
	const [step, setStep] = useState<AuthStep>('email');
	const [mode, setMode] = useState<AuthMode>(initialMode);
	const [email, setEmail] = useState('');
	const [otp, setOtp] = useState('');
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState('');
	const [register_data, setRegister_data] = useState<RegisterData>({
		firstName: '',
		lastName: '',
		studentId: '',
		major: '',
		graduationYear: new Date().getFullYear() + 4,
	});

	const requestOTP = async () => {
		if (!email.trim()) {
			setError('Email is required');
			return;
		}

		setIsLoading(true);
		setError('');

		try {
			const data = await requestOTPAction(email, mode);

			if (data.success) {
				setStep('otp');
				toast.success(`Verification code sent to ${email}`);
			} else {
				setError(data.message || 'Failed to send verification code');
			}
		} catch (err) {
			console.error('Error requesting OTP:', err);
			setError('Network error. Please try again.');
		} finally {
			setIsLoading(false);
		}
	};

	const verifyOTP = async () => {
		if (!otp.trim()) {
			setError('Verification code is required');
			return;
		}

		if (mode === 'register') {
			if (!register_data.firstName || !register_data.lastName) {
				setError('First name and last name are required');
				return;
			}
		}

		setIsLoading(true);
		setError('');

		try {
			console.log('Verifying OTP with mode:', mode);
			console.log(
				'Register data:',
				mode === 'register' ? JSON.stringify(register_data) : 'N/A'
			);

			// Use NextAuth signIn instead of direct GraphQL
			const credentials: Record<string, string> = {
				email,
				code: otp,
			};

			// Add registration data if registering
			if (mode === 'register') {
				Object.assign(credentials, {
					firstName: register_data.firstName,
					lastName: register_data.lastName,
					studentId: register_data.studentId,
					major: register_data.major,
					graduationYear: register_data.graduationYear?.toString(),
				});
			}

			console.log(
				'🔐 Calling NextAuth signIn with provider:',
				mode === 'register' ? 'register' : 'signin'
			);

			const result = await signIn(mode === 'register' ? 'register' : 'signin', {
				...credentials,
				redirect: false, // Don't redirect automatically
			});

			console.log('🔐 NextAuth signIn result:', result);

			if (result?.error) {
				setError(result.error);
			} else if (result?.ok) {
				toast.success(
					mode === 'register'
						? 'Account created successfully!'
						: 'Signed in successfully!'
				);

				// Redirect to dashboard on successful authentication
				router.push('/dashboard');
				router.refresh();
			}
		} catch (error) {
			console.error('Exception during OTP verification:', error);
			setError(
				error instanceof Error
					? `Verification error: ${error.message}`
					: 'Verification failed. Please try again.'
			);
		} finally {
			setIsLoading(false);
		}
	};

	const switchMode = () => {
		setMode(mode === 'login' ? 'register' : 'login');
		setStep('email');
		setError('');
		setOtp('');
	};

	return (
		<Card className="w-full max-w-md mx-auto">
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					{step === 'email' && <Mail className="h-5 w-5" />}
					{step === 'otp' && <KeyRound className="h-5 w-5" />}
					{step === 'email' &&
						(mode === 'login' ? 'Sign In' : 'Create Account')}
					{step === 'otp' && 'Enter Verification Code'}
				</CardTitle>
			</CardHeader>

			<CardContent className="space-y-4">
				{error && (
					<div className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
						<AlertCircle className="h-4 w-4" />
						{error}
					</div>
				)}

				{step === 'email' && (
					<div className="space-y-4">
						<div>
							<label className="block text-sm font-medium mb-2">
								Email Address
							</label>
							<Input
								type="email"
								placeholder="Enter your Northeastern email"
								value={email}
								onChange={e => setEmail(e.target.value)}
								onKeyPress={e => e.key === 'Enter' && requestOTP()}
							/>
						</div>

						<Button
							onClick={requestOTP}
							className="w-full"
							disabled={isLoading}
						>
							{isLoading ? 'Sending...' : 'Send Verification Code'}
						</Button>

						<div className="text-center">
							<button
								type="button"
								onClick={switchMode}
								className="text-sm text-northeastern-blue hover:text-northeastern-teal"
							>
								{mode === 'login'
									? "Don't have an account? Sign up"
									: 'Already have an account? Sign in'}
							</button>
						</div>
					</div>
				)}

				{step === 'otp' && (
					<div className="space-y-4">
						<div className="text-sm text-gray-600 mb-4">
							We sent a verification code to <strong>{email}</strong>
						</div>

						<div>
							<label className="block text-sm font-medium mb-2">
								Verification Code
							</label>
							<Input
								type="text"
								placeholder="Enter 6-digit code"
								value={otp}
								onChange={e =>
									setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))
								}
								maxLength={6}
								className="text-center text-lg tracking-widest"
								onKeyPress={e => e.key === 'Enter' && verifyOTP()}
							/>
						</div>

						{mode === 'register' && (
							<div className="space-y-3">
								<div className="grid grid-cols-2 gap-3">
									<div>
										<label className="block text-sm font-medium mb-1">
											First Name *
										</label>
										<Input
											placeholder="First name"
											value={register_data.firstName}
											onChange={e =>
												setRegister_data({
													...register_data,
													firstName: e.target.value,
												})
											}
										/>
									</div>
									<div>
										<label className="block text-sm font-medium mb-1">
											Last Name *
										</label>
										<Input
											placeholder="Last name"
											value={register_data.lastName}
											onChange={e =>
												setRegister_data({
													...register_data,
													lastName: e.target.value,
												})
											}
										/>
									</div>
								</div>

								<div>
									<label className="block text-sm font-medium mb-1">
										Student ID (Optional)
									</label>
									<Input
										placeholder="e.g., 002123456"
										value={register_data.studentId}
										onChange={e =>
											setRegister_data({
												...register_data,
												studentId: e.target.value,
											})
										}
									/>
								</div>

								<div>
									<label className="block text-sm font-medium mb-1">
										Major (Optional)
									</label>
									<Input
										placeholder="e.g., Computer Science"
										value={register_data.major}
										onChange={e =>
											setRegister_data({
												...register_data,
												major: e.target.value,
											})
										}
									/>
								</div>

								<div>
									<label className="block text-sm font-medium mb-1">
										Expected Graduation Year
									</label>
									<Input
										type="number"
										placeholder="2025"
										value={register_data.graduationYear || ''}
										onChange={e =>
											setRegister_data({
												...register_data,
												graduationYear:
													parseInt(e.target.value) ||
													new Date().getFullYear() +
														DEFAULT_YEARS_TO_GRADUATION,
											})
										}
									/>
								</div>
							</div>
						)}

						<Button onClick={verifyOTP} className="w-full" disabled={isLoading}>
							{isLoading
								? 'Verifying...'
								: mode === 'register'
									? 'Create Account'
									: 'Sign In'}
						</Button>

						<div className="flex justify-between text-sm">
							<button
								type="button"
								onClick={() => setStep('email')}
								className="text-gray-600 hover:text-gray-800"
							>
								← Back
							</button>
							<button
								type="button"
								onClick={requestOTP}
								className="text-blue-600 hover:text-blue-800"
								disabled={isLoading}
							>
								Resend Code
							</button>
						</div>
					</div>
				)}
			</CardContent>
		</Card>
	);
}
