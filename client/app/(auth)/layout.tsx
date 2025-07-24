import React from 'react';

export default function AuthLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<div className="container flex min-h-screen w-full flex-col items-center justify-center py-12 bg-northeastern-gray-light/10">
			<div className="max-w-md w-full mx-auto space-y-6">
				<div className="text-center space-y-2">
					<h1 className="text-3xl font-bold text-northeastern-black">
						NEU Course Scheduler
					</h1>
					<p className="text-northeastern-gray">
						Sign in to your account or create a new one
					</p>
				</div>
				{children}
			</div>
		</div>
	);
}
