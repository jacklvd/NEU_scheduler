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
		<nav className="border-b border-northeastern-gray-light bg-northeastern-white/95 backdrop-blur supports-[backdrop-filter]:bg-northeastern-white/60">
			<div className="container mx-auto px-4">
				<div className="flex h-14 items-center justify-between">
					{/* Logo */}
					<div className="flex items-center space-x-8">
						<Link href="/" className="flex items-center space-x-2">
							<div className="h-8 w-8 rounded-md bg-northeastern-red flex items-center justify-center">
								<span className="text-northeastern-white font-bold text-sm">
									NEU
								</span>
							</div>
							<span className="font-bold text-xl text-northeastern-black">
								Course Scheduler
							</span>
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
										className={`flex items-center space-x-2 text-sm font-medium transition-colors hover:text-northeastern-red ${
											isActive
												? 'text-northeastern-red border-b-2 border-northeastern-red pb-1'
												: 'text-northeastern-gray'
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
							<div className="h-8 w-8 animate-spin rounded-full border-2 border-northeastern-red border-t-transparent"></div>
						) : session ? (
							<UserDropdown />
						) : (
							<div className="flex items-center space-x-2">
								<Button
									asChild
									variant="outline"
									size="sm"
									className="border-northeastern-blue text-northeastern-blue hover:bg-northeastern-blue hover:text-northeastern-white"
								>
									<Link href="/sign-in">Sign In</Link>
								</Button>
								<Button
									asChild
									size="sm"
									className="bg-northeastern-red hover:bg-northeastern-red/90 text-northeastern-white"
								>
									<Link href="/sign-up">Sign Up</Link>
								</Button>
							</div>
						)}
					</div>
				</div>

				{/* Mobile Navigation */}
				<div className="md:hidden flex items-center justify-between py-2 border-t border-northeastern-gray-light">
					{navItems.map(item => {
						const Icon = item.icon;
						const isActive = pathname === item.href;

						return (
							<Link
								key={item.href}
								href={item.href}
								className={`flex flex-col items-center space-y-1 p-2 rounded-md transition-colors ${
									isActive
										? 'text-northeastern-red bg-northeastern-red/10'
										: 'text-northeastern-gray hover:text-northeastern-red'
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
