'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Search, Sparkles, Calendar, Home } from 'lucide-react';
import { Button } from './ui/button';

export function Navigation() {
	const pathname = usePathname();

	const navItems = [
		{ href: '/', label: 'Home', icon: Home },
		{ href: '/courses', label: 'Course Search', icon: Search },
		{ href: '/planner', label: 'AI Planner', icon: Sparkles },
		{ href: '/schedule', label: 'My Schedule', icon: Calendar },
	];

	return (
		<nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
			<div className="container mx-auto px-4">
				<div className="flex h-14 items-center justify-between">
					<div className="flex items-center space-x-8">
						<Link href="/" className="flex items-center space-x-2">
							<div className="h-8 w-8 rounded-md bg-primary flex items-center justify-center">
								<span className="text-primary-foreground font-bold text-sm">
									NEU
								</span>
							</div>
							<span className="font-bold text-xl">Course Scheduler</span>
						</Link>

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

					<div className="flex items-center space-x-4">
						<Button variant="outline" size="sm">
							Sign In
						</Button>
						<Button size="sm">Get Started</Button>
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
