'use client';

import React, { useState, useEffect } from 'react';
import { Search, Loader2, Info, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { useTerms, useSubjects, useCourseSearch } from '../hooks/useCourses';
import type { Class } from '../types/api';
import { toast } from 'sonner';

export function CourseSearch() {
	const [selectedTerm, setSelectedTerm] = useState('');
	const [searchQuery, setSearchQuery] = useState('');
	const [currentPage, setCurrentPage] = useState(1);
	const [itemsPerPage] = useState(15);

	const {
		terms,
		loading: termsLoading,
		error: termsError,
		refetch: refetchTerms,
	} = useTerms();
	const { subjects, loading: subjectsLoading } = useSubjects(selectedTerm);
	const {
		courses,
		loading: coursesLoading,
		error: coursesError,
		searchCourses,
	} = useCourseSearch();

	// Set default term when terms are loaded
	useEffect(() => {
		if (terms.length > 0 && !selectedTerm) {
			// Look for Fall 2025 or current semester
			const fall2025 = terms.find(
				term =>
					term.name.toLowerCase().includes('fall 2025') ||
					term.name.toLowerCase().includes('spring 2025')
			);
			if (fall2025) {
				setSelectedTerm(fall2025.id);
			} else {
				// Fallback to first available term
				setSelectedTerm(terms[0].id);
			}
		}
	}, [terms, selectedTerm]);

	const handleSearch = async () => {
		if (!selectedTerm) {
			toast.error('Please select a term first');
			return;
		}

		if (!searchQuery.trim()) {
			toast.error('Please enter a search query');
			return;
		}

		setCurrentPage(1); // Reset to first page on new search
		await searchCourses({
			term: selectedTerm,
			subject: searchQuery.trim().toUpperCase(), // Convert to uppercase for subject codes
			pageSize: 100, // Get more results for pagination
		});
	};

	const handleViewAllCourses = async () => {
		if (!selectedTerm) {
			toast.error('Please select a term first');
			return;
		}

		setCurrentPage(1); // Reset to first page
		await searchCourses({
			term: selectedTerm,
			subject: '',
			courseNumber: '',
			pageSize: 100,
		});
	};

	// Calculate pagination
	const totalPages = Math.ceil(courses.length / itemsPerPage);
	const startIndex = (currentPage - 1) * itemsPerPage;
	const endIndex = startIndex + itemsPerPage;
	const currentCourses = courses.slice(startIndex, endIndex);

	return (
		<div className="space-y-6">
			{/* Error Messages */}
			{termsError && (
				<div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-md">
					<AlertCircle className="h-5 w-5 text-red-600" />
					<span className="text-red-800">{termsError}</span>
					<Button
						variant="outline"
						size="sm"
						onClick={refetchTerms}
						className="ml-auto"
					>
						<RefreshCw className="h-4 w-4 mr-2" />
						Retry
					</Button>
				</div>
			)}

			{/* Main Search Interface */}
			<div className="bg-gray-50 rounded-lg p-6 border">
				{/* Search Form */}
				<div className="space-y-4">
					{/* Term and Search Row */}
					<div className="flex gap-4 items-end">
						{/* Term Dropdown */}
						<div className="min-w-[250px]">
							<label className="block text-sm font-medium mb-2">Term</label>
							<select
								value={selectedTerm}
								onChange={e => setSelectedTerm(e.target.value)}
								className="w-full h-12 p-3 border border-gray-300 rounded-md bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
								disabled={termsLoading}
							>
								{termsLoading ? (
									<option value="">Loading terms...</option>
								) : (
									<>
										<option value="">Select Term...</option>
										{terms.map(term => (
											<option key={term.id} value={term.id}>
												{term.name}
											</option>
										))}
									</>
								)}
							</select>
							{termsLoading && (
								<div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
									<Loader2 className="h-3 w-3 animate-spin" />
									Loading terms...
								</div>
							)}
						</div>

						{/* Search Input */}
						<div className="flex-1">
							<label className="block text-sm font-medium mb-2">Search</label>
							<div className="flex gap-2 h-12">
								<Input
									value={searchQuery}
									onChange={e => setSearchQuery(e.target.value)}
									placeholder='Subject code (e.g., "CS", "MATH") or course title'
									className="flex-1 h-full border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
									disabled={!selectedTerm}
									onKeyPress={e => e.key === 'Enter' && handleSearch()}
								/>
								<Button
									onClick={handleSearch}
									disabled={!selectedTerm || coursesLoading}
									className="h-full px-6 bg-blue-600 hover:bg-blue-700 text-white"
								>
									{coursesLoading ? (
										<Loader2 className="h-4 w-4 animate-spin" />
									) : (
										<Search className="h-4 w-4" />
									)}
								</Button>
							</div>
						</div>

						{/* Info Button */}
						<div>
							<Button
								variant="outline"
								size="icon"
								className="h-12 w-12 border-gray-300 text-gray-600 hover:text-gray-800 hover:border-gray-400"
								onClick={() =>
									toast.info(
										'Search by subject code (CS, MATH) or course title keywords'
									)
								}
							>
								<Info className="h-4 w-4" />
							</Button>
						</div>
					</div>

					{/* Quick Actions */}
					<div className="flex gap-4 text-sm">
						<button
							onClick={handleViewAllCourses}
							className="text-blue-600 hover:text-blue-800 underline"
							disabled={!selectedTerm || coursesLoading}
						>
							View all classes for{' '}
							{selectedTerm
								? terms.find(t => t.id === selectedTerm)?.name ||
									'selected term'
								: 'selected term'}
						</button>

						{subjects.length > 0 && (
							<div className="text-gray-600">
								Available subjects:{' '}
								{subjects
									.slice(0, 5)
									.map(s => s.code)
									.join(', ')}
								{subjects.length > 5 && ` (+${subjects.length - 5} more)`}
							</div>
						)}
					</div>

					{/* Subjects Loading */}
					{subjectsLoading && (
						<div className="flex items-center gap-2 text-sm text-gray-500">
							<Loader2 className="h-3 w-3 animate-spin" />
							Loading available subjects...
						</div>
					)}

					{/* Search Status */}
					{coursesLoading && (
						<div className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
							<Loader2 className="h-4 w-4 animate-spin text-blue-600" />
							<span className="text-blue-800">Searching courses...</span>
						</div>
					)}

					{/* Course Search Error */}
					{coursesError && (
						<div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
							<AlertCircle className="h-4 w-4 text-red-600" />
							<span className="text-red-800">{coursesError}</span>
						</div>
					)}
				</div>
			</div>

			{/* Results */}
			{courses.length > 0 && (
				<>
					<Card className="border-gray-200">
						<CardHeader className="bg-blue-600 text-white">
							<CardTitle>
								Search Results ({courses.length} courses found)
								{totalPages > 1 && (
									<span className="text-blue-100 font-normal ml-2">
										- Page {currentPage} of {totalPages}
									</span>
								)}
							</CardTitle>
						</CardHeader>
						<CardContent className="p-0">
							<div className="space-y-0">
								{currentCourses.map((course, index) => (
									<CourseCard
										key={course.crn}
										course={course}
										isEven={index % 2 === 0}
									/>
								))}
							</div>
						</CardContent>
					</Card>

					{/* Pagination */}
					{totalPages > 1 && (
						<div className="flex justify-between items-center p-4 bg-gray-50 border-t">
							<div className="text-sm text-gray-600">
								Showing {startIndex + 1}-{Math.min(endIndex, courses.length)} of{' '}
								{courses.length} results
							</div>
							<div className="flex gap-2">
								<Button
									variant="outline"
									size="sm"
									onClick={() => setCurrentPage(1)}
									disabled={currentPage === 1}
								>
									First
								</Button>
								<Button
									variant="outline"
									size="sm"
									onClick={() => setCurrentPage(currentPage - 1)}
									disabled={currentPage === 1}
								>
									Previous
								</Button>
								<span className="flex items-center px-3 text-sm font-medium">
									{currentPage} of {totalPages}
								</span>
								<Button
									variant="outline"
									size="sm"
									onClick={() => setCurrentPage(currentPage + 1)}
									disabled={currentPage === totalPages}
								>
									Next
								</Button>
								<Button
									variant="outline"
									size="sm"
									onClick={() => setCurrentPage(totalPages)}
									disabled={currentPage === totalPages}
								>
									Last
								</Button>
							</div>
						</div>
					)}
				</>
			)}

			{/* No Results Message */}
			{!coursesLoading &&
				courses.length === 0 &&
				searchQuery &&
				selectedTerm && (
					<Card className="border-gray-200">
						<CardContent className="p-8 text-center">
							<div className="text-gray-500">
								<Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
								<h3 className="text-lg font-medium mb-2">No courses found</h3>
								<p className="text-sm">
									Try searching with a different subject code or term. Popular
									subjects include: CS, MATH, ENGW, PHYS
								</p>
							</div>
						</CardContent>
					</Card>
				)}
		</div>
	);
}

function CourseCard({ course, isEven }: { course: Class; isEven: boolean }) {
	const [showDetails, setShowDetails] = useState(false);

	return (
		<div
			className={`border-b border-gray-200 hover:bg-gray-50 transition-colors ${isEven ? 'bg-white' : 'bg-gray-25'}`}
		>
			<div className="p-4">
				<div className="flex justify-between items-start mb-3">
					<div className="flex-1">
						<h3 className="font-semibold text-lg text-gray-900">
							{course.subject} {course.courseNumber} - {course.title}
						</h3>
						<div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
							<span>CRN: {course.crn}</span>
							<span className="text-blue-600 font-medium">
								{course.credits} credits
							</span>
							<span
								className={`px-2 py-1 rounded text-xs font-medium ${
									course.enrollment &&
									course.enrollmentCap &&
									course.enrollment >= course.enrollmentCap
										? 'bg-red-100 text-red-800'
										: course.enrollment &&
											  course.enrollmentCap &&
											  course.enrollment / course.enrollmentCap > 0.8
											? 'bg-yellow-100 text-yellow-800'
											: 'bg-green-100 text-green-800'
								}`}
							>
								{course.enrollment}/{course.enrollmentCap} enrolled
							</span>
						</div>
					</div>

					<Button
						variant="outline"
						size="sm"
						onClick={() => setShowDetails(!showDetails)}
					>
						{showDetails ? 'Hide Details' : 'Show Details'}
					</Button>
				</div>

				{/* Basic Info Row */}
				<div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
					<div>
						<span className="font-medium text-gray-700">Instructor:</span>
						<p className="text-gray-600">{course.instructor || 'TBA'}</p>
					</div>
					<div>
						<span className="font-medium text-gray-700">Schedule:</span>
						<p className="text-gray-600">{course.meetingDays || 'TBA'}</p>
						<p className="text-gray-600">{course.meetingTimes || 'TBA'}</p>
					</div>
					<div>
						<span className="font-medium text-gray-700">Location:</span>
						<p className="text-gray-600">{course.location || 'TBA'}</p>
					</div>
				</div>

				{/* Expanded Details */}
				{showDetails && (
					<div className="mt-4 pt-4 border-t border-gray-200">
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
							<div>
								<span className="font-medium text-gray-700">Subject Code:</span>
								<p className="text-gray-600">{course.subject}</p>
							</div>
							<div>
								<span className="font-medium text-gray-700">
									Course Reference Number:
								</span>
								<p className="text-gray-600">{course.crn}</p>
							</div>
						</div>

						<div className="mt-3 flex gap-2">
							<Button variant="outline" size="sm">
								Add to Schedule
							</Button>
							<Button variant="outline" size="sm">
								View Details
							</Button>
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
