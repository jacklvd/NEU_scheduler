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
			<Card>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<Search className="h-5 w-5" />
						Course Search
					</CardTitle>
					<CardDescription>
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
								className="w-full"
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
				</CardContent>
			</Card>

			{/* Results */}
			{courses.length > 0 && (
				<Card>
					<CardHeader>
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
		<Card className="hover:shadow-md transition-shadow">
			<CardContent className="p-4">
				<div className="flex justify-between items-start mb-2">
					<div>
						<h3 className="font-semibold text-lg">
							{course.subject} {course.courseNumber} - {course.title}
						</h3>
						<p className="text-sm text-muted-foreground">CRN: {course.crn}</p>
					</div>
					<div className="text-right">
						<p className="text-sm font-medium">{course.credits} credits</p>
						<p className="text-sm text-muted-foreground">
							{course.enrollment}/{course.enrollmentCap} enrolled
						</p>
					</div>
				</div>

				<div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
					<div>
						<span className="font-medium">Instructor:</span>
						<p>{course.instructor || 'TBA'}</p>
					</div>
					<div>
						<span className="font-medium">Schedule:</span>
						<p>{course.meetingDays || 'TBA'}</p>
						<p>{course.meetingTimes || 'TBA'}</p>
					</div>
					<div>
						<span className="font-medium">Location:</span>
						<p>{course.location || 'TBA'}</p>
					</div>
				</div>
			</CardContent>
		</Card>
	);
}
