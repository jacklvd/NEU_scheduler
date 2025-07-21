import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Navigation } from '@/components/navbar';
import { Toaster } from '@/components/ui/sonner';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
	title: 'NEU Course Scheduler',
	description: 'AI-powered academic planning for Northeastern students',
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="en">
			<body className={inter.className}>
				<Navigation />
				<main className="min-h-screen bg-background">{children}</main>
				<Toaster />
			</body>
		</html>
	);
}
