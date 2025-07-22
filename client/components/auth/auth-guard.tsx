'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface AuthGuardProps {
	children: React.ReactNode;
	fallback?: React.ReactNode;
	requireAuth?: boolean;
}

export function AuthGuard({
	children,
	fallback,
	requireAuth = true,
}: AuthGuardProps) {
	const { data: session, status } = useSession();
	const router = useRouter();

	useEffect(() => {
		if (status === 'loading') return; // Still loading

		if (requireAuth && !session) {
			router.push('/auth/signin');
			return;
		}
	}, [session, status, requireAuth, router]);

	if (status === 'loading') {
		return (
			<div className="flex items-center justify-center min-h-screen">
				<div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
			</div>
		);
	}

	if (requireAuth && !session) {
		return (
			fallback || (
				<div className="flex items-center justify-center min-h-screen">
					<div className="text-center">
						<h2 className="text-2xl font-bold mb-4">Authentication Required</h2>
						<p className="text-gray-600 mb-6">Redirecting to sign in...</p>
					</div>
				</div>
			)
		);
	}

	return <>{children}</>;
}
