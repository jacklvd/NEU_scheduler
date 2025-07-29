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
			// Instead of alert, we could set an error state
			return;
		}
		generatePlan(interest, years);
	};

	return (
		<div className="space-y-6">
			{/* Input Form */}
			<Card className="border-northeastern-gray-light shadow-lg">
				<CardHeader>
					<CardTitle className="flex items-center gap-3 text-xl">
						<div className="p-2 bg-northeastern-white/20 rounded-lg">
							<Sparkles className="h-6 w-6" />
						</div>
						AI Course Planner
					</CardTitle>
					<CardDescription className="text-northeastern-white/90 text-base">
						Get personalized course recommendations tailored to your academic
						interests and career goals
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-6 p-6">
					<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
						<div className="md:col-span-2 space-y-2">
							<label className="block text-sm font-semibold text-northeastern-black mb-2">
								Area of Interest
							</label>
							<Input
								value={interest}
								onChange={e => setInterest(e.target.value)}
								placeholder="e.g., machine learning, web development, cybersecurity, business analysis"
								className="h-12 text-base border-northeastern-gray-light focus:border-northeastern-orange focus:ring-northeastern-orange/20"
							/>
							<p className="text-xs text-northeastern-gray-dark">
								Enter your field of interest or career focus area
							</p>
						</div>
						<div className="space-y-2">
							<label className="block text-sm font-semibold text-northeastern-black mb-2">
								Program Duration
							</label>
							<select
								value={years}
								onChange={e => setYears(Number(e.target.value))}
								className="w-full h-12 p-3 border border-northeastern-gray-light rounded-md bg-background text-base focus:border-northeastern-orange focus:ring-2 focus:ring-northeastern-orange/20 focus:outline-none"
							>
								<option value={2}>2 Years (Masters)</option>
								<option value={4}>4 Years (Undergraduate)</option>
							</select>
						</div>
					</div>
					<Button
						onClick={handleGeneratePlan}
						disabled={loading || !interest.trim()}
						className="w-full h-12 bg-gradient-to-r from-northeastern-orange to-northeastern-orange/90 hover:from-northeastern-orange/90 hover:to-northeastern-orange text-northeastern-white font-semibold text-base shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{loading ? (
							<>
								<Loader2 className="h-5 w-5 animate-spin mr-3" />
								Generating Your Plan...
							</>
						) : (
							<>
								<Sparkles className="h-5 w-5 mr-3" />
								Generate My Academic Plan
							</>
						)}
					</Button>
				</CardContent>
			</Card>

			{/* Loading State */}
			{loading && (
				<Card className="border-northeastern-gray-light shadow-md">
					<CardContent className="p-8">
						<div className="flex flex-col items-center text-center space-y-4">
							<div className="relative">
								<div className="w-16 h-16 border-4 border-northeastern-gray-light rounded-full"></div>
								<div className="w-16 h-16 border-4 border-northeastern-orange border-t-transparent rounded-full animate-spin absolute top-0 left-0"></div>
							</div>
							<div className="space-y-2">
								<h3 className="text-lg font-semibold text-northeastern-black">
									Creating Your Academic Plan
								</h3>
								<p className="text-northeastern-gray-dark">
									Analyzing course data and generating personalized
									recommendations for {interest}...
								</p>
							</div>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Error Display */}
			{error && (
				<Card className="border-red-200 bg-red-50 shadow-md">
					<CardContent className="p-6">
						<div className="flex items-center gap-3">
							<div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center">
								<span className="text-red-600 text-sm font-bold">!</span>
							</div>
							<div>
								<p className="text-red-800 font-medium">
									Error generating plan
								</p>
								<p className="text-red-600 text-sm">{error}</p>
							</div>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Empty State */}
			{!loading && !error && plan.length === 0 && (
				<Card className="border-northeastern-gray-light shadow-md border-dashed">
					<CardContent className="p-12">
						<div className="flex flex-col items-center text-center space-y-4">
							<div className="w-20 h-20 bg-northeastern-gray-light/30 rounded-full flex items-center justify-center">
								<BookOpen className="h-10 w-10 text-northeastern-gray-dark" />
							</div>
							<div className="space-y-2">
								<h3 className="text-xl font-semibold text-northeastern-black">
									Ready to plan your academic journey?
								</h3>
								<p className="text-northeastern-gray-dark max-w-md">
									Enter your area of interest above and let our AI create a
									personalized course plan tailored to your goals.
								</p>
							</div>
							<div className="flex items-center gap-6 text-sm text-northeastern-gray-dark">
								<div className="flex items-center gap-2">
									<div className="w-2 h-2 bg-northeastern-orange rounded-full"></div>
									<span>Personalized recommendations</span>
								</div>
								<div className="flex items-center gap-2">
									<div className="w-2 h-2 bg-northeastern-green rounded-full"></div>
									<span>Structured timeline</span>
								</div>
								<div className="flex items-center gap-2">
									<div className="w-2 h-2 bg-northeastern-blue rounded-full"></div>
									<span>Credit optimization</span>
								</div>
							</div>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Plan Results */}
			{plan.length > 0 && (
				<Card className="border-northeastern-gray-light shadow-lg">
					<CardHeader>
						<CardTitle className="flex items-center gap-3 text-xl">
							<div className="p-2 bg-northeastern-white/20 rounded-lg">
								<BookOpen className="h-6 w-6" />
							</div>
							Your Personalized Course Plan
						</CardTitle>
						<CardDescription className="text-northeastern-white/90 text-base">
							Suggested {years}-year plan for{' '}
							<span className="font-semibold">{interest}</span> • {plan.length}{' '}
							semesters •{' '}
							<span className="font-semibold">
								{plan.reduce(
									(total, semester) => total + (semester.credits || 0),
									0
								)}{' '}
								total credits
							</span>
						</CardDescription>
					</CardHeader>
					<CardContent className="p-6">
						{(() => {
							// Group semesters by year for better organization
							const groupedPlan = plan.reduce(
								(acc, semester) => {
									const year = semester.year;
									if (!acc[year]) {
										acc[year] = [];
									}
									acc[year].push(semester);
									return acc;
								},
								{} as Record<number, typeof plan>
							);

							// Remove duplicates based on year, term, and course content
							const deduplicatedGroupedPlan = Object.entries(
								groupedPlan
							).reduce(
								(acc, [yearStr, semesters]) => {
									const year = parseInt(yearStr);
									const uniqueSemesters = semesters.filter(
										(semester, index, array) => {
											// Keep the first occurrence of each unique year+term combination
											return (
												array.findIndex(
													s =>
														s.year === semester.year &&
														s.term === semester.term &&
														JSON.stringify(s.courses.sort()) ===
															JSON.stringify(semester.courses.sort())
												) === index
											);
										}
									);

									if (uniqueSemesters.length > 0) {
										acc[year] = uniqueSemesters;
									}
									return acc;
								},
								{} as Record<number, typeof plan>
							);

							return (
								<div className="space-y-8">
									{/* Plan Summary */}
									<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
										<div className="bg-gradient-to-br from-northeastern-orange/10 to-northeastern-orange/5 border border-northeastern-orange/20 rounded-lg p-4">
											<div className="text-2xl font-bold text-northeastern-orange">
												{Object.keys(deduplicatedGroupedPlan).length}
											</div>
											<div className="text-sm font-medium text-northeastern-gray-dark">
												Academic Years
											</div>
										</div>
										<div className="bg-gradient-to-br from-northeastern-green/10 to-northeastern-green/5 border border-northeastern-green/20 rounded-lg p-4">
											<div className="text-2xl font-bold text-northeastern-green">
												{Object.values(deduplicatedGroupedPlan).flat().length}
											</div>
											<div className="text-sm font-medium text-northeastern-gray-dark">
												Total Semesters
											</div>
										</div>
										<div className="bg-gradient-to-br from-northeastern-blue/10 to-northeastern-blue/5 border border-northeastern-blue/20 rounded-lg p-4">
											<div className="text-2xl font-bold text-northeastern-blue">
												{Object.values(deduplicatedGroupedPlan)
													.flat()
													.reduce((total, s) => total + s.courses.length, 0)}
											</div>
											<div className="text-sm font-medium text-northeastern-gray-dark">
												Total Courses
											</div>
										</div>
									</div>

									{Object.entries(deduplicatedGroupedPlan)
										.sort(([a], [b]) => Number(a) - Number(b))
										.map(([year, semesters]) => (
											<div key={year} className="space-y-6">
												<div className="flex items-center gap-4">
													<div className="bg-northeastern-orange text-northeastern-white px-4 py-2 rounded-lg font-bold text-lg">
														Year {year}
													</div>
													<div className="flex-1 h-px bg-northeastern-gray-light"></div>
													<div className="bg-northeastern-gray-light/50 px-3 py-1 rounded-full text-sm font-medium text-northeastern-gray-dark">
														{semesters.reduce(
															(total, s) => total + (s.credits || 0),
															0
														)}{' '}
														credits total
													</div>
												</div>
												<div className="grid gap-6 md:grid-cols-2">
													{semesters
														.sort((a, b) => {
															// Sort by semester order: Fall, Spring, Summer
															const order = {
																Fall: 1,
																Spring: 2,
																Summer: 3,
																Summer1: 3,
																Summer2: 4,
															};
															return (
																(order[a.term as keyof typeof order] || 5) -
																(order[b.term as keyof typeof order] || 5)
															);
														})
														.map((semester, index) => (
															<Card
																key={`${year}-${semester.term}-${index}`}
																className="bg-gradient-to-br from-northeastern-gray-light/10 to-northeastern-gray-light/20 border-northeastern-gray-light/50 hover:shadow-md transition-shadow duration-200"
															>
																<CardHeader className="pb-4">
																	<CardTitle className="text-lg text-northeastern-black flex items-center justify-between">
																		<span className="font-bold">
																			{semester.term} {semester.year}
																		</span>
																		{semester.credits && (
																			<span className="text-sm font-normal bg-northeastern-orange/10 text-northeastern-orange px-2 py-1 rounded-full">
																				{semester.credits} credits
																			</span>
																		)}
																	</CardTitle>
																	{semester.notes && (
																		<CardDescription className="text-northeastern-gray-dark text-sm">
																			{semester.notes}
																		</CardDescription>
																	)}
																</CardHeader>
																<CardContent>
																	<div className="space-y-3">
																		{semester.courses.map(
																			(course, courseIndex) => {
																				// Try to parse course code and title
																				const courseMatch = course.match(
																					/^([A-Z]{2,4}\s?\d{4})\s*[-:]?\s*(.*)$/
																				);
																				const courseCode = courseMatch
																					? courseMatch[1]
																					: '';
																				const courseTitle = courseMatch
																					? courseMatch[2]
																					: course;

																				return (
																					<div
																						key={courseIndex}
																						className="flex items-start gap-3 p-4 bg-white rounded-lg border border-northeastern-gray-light/30 hover:border-northeastern-orange/40 hover:shadow-sm transition-all duration-200 group"
																					>
																						<div className="w-2 h-2 rounded-full bg-northeastern-orange mt-2 flex-shrink-0 group-hover:bg-northeastern-orange/80"></div>
																						<div className="flex-1 min-w-0">
																							{courseCode ? (
																								<>
																									<div className="font-mono text-sm font-bold text-northeastern-orange mb-1">
																										{courseCode}
																									</div>
																									<div className="text-sm text-northeastern-gray-dark font-medium leading-relaxed">
																										{courseTitle}
																									</div>
																								</>
																							) : (
																								<span className="text-sm text-northeastern-gray-dark font-medium leading-relaxed">
																									{course}
																								</span>
																							)}
																						</div>
																					</div>
																				);
																			}
																		)}
																	</div>
																</CardContent>
															</Card>
														))}
												</div>
											</div>
										))}
								</div>
							);
						})()}
					</CardContent>
				</Card>
			)}
		</div>
	);
}
