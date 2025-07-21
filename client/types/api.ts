export interface Term {
	id: string;
	name: string;
}

export interface Subject {
	code: string;
	name: string;
}

export interface Course {
	subject: string;
	courseNumber: string;
	title: string;
	description?: string;
	credits?: number;
	prerequisites?: string[];
}

export interface Class {
	crn: string;
	title: string;
	subject: string;
	courseNumber: string;
	instructor?: string;
	meetingDays?: string;
	meetingTimes?: string;
	location?: string;
	enrollment?: number;
	enrollmentCap?: number;
	credits?: number;
}

export interface SuggestedPlan {
	year: number;
	term: string;
	courses: string[];
}

export interface ApiResponse<T> {
	data: T;
	errors?: Array<{
		message: string;
		path?: string[];
	}>;
}
