import { AuthGuard } from '@/components/auth/auth-guard';

export default function DashboardPage() {
	return (
		<AuthGuard>
			<div className="container mx-auto px-4 py-8">
				<h1 className="text-3xl font-bold mb-6 text-northeastern-black">
					Dashboard
				</h1>
				<div className="bg-northeastern-gray-light/20 border border-northeastern-gray-light rounded-lg p-6">
					<p className="text-northeastern-gray-dark">
						Welcome to your protected dashboard!
					</p>
				</div>
			</div>
		</AuthGuard>
	);
}
