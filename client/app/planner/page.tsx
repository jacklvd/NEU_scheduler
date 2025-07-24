import { AIPlannerComponent } from '@/components/ai-planner';

export default function PlannerPage() {
	return (
		<div className="container mx-auto px-4 py-8">
			<div className="mb-8">
				<h1 className="text-3xl font-bold mb-2 text-northeastern-black">
					AI Course Planner
				</h1>
				<p className="text-northeastern-gray">
					Get personalized course recommendations powered by AI
				</p>
			</div>
			<AIPlannerComponent />
		</div>
	);
}
