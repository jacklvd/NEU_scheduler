'use client';

import React, { useState } from 'react';
import { Sparkles, Loader2, BookOpen } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from './ui/card';
import { useAIPlan } from '../hooks/useCourses';

export function AIPlannerComponent() {
	const [interest, setInterest] = useState('');
	const [years, setYears] = useState(2);
	const { plan, loading, error, generatePlan } = useAIPlan();

	const handleGeneratePlan = () => {
		if (!interest.trim()) {
			alert('Please enter your area of interest');
			return;
		}
		generatePlan(interest, years);
	};

	return (
		<div className="space-y-6">
			{/* Input Form */}
			<Card className="border-northeastern-gray-light">
				<CardHeader className="bg-northeastern-orange text-northeastern-white">
					<CardTitle className="flex items-center gap-2">
						<Sparkles className="h-5 w-5" />
						AI Course Planner
					</CardTitle>
					<CardDescription className="text-northeastern-white/90">
						Get personalized course recommendations based on your interests
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
						<div className="md:col-span-2">
							<label className="block text-sm font-medium mb-2">
								Area of Interest
							</label>
							<Input
								value={interest}
								onChange={e => setInterest(e.target.value)}
								placeholder="e.g., machine learning, web development, cybersecurity"
							/>
						</div>
						<div>
							<label className="block text-sm font-medium mb-2">Years</label>
							<select
								value={years}
								onChange={e => setYears(Number(e.target.value))}
								className="w-full p-2 border rounded-md bg-background"
							>
								<option value={2}>2 Years (Masters)</option>
								<option value={4}>4 Years (Undergraduate)</option>
							</select>
						</div>
					</div>
					<Button
						onClick={handleGeneratePlan}
						disabled={loading}
						className="w-full bg-northeastern-orange hover:bg-northeastern-orange/90 text-northeastern-white"
					>
						{loading ? (
							<Loader2 className="h-4 w-4 animate-spin mr-2" />
						) : (
							<Sparkles className="h-4 w-4 mr-2" />
						)}
						Generate Plan
					</Button>
				</CardContent>
			</Card>

			{/* Error Display */}
			{error && (
				<Card className="border-northeastern-red">
					<CardContent className="p-4">
						<p className="text-northeastern-red">{error}</p>
					</CardContent>
				</Card>
			)}

			{/* Plan Results */}
			{plan.length > 0 && (
				<Card className="border-northeastern-gray-light">
					<CardHeader className="bg-northeastern-green text-northeastern-white">
						<CardTitle className="flex items-center gap-2">
							<BookOpen className="h-5 w-5" />
							Your Personalized Course Plan
						</CardTitle>
						<CardDescription className="text-northeastern-white/90">
							Suggested {years}-year plan for {interest}
						</CardDescription>
					</CardHeader>
					<CardContent>
						<div className="grid gap-4">
							{plan.map((semester, index) => (
								<Card
									key={index}
									className="bg-northeastern-gray-light/20 border-northeastern-gray-light"
								>
									<CardHeader className="pb-3">
										<CardTitle className="text-lg text-northeastern-black">
											Year {semester.year} - {semester.term}
										</CardTitle>
									</CardHeader>
									<CardContent>
										<ul className="space-y-1">
											{semester.courses.map((course, courseIndex) => (
												<li
													key={courseIndex}
													className="text-sm text-northeastern-gray-dark"
												>
													• {course}
												</li>
											))}
										</ul>
									</CardContent>
								</Card>
							))}
						</div>
					</CardContent>
				</Card>
			)}
		</div>
	);
}
