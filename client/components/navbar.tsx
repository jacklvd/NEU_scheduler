'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { Search, Sparkles, Calendar, Home } from 'lucide-react';
import { Button } from './ui/button';
import { UserDropdown } from './auth/user-dropdown';

export function Navbar() {
	const pathname = usePathname();
	const { data: session, status } = useSession();

	const navItems = [
		{ href: '/', label: 'Home', icon: Home },
		{ href: '/courses', label: 'Courses', icon: Search },
		{ href: '/planner', label: 'AI Planner', icon: Sparkles },
		{ href: '/schedule', label: 'Schedule', icon: Calendar },
	];

	return (
		<nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
			<div className="container mx-auto px-4">
				<div className="flex h-14 items-center justify-between">
					{/* Logo */}
					<div className="flex items-center space-x-8">
						<Link href="/" className="flex items-center space-x-2">
							<div className="h-8 w-8 rounded-md bg-primary flex items-center justify-center">
								<span className="text-primary-foreground font-bold text-sm">
									NEU
								</span>
							</div>
							<span className="font-bold text-xl">Course Scheduler</span>
						</Link>

						{/* Desktop Navigation */}
						<div className="hidden md:flex items-center space-x-6">
							{navItems.map(item => {
								const Icon = item.icon;
								const isActive = pathname === item.href;

								return (
									<Link
										key={item.href}
										href={item.href}
										className={`flex items-center space-x-2 text-sm font-medium transition-colors hover:text-primary ${
											isActive
												? 'text-primary border-b-2 border-primary pb-1'
												: 'text-muted-foreground'
										}`}
									>
										<Icon className="h-4 w-4" />
										<span>{item.label}</span>
									</Link>
								);
							})}
						</div>
					</div>

					{/* Auth Section */}
					<div className="flex items-center space-x-4">
						{status === 'loading' ? (
							<div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
						) : session ? (
							<UserDropdown />
						) : (
							<div className="flex items-center space-x-2">
								<Button asChild variant="outline" size="sm">
									<Link href="/sign-in">Sign In</Link>
								</Button>
								<Button asChild size="sm">
									<Link href="/sign-up">Sign Up</Link>
								</Button>
							</div>
						)}
					</div>
				</div>

				{/* Mobile Navigation */}
				<div className="md:hidden flex items-center justify-between py-2 border-t">
					{navItems.map(item => {
						const Icon = item.icon;
						const isActive = pathname === item.href;

						return (
							<Link
								key={item.href}
								href={item.href}
								className={`flex flex-col items-center space-y-1 p-2 rounded-md transition-colors ${
									isActive
										? 'text-primary bg-primary/10'
										: 'text-muted-foreground hover:text-primary'
								}`}
							>
								<Icon className="h-4 w-4" />
								<span className="text-xs">{item.label}</span>
							</Link>
						);
					})}
				</div>
			</div>
		</nav>
	);
}
