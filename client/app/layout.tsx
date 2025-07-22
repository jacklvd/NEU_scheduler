import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Navbar } from '@/components/navbar';
import { Toaster } from '@/components/ui/sonner';
import { AuthProvider } from '@/components/providers/auth-provider';
import { auth } from '@/auth';
import { ReactNode } from 'react';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
	title: 'NEU Course Scheduler',
	description: 'AI-powered academic planning for Northeastern students',
};

const RootLayout = async ({ children }: { children: ReactNode }) => {
	const session = await auth();
	return (
		<html lang="en">
			<body className={inter.className}>
				<AuthProvider session={session}>
					<Navbar />
					<main className="min-h-screen bg-background">{children}</main>
				</AuthProvider>
				<Toaster />
			</body>
		</html>
	);
};
export default RootLayout;
