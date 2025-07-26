'use client';

import React from 'react';
import { useSearchParams } from 'next/navigation';
import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function AuthErrorPage() {
	const searchParams = useSearchParams();
	const error = searchParams.get('error');

	let errorMessage = 'Something went wrong';
	switch (error) {
		case 'CredentialsSignin':
			errorMessage = 'Invalid verification code';
			break;
		case 'OAuthAccountNotLinked':
			errorMessage = 'Account already exists with a different sign-in method';
			break;
		case 'Verification':
			errorMessage = 'Email verification failed';
			break;
		case 'AccessDenied':
			errorMessage = 'Access denied';
			break;
		default:
			errorMessage = 'An unexpected error occurred';
	}

	return (
		<div className="space-y-6">
			<div className="text-center">
				<div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
					<AlertCircle className="h-6 w-6 text-red-600" />
				</div>
				<h3 className="mt-3 text-lg font-medium">Authentication Error</h3>
				<p className="mt-2 text-sm text-muted-foreground">{errorMessage}</p>
			</div>
			<Button asChild className="w-full">
				<Link href="/sign-in">Try Again</Link>
			</Button>
		</div>
	);
}
