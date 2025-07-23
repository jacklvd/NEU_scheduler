'use client';

import React, { useState } from 'react';
import { signOut, useSession } from 'next-auth/react';
import { User, LogOut, Settings, GraduationCap } from 'lucide-react';
import { Avatar } from '../ui/avatar';

export function UserDropdown() {
	const { data: session } = useSession();
	const [isOpen, setIsOpen] = useState(false);

	if (!session?.user) return null;

	const user = session.user;
	const getInitials = (firstName: string, lastName: string) => {
		return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
	};

	const handleSignOut = () => {
		signOut({ callbackUrl: '/' });
	};

	return (
		<div className="relative">
			<button
				onClick={() => setIsOpen(!isOpen)}
				className="flex items-center gap-2 p-2 rounded-md hover:bg-gray-100"
			>
				<Avatar className="h-8 w-8">
					<div className="flex items-center justify-center h-full w-full bg-primary text-primary-foreground text-sm font-medium">
						{getInitials(user.firstName, user.lastName)}
					</div>
				</Avatar>
				<span className="hidden md:block text-sm font-medium">
					{user.firstName} {user.lastName}
				</span>
			</button>

			{isOpen && (
				<>
					<div
						className="fixed inset-0 z-10"
						onClick={() => setIsOpen(false)}
					/>
					<div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-md shadow-lg z-20">
						<div className="p-3 border-b border-gray-100">
							<p className="font-medium">
								{user.firstName} {user.lastName}
							</p>
							<p className="text-sm text-gray-500">{user.email}</p>
							{user.major && (
								<p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
									<GraduationCap className="h-3 w-3" />
									{user.major}
								</p>
							)}
						</div>

						<div className="p-1">
							<button
								className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left hover:bg-gray-50 rounded-md"
								onClick={() => {
									setIsOpen(false);
									// Navigate to profile page
								}}
							>
								<User className="h-4 w-4" />
								Profile
							</button>

							<button
								className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left hover:bg-gray-50 rounded-md"
								onClick={() => {
									setIsOpen(false);
									// Navigate to settings
								}}
							>
								<Settings className="h-4 w-4" />
								Settings
							</button>

							<hr className="my-1" />

							<button
								className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left hover:bg-gray-50 rounded-md text-red-600"
								onClick={handleSignOut}
							>
								<LogOut className="h-4 w-4" />
								Sign Out
							</button>
						</div>
					</div>
				</>
			)}
		</div>
	);
}
