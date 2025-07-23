import { AuthGuard } from '@/components/auth/auth-guard';

export default function DashboardPage() {
	return (
		<AuthGuard>
			<div className="container mx-auto px-4 py-8">
				<h1 className="text-3xl font-bold mb-6">Dashboard</h1>
				<p>Welcome to your protected dashboard!</p>
			</div>
		</AuthGuard>
	);
}
