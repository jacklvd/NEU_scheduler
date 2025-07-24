'use client';

import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from './ui/card';
import {
	useTerms,
	useSubjects,
	useCourseSearch,
} from '../lib/hooks/useCourses';
import type { Class } from '../types/api';

export function CourseSearch() {
	const [selectedTerm, setSelectedTerm] = useState('');
	const [selectedSubject, setSelectedSubject] = useState('');
	const [courseNumber, setCourseNumber] = useState('');
	const [errorMessage, setErrorMessage] = useState('');

	const { terms, loading: termsLoading } = useTerms();
	const { subjects, loading: subjectsLoading } = useSubjects(selectedTerm);
	const { courses, loading: coursesLoading, searchCourses } = useCourseSearch();

	const handleSearch = () => {
		if (!selectedTerm) {
			setErrorMessage('Please select a term first');
			return;
		}

		setErrorMessage(''); // Clear error message
		searchCourses({
			term: selectedTerm,
			subject: selectedSubject,
			courseNumber,
			pageSize: 20,
		});
	};

	return (
		<div className="space-y-6">
			{/* Search Form */}
			<Card className="border-northeastern-gray-light">
				<CardHeader className="bg-northeastern-red text-northeastern-white">
					<CardTitle className="flex items-center gap-2">
						<Search className="h-5 w-5" />
						Course Search
					</CardTitle>
					<CardDescription className="text-northeastern-white/90">
						Search for courses by term, subject, and course number
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
						{/* Term Selection */}
						<div>
							<label className="block text-sm font-medium mb-2">Term</label>
							<select
								value={selectedTerm}
								onChange={e => setSelectedTerm(e.target.value)}
								className="w-full p-2 border rounded-md bg-background"
								disabled={termsLoading}
							>
								<option value="">Select Term...</option>
								{terms.map(term => (
									<option key={term.id} value={term.id}>
										{term.name}
									</option>
								))}
							</select>
						</div>

						{/* Subject Selection */}
						<div>
							<label className="block text-sm font-medium mb-2">Subject</label>
							<select
								value={selectedSubject}
								onChange={e => setSelectedSubject(e.target.value)}
								className="w-full p-2 border rounded-md bg-background"
								disabled={!selectedTerm || subjectsLoading}
							>
								<option value="">All Subjects</option>
								{subjects.map(subject => (
									<option key={subject.code} value={subject.code}>
										{subject.code} - {subject.name}
									</option>
								))}
							</select>
						</div>

						{/* Course Number */}
						<div>
							<label className="block text-sm font-medium mb-2">
								Course Number
							</label>
							<Input
								value={courseNumber}
								onChange={e => setCourseNumber(e.target.value)}
								placeholder="e.g., 2500"
								disabled={!selectedTerm}
							/>
						</div>

						{/* Search Button */}
						<div>
							<label className="block text-sm font-medium mb-2">&nbsp;</label>
							<Button
								onClick={handleSearch}
								disabled={!selectedTerm || coursesLoading}
								className="w-full bg-northeastern-red hover:bg-northeastern-red/90 text-northeastern-white"
							>
								{coursesLoading ? (
									<Loader2 className="h-4 w-4 animate-spin mr-2" />
								) : (
									<Search className="h-4 w-4 mr-2" />
								)}
								Search
							</Button>
						</div>
					</div>
					{errorMessage && (
						<div className="mt-4 p-3 bg-northeastern-red/10 border border-northeastern-red/20 rounded-md">
							<p className="text-northeastern-red text-sm">{errorMessage}</p>
						</div>
					)}
				</CardContent>
			</Card>

			{/* Results */}
			{courses.length > 0 && (
				<Card className="border-northeastern-gray-light">
					<CardHeader className="bg-northeastern-blue text-northeastern-white">
						<CardTitle>
							Search Results ({courses.length} courses found)
						</CardTitle>
					</CardHeader>
					<CardContent>
						<div className="space-y-4">
							{courses.map(course => (
								<CourseCard key={course.crn} course={course} />
							))}
						</div>
					</CardContent>
				</Card>
			)}
		</div>
	);
}

function CourseCard({ course }: { course: Class }) {
	return (
		<Card className="hover:shadow-md transition-shadow border-northeastern-gray-light hover:border-northeastern-blue">
			<CardContent className="p-4">
				<div className="flex justify-between items-start mb-2">
					<div>
						<h3 className="font-semibold text-lg text-northeastern-black">
							{course.subject} {course.courseNumber} - {course.title}
						</h3>
						<p className="text-sm text-northeastern-gray">CRN: {course.crn}</p>
					</div>
					<div className="text-right">
						<p className="text-sm font-medium text-northeastern-red">
							{course.credits} credits
						</p>
						<p className="text-sm text-northeastern-gray">
							{course.enrollment}/{course.enrollmentCap} enrolled
						</p>
					</div>
				</div>

				<div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
					<div>
						<span className="font-medium text-northeastern-black">
							Instructor:
						</span>
						<p className="text-northeastern-gray">
							{course.instructor || 'TBA'}
						</p>
					</div>
					<div>
						<span className="font-medium text-northeastern-black">
							Schedule:
						</span>
						<p className="text-northeastern-gray">
							{course.meetingDays || 'TBA'}
						</p>
						<p className="text-northeastern-gray">
							{course.meetingTimes || 'TBA'}
						</p>
					</div>
					<div>
						<span className="font-medium text-northeastern-black">
							Location:
						</span>
						<p className="text-northeastern-gray">{course.location || 'TBA'}</p>
					</div>
				</div>
			</CardContent>
		</Card>
	);
}
