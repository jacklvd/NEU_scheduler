import Link from 'next/link';
import { Button } from '../components/ui/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '../components/ui/card';
import {
	Search,
	Sparkles,
	Calendar,
	Users,
	TrendingUp,
	Shield,
} from 'lucide-react';

export default function HomePage() {
	const features = [
		{
			icon: Search,
			title: 'Course Search',
			description:
				'Browse and search through thousands of courses with real-time availability.',
			href: '/courses',
		},
		{
			icon: Sparkles,
			title: 'AI-Powered Planning',
			description:
				'Get personalized course recommendations based on your interests and career goals.',
			href: '/planner',
		},
		{
			icon: Calendar,
			title: 'Schedule Management',
			description:
				'Plan your academic journey with our intuitive scheduling tools.',
			href: '/schedule',
		},
		{
			icon: Users,
			title: 'Instructor Insights',
			description:
				'View instructor information and class details to make informed decisions.',
			href: '/courses',
		},
		{
			icon: TrendingUp,
			title: 'Progress Tracking',
			description:
				'Monitor your academic progress and stay on track for graduation.',
			href: '/schedule',
		},
		{
			icon: Shield,
			title: 'Prerequisite Validation',
			description:
				'Automatically check prerequisites and avoid scheduling conflicts.',
			href: '/planner',
		},
	];

	return (
		<div className="container mx-auto px-4 py-12">
			{/* Hero Section */}
			<div className="text-center mb-16">
				<h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-northeastern-red to-northeastern-orange bg-clip-text text-transparent">
					Plan Your Academic Journey
				</h1>
				<p className="text-xl text-northeastern-gray mb-8 max-w-3xl mx-auto">
					AI-powered course planning for Northeastern University students.
					Discover courses, get personalized recommendations, and build your
					perfect schedule.
				</p>
				<div className="flex flex-col sm:flex-row gap-4 justify-center">
					<Button
						asChild
						size="lg"
						className="bg-northeastern-red hover:bg-northeastern-red/90 text-northeastern-white"
					>
						<Link href="/courses">
							<Search className="mr-2 h-4 w-4" />
							Search Courses
						</Link>
					</Button>
					<Button
						asChild
						variant="outline"
						size="lg"
						className="border-northeastern-red text-northeastern-red hover:bg-northeastern-red hover:text-northeastern-white"
					>
						<Link href="/planner">
							<Sparkles className="mr-2 h-4 w-4" />
							Try AI Planner
						</Link>
					</Button>
				</div>
			</div>

			{/* Features Grid */}
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
				{features.map((feature, index) => {
					const Icon = feature.icon;
					return (
						<Card
							key={index}
							className="hover:shadow-lg transition-shadow border-northeastern-gray-light hover:border-northeastern-red"
						>
							<CardHeader>
								<div className="flex items-center space-x-3">
									<div className="p-2 bg-northeastern-red/10 rounded-md">
										<Icon className="h-6 w-6 text-northeastern-red" />
									</div>
									<CardTitle className="text-xl text-northeastern-black">
										{feature.title}
									</CardTitle>
								</div>
							</CardHeader>
							<CardContent>
								<CardDescription className="text-base mb-4 text-northeastern-gray">
									{feature.description}
								</CardDescription>
								<Button
									asChild
									variant="outline"
									size="sm"
									className="border-northeastern-blue text-northeastern-blue hover:bg-northeastern-blue hover:text-northeastern-white"
								>
									<Link href={feature.href}>Learn More</Link>
								</Button>
							</CardContent>
						</Card>
					);
				})}
			</div>

			{/* Quick Stats */}
			<div className="bg-northeastern-gray-light/30 rounded-lg p-8 text-center border border-northeastern-gray-light">
				<h2 className="text-2xl font-bold mb-6 text-northeastern-black">
					Trusted by NEU Students
				</h2>
				<div className="grid grid-cols-1 md:grid-cols-3 gap-8">
					<div>
						<div className="text-3xl font-bold text-northeastern-red mb-2">
							2,000+
						</div>
						<div className="text-northeastern-gray">Courses Available</div>
					</div>
					<div>
						<div className="text-3xl font-bold text-northeastern-red mb-2">
							95%
						</div>
						<div className="text-northeastern-gray">Planning Accuracy</div>
					</div>
					<div>
						<div className="text-3xl font-bold text-northeastern-red mb-2">
							24/7
						</div>
						<div className="text-northeastern-gray">AI Assistance</div>
					</div>
				</div>
			</div>
		</div>
	);
}
