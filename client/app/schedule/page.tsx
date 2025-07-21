'use client';

import React, { useState } from 'react';
import { Calendar, Clock, MapPin, User, Plus, Trash2 } from 'lucide-react';
import { Button } from '../../components/ui/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import type { Class } from '../../types/api';

// Mock schedule data - replace with real data from your backend
const mockSchedule: Class[] = [
	{
		crn: '12345',
		title: 'Fundamentals of Computer Science 1',
		subject: 'CS',
		courseNumber: '2500',
		instructor: 'John Smith',
		meetingDays: 'Mon, Wed, Fri',
		meetingTimes: '09:15 AM - 10:20 AM',
		location: 'West Village H 212',
		enrollment: 45,
		enrollmentCap: 50,
		credits: 4,
	},
	{
		crn: '12346',
		title: 'Calculus for Science and Engineering I',
		subject: 'MATH',
		courseNumber: '1341',
		instructor: 'Jane Doe',
		meetingDays: 'Tue, Thu',
		meetingTimes: '11:45 AM - 01:25 PM',
		location: 'Snell Engineering 108',
		enrollment: 30,
		enrollmentCap: 35,
		credits: 4,
	},
];

export default function SchedulePage() {
	const [schedule, setSchedule] = useState<Class[]>(mockSchedule);
	const [newCourseId, setNewCourseId] = useState('');

	const totalCredits = schedule.reduce(
		(sum, course) => sum + (course.credits || 0),
		0
	);

	const addCourse = () => {
		if (newCourseId.trim()) {
			// In a real app, you'd search for the course by ID and add it
			console.log('Adding course:', newCourseId);
			setNewCourseId('');
		}
	};

	const removeCourse = (crn: string) => {
		setSchedule(schedule.filter(course => course.crn !== crn));
	};

	return (
		<div className="container mx-auto px-4 py-8">
			<div className="mb-8">
				<h1 className="text-3xl font-bold mb-2">My Schedule</h1>
				<p className="text-muted-foreground">
					Manage your course schedule and track your academic progress
				</p>
			</div>

			<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
				{/* Schedule Overview */}
				<div className="lg:col-span-2 space-y-6">
					{/* Add Course Section */}
					<Card>
						<CardHeader>
							<CardTitle className="flex items-center gap-2">
								<Plus className="h-5 w-5" />
								Add Course
							</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="flex gap-2">
								<Input
									value={newCourseId}
									onChange={e => setNewCourseId(e.target.value)}
									placeholder="Enter CRN or course code (e.g., CS 2500)"
									className="flex-1"
								/>
								<Button onClick={addCourse}>Add</Button>
							</div>
						</CardContent>
					</Card>

					{/* Current Schedule */}
					<Card>
						<CardHeader>
							<CardTitle>Current Schedule</CardTitle>
							<CardDescription>
								{schedule.length} courses • {totalCredits} total credits
							</CardDescription>
						</CardHeader>
						<CardContent>
							<div className="space-y-4">
								{schedule.length === 0 ? (
									<div className="text-center py-8 text-muted-foreground">
										<Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
										<p>No courses added yet</p>
										<p className="text-sm">
											Add courses to start building your schedule
										</p>
									</div>
								) : (
									schedule.map(course => (
										<ScheduleCard
											key={course.crn}
											course={course}
											onRemove={() => removeCourse(course.crn)}
										/>
									))
								)}
							</div>
						</CardContent>
					</Card>
				</div>

				{/* Sidebar */}
				<div className="space-y-6">
					{/* Schedule Summary */}
					<Card>
						<CardHeader>
							<CardTitle>Schedule Summary</CardTitle>
						</CardHeader>
						<CardContent className="space-y-4">
							<div className="flex justify-between">
								<span>Total Courses:</span>
								<span className="font-medium">{schedule.length}</span>
							</div>
							<div className="flex justify-between">
								<span>Total Credits:</span>
								<span className="font-medium">{totalCredits}</span>
							</div>
							<div className="flex justify-between">
								<span>Status:</span>
								<span
									className={`font-medium ${
										totalCredits >= 12 ? 'text-green-600' : 'text-orange-600'
									}`}
								>
									{totalCredits >= 12 ? 'Full-time' : 'Part-time'}
								</span>
							</div>
						</CardContent>
					</Card>

					{/* Quick Actions */}
					<Card>
						<CardHeader>
							<CardTitle>Quick Actions</CardTitle>
						</CardHeader>
						<CardContent className="space-y-2">
							<Button variant="outline" className="w-full justify-start">
								<Calendar className="h-4 w-4 mr-2" />
								Export Schedule
							</Button>
							<Button variant="outline" className="w-full justify-start">
								<Clock className="h-4 w-4 mr-2" />
								Check Conflicts
							</Button>
							<Button variant="outline" className="w-full justify-start">
								<User className="h-4 w-4 mr-2" />
								View Instructors
							</Button>
						</CardContent>
					</Card>

					{/* Schedule Tips */}
					<Card>
						<CardHeader>
							<CardTitle>💡 Tips</CardTitle>
						</CardHeader>
						<CardContent className="text-sm space-y-2">
							<p>• Aim for 12-18 credits per semester for full-time status</p>
							<p>• Check prerequisites before adding courses</p>
							<p>• Balance difficult courses with easier ones</p>
							<p>• Consider your work and personal schedule</p>
						</CardContent>
					</Card>
				</div>
			</div>
		</div>
	);
}

function ScheduleCard({
	course,
	onRemove,
}: {
	course: Class;
	onRemove: () => void;
}) {
	return (
		<Card className="hover:shadow-md transition-shadow">
			<CardContent className="p-4">
				<div className="flex justify-between items-start mb-3">
					<div>
						<h3 className="font-semibold text-lg">
							{course.subject} {course.courseNumber}
						</h3>
						<p className="text-sm text-muted-foreground">{course.title}</p>
					</div>
					<div className="flex items-center gap-2">
						<span className="text-sm font-medium bg-primary/10 text-primary px-2 py-1 rounded">
							{course.credits} credits
						</span>
						<Button
							variant="ghost"
							size="sm"
							onClick={onRemove}
							className="text-destructive hover:text-destructive"
						>
							<Trash2 className="h-4 w-4" />
						</Button>
					</div>
				</div>

				<div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
					<div className="flex items-center gap-2">
						<User className="h-4 w-4 text-muted-foreground" />
						<span>{course.instructor || 'TBA'}</span>
					</div>
					<div className="flex items-center gap-2">
						<Clock className="h-4 w-4 text-muted-foreground" />
						<div>
							<p>{course.meetingDays || 'TBA'}</p>
							<p className="text-muted-foreground">
								{course.meetingTimes || 'TBA'}
							</p>
						</div>
					</div>
					<div className="flex items-center gap-2">
						<MapPin className="h-4 w-4 text-muted-foreground" />
						<span>{course.location || 'TBA'}</span>
					</div>
				</div>

				<div className="mt-3 pt-3 border-t">
					<div className="flex justify-between text-sm">
						<span>CRN: {course.crn}</span>
						<span className="text-muted-foreground">
							{course.enrollment}/{course.enrollmentCap} enrolled
						</span>
					</div>
				</div>
			</CardContent>
		</Card>
	);
}
